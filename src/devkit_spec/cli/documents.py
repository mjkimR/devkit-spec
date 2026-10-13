"""``devkit spec resolve``, ``refs`` and ``list``: find documents by ID, follow their references, browse them.

Text output (paths are relative to the workspace root):

- ``resolve``: one ``[DOCUMENT: <id> kind= status= path=]`` line per resolved ID; unresolved or duplicated IDs
  are errors after the lines that did resolve.
- ``refs``: ``[REF: <id> path= status= fields= count=]`` per referenced (``--direction out``) or referencing
  (``--direction in``) document, in ID order; ``path=-`` is a reference to an ID no document declares.
- ``list``: ``[DOCUMENT: <id> kind= status= path= tasks= title=]`` per document in kind, then ID order; ``tasks``
  is ``<checked>/<total>`` of a spec's ``tasks.md``.

``refs`` and ``list`` end with ``[PAGE: total= offset= limit= count= next=]`` and, when more items follow,
``[NEXT_CMD: ...]`` for the next page. Files that could not be indexed are ``SPEC_DOCUMENT_INVALID`` warnings.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import click
from devkit.advisory import AdvisoryError
from devkit.core.cli import (
    FORMAT_OPTION,
    boundary,
    echo_json,
    echo_notices,
    exit_on_problems,
    exit_on_warnings,
    is_json,
    resolve_root,
    workspace_option,
)
from devkit.core.errors import ArgumentError

from devkit_spec.cli.output import echo_page, page, sentinel
from devkit_spec.config import Namespace, read_spec_config
from devkit_spec.documents import Document, DocumentIndex, Kind, Reference
from devkit_spec.entrypoints.paths import overlaps
from devkit_spec.namespaces import Selection, namespace_resolver, select

WORKSPACE = workspace_option()
LIMIT = click.option("--limit", "-n", type=int, default=20, show_default=True, help="Items per page; 0 for all")
OFFSET = click.option("--offset", type=int, default=0, show_default=True, help="Items to skip")
_KIND_ORDER = {kind: position for position, kind in enumerate(Kind)}


NAMESPACE = click.option(
    "--namespace", default=None, help="Show this namespace and the global documents; global shows only those"
)
ALL_NAMESPACES = click.option("--all-namespaces", is_flag=True, help="Show every namespace")


@dataclass(frozen=True)
class NamespaceScope:
    """The namespaces of the workspace and the selection a browsing command applies."""

    namespaces: tuple[Namespace, ...]
    selection: Selection
    namespace_of: Callable[[Document], str]

    @classmethod
    def of(cls, index: DocumentIndex, name: str | None, every: bool) -> NamespaceScope:
        namespaces = read_spec_config(index.root).namespaces
        selection = select(namespaces, index.root, Path.cwd(), name, every)
        return cls(namespaces, selection, namespace_resolver(index, namespaces))

    def accepts(self, document: Document) -> bool:
        return self.selection.matches(self.namespace_of(document))

    def fields(self, document: Document) -> dict[str, str]:
        """``namespace=`` for text output, only in a workspace that has namespaces."""
        return {"namespace": self.namespace_of(document)} if self.namespaces else {}

    @staticmethod
    def args(name: str | None, every: bool) -> list[str]:
        return ["--namespace", name] if name is not None else ["--all-namespaces"] if every else []


def _load(workspace_root: str | None) -> DocumentIndex:
    return DocumentIndex.load(resolve_root(workspace_root))


def _check_page(limit: int, offset: int) -> None:
    if limit < 0 or offset < 0:
        raise ArgumentError(
            f"--limit {limit} --offset {offset}: must not be negative",
            target_files=["--limit", "--offset"],
            fix="Pass --limit 0 or more (0 returns every item) and --offset 0 or more",
        )


def _paging_args(workspace_root: str | None, limit: int) -> list[str]:
    return [*(["-w", workspace_root] if workspace_root is not None else []), "--limit", str(limit)]


def _finish(notices: Sequence[AdvisoryError]) -> None:
    echo_notices(notices)
    exit_on_warnings(notices)


@click.command(name="resolve")
@click.argument("ids", nargs=-1, required=True, metavar="ID...")
@WORKSPACE
@FORMAT_OPTION
@boundary
def resolve_cmd(ids: tuple[str, ...], workspace_root: str | None, output_format: str) -> None:
    """Print the path of each document ID."""
    index = _load(workspace_root)
    found: list[Document] = []
    errors: list[AdvisoryError] = []
    for document_id in ids:
        try:
            found.append(index.resolve(document_id))
        except AdvisoryError as error:
            errors.append(error)
    if is_json(output_format):
        echo_json(
            {
                "documents": [document.to_dict() for document in found],
                "errors": [error.to_dict() for error in errors],
                "notices": [notice.to_dict() for notice in index.problems],
            }
        )
    else:
        for document in found:
            click.echo(
                sentinel("DOCUMENT", document.id, kind=document.kind, status=document.status, path=document.path)
            )
    echo_notices(index.problems)
    exit_on_problems(errors)
    exit_on_warnings(index.problems)


@click.command(name="refs")
@click.argument("document_id", metavar="ID")
@click.option(
    "--direction",
    type=click.Choice(["out", "in"]),
    default="out",
    show_default=True,
    help="out: the documents ID references; in: the documents that reference ID",
)
@LIMIT
@OFFSET
@WORKSPACE
@FORMAT_OPTION
@boundary
def refs_cmd(
    document_id: str, direction: str, limit: int, offset: int, workspace_root: str | None, output_format: str
) -> None:
    """List the documents a document references, or the documents referencing it."""
    _check_page(limit, offset)
    index = _load(workspace_root)
    document = index.resolve(document_id)
    groups = index.outgoing(document) if direction == "out" else index.incoming(document.id)
    keys = list(groups)
    shown = page(keys, offset, limit)
    items = [_RefGroup.of(index, key, groups[key]) for key in shown]
    if is_json(output_format):
        echo_json(
            {
                "id": document.id,
                "direction": direction,
                "total": len(keys),
                "offset": offset,
                "limit": limit,
                "items": [item.to_dict() for item in items],
                "notices": [notice.to_dict() for notice in index.problems],
            }
        )
    else:
        for item in items:
            click.echo(
                sentinel(
                    "REF",
                    item.id,
                    path=item.document.path if item.document else None,
                    status=item.document.status if item.document else None,
                    fields=",".join(sorted({ref.field for ref in item.references})),
                    count=len(item.references),
                )
            )
        args = ["refs", document.id, "--direction", direction, *_paging_args(workspace_root, limit)]
        echo_page(len(keys), offset, limit, len(items), args)
    _finish(index.problems)


@dataclass(frozen=True)
class _RefGroup:
    """The references between the requested document and the document ``id`` (``None`` when no single document
    declares it)."""

    id: str
    document: Document | None
    references: list[Reference]

    @classmethod
    def of(cls, index: DocumentIndex, other: str, references: list[Reference]) -> _RefGroup:
        declared = index.by_id.get(other, [])
        return cls(other, declared[0] if len(declared) == 1 else None, references)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "path": self.document.path if self.document else None,
            "status": self.document.status if self.document else None,
            "references": [ref.to_dict() for ref in self.references],
        }


@click.command(name="list")
@click.argument("kinds", nargs=-1, type=click.Choice([str(kind) for kind in Kind]), metavar="[KIND]...")
@click.option("--status", "-s", default=None, help="Comma-separated statuses to keep (case-insensitive)")
@click.option("--area", "-a", default=None, help="Keep documents whose frontmatter area contains this text")
@click.option("--query", "query", default=None, help="Keep documents whose ID or title contains this text")
@click.option("--history", is_flag=True, help="Include the files of completed spec bundles")
@click.option(
    "--file",
    "file",
    default=None,
    help="Keep documents whose frontmatter entrypoints overlap this workspace-relative file or directory",
)
@NAMESPACE
@ALL_NAMESPACES
@LIMIT
@OFFSET
@WORKSPACE
@FORMAT_OPTION
@boundary
def list_cmd(
    kinds: tuple[str, ...],
    status: str | None,
    area: str | None,
    query: str | None,
    history: bool,
    file: str | None,
    namespace: str | None,
    all_namespaces: bool,
    limit: int,
    offset: int,
    workspace_root: str | None,
    output_format: str,
) -> None:
    """List documents of the given KINDs (default: all), current ones only unless --history.

    --file finds the documents that own a code path through their ``entrypoints``. KIND is one of: capability, story, architecture, decision, proposal, proposal-decision, spec, plan, tasks,
    reconcile, feedback, material. In a workspace with namespaces, the namespace of the current directory (plus the
    global documents) is shown unless --namespace or --all-namespaces says otherwise.
    """
    _check_page(limit, offset)
    index = _load(workspace_root)
    scope = NamespaceScope.of(index, namespace, all_namespaces)
    statuses = {part.strip().lower() for part in status.split(",") if part.strip()} if status else set()
    wanted = {Kind(kind) for kind in kinds}
    selected = [
        document
        for document in index.documents
        if (not wanted or document.kind in wanted)
        and (history or not index.is_historical(document))
        and (not statuses or document.status.lower() in statuses)
        and (not area or area.lower() in document.area.lower())
        and (not query or query.lower() in document.id.lower() or query.lower() in document.title.lower())
        and scope.accepts(document)
        and (file is None or _overlaps(document, file))
    ]
    selected.sort(key=lambda document: (_KIND_ORDER[document.kind], document.id, document.path))
    shown = page(selected, offset, limit)
    tasks = {document.path: _tasks(index.root, document) for document in shown}
    if is_json(output_format):
        echo_json(
            {
                "total": len(selected),
                "offset": offset,
                "limit": limit,
                "namespace": scope.selection.name,
                "documents": [
                    document.to_dict()
                    | {
                        "namespace": scope.namespace_of(document),
                        "historical": index.is_historical(document),
                        "tasks": tasks[document.path],
                    }
                    for document in shown
                ],
                "notices": [notice.to_dict() for notice in index.problems],
            }
        )
    else:
        for document in shown:
            click.echo(
                sentinel(
                    "DOCUMENT",
                    document.id,
                    kind=document.kind,
                    status=document.status,
                    path=document.path,
                    tasks=tasks[document.path],
                    **scope.fields(document),
                    title=document.title,
                )
            )
        args = ["list", *kinds]
        for flag, given in (("--status", status), ("--area", area), ("--query", query), ("--file", file)):
            if given is not None:
                args += [flag, given]
        args += ["--history"] if history else []
        args += scope.args(namespace, all_namespaces)
        echo_page(len(selected), offset, limit, len(shown), [*args, *_paging_args(workspace_root, limit)])
    _finish(index.problems)


def _overlaps(document: Document, path: str) -> bool:
    """Whether one of the document's ``entrypoints`` is ``path``, under it, or a directory containing it."""
    entrypoints = document.frontmatter.get("entrypoints")
    if not isinstance(entrypoints, list):
        return False
    return any(isinstance(entry, str) and overlaps(entry, path) for entry in entrypoints)


def _tasks(root: Path, document: Document) -> str | None:
    """``<checked>/<total>`` of the ``tasks.md`` beside a spec, ``None`` for other kinds or without one."""
    if document.kind is not Kind.SPEC:
        return None
    tasks = root / document.path.rsplit("/", 1)[0] / "tasks.md"
    if not tasks.is_file():
        return None
    from devkit.rules import count_tasks

    checked, total = count_tasks(tasks.read_text(encoding="utf-8", errors="replace"))
    return f"{checked}/{total}"
