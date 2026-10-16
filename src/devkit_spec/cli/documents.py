"""``devkit spec resolve``, ``refs`` and ``list``: find documents by ID, follow their references, browse them.

Text output (paths are relative to the workspace root):

- ``resolve``: one ``[DOCUMENT: <id> kind= status= path=]`` line per resolved ID; unresolved or duplicated IDs
  are errors after the lines that did resolve.
- ``refs``: ``[REF: <id> path= status= fields= count=]`` per referenced (``--direction out``) or referencing
  (``--direction in``) document, in ID order; ``path=-`` is a reference to an ID no document declares.
- ``list``: ``[DOCUMENT: <id> kind= status= path= tasks= title=]`` per document in kind, then ID order (feedback by
  severity first); ``tasks`` is ``<checked>/<total>`` of a spec's ``tasks.md``. Proposal lines add ``task_kind=``,
  ``planning_effort=`` and ``dev_effort=`` after ``tasks=``; feedback lines add ``severity=``,
  ``scope=`` and ``target=`` after ``tasks=``. ``--where FIELD=A,B`` keeps documents whose frontmatter ``FIELD``
  is one of the values.

``refs`` and ``list`` end with ``[PAGE: total= offset= limit= count= next=]`` and, when more items follow,
``[NEXT_CMD: ...]`` for the next page. Files that could not be indexed are ``SPEC_DOCUMENT_INVALID`` warnings;
``list --status`` adds a ``SPEC_LIST_STATUS_UNKNOWN`` notice naming the values no document of the selected kinds
carries.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
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

from devkit_spec.branches import planning_branches
from devkit_spec.cli.output import echo_page, page, sentinel
from devkit_spec.config import Namespace, read_spec_config
from devkit_spec.documents import Document, DocumentIndex, Kind, Reference
from devkit_spec.entrypoints.paths import normalize, overlaps
from devkit_spec.errors import ListStatusUnknownNotice
from devkit_spec.namespaces import Selection, namespace_resolver, select

WORKSPACE = workspace_option()
LIMIT = click.option("--limit", "-n", type=int, default=20, show_default=True, help="Items per page; 0 for all")
OFFSET = click.option("--offset", type=int, default=0, show_default=True, help="Items to skip")
_KIND_ORDER = {kind: position for position, kind in enumerate(Kind)}
# Feedback ``severity`` values from the most to the least urgent; any other value, or none, ranks after them.
SEVERITY_ORDER = ("critical", "blocked", "workaround", "noise")
# The proposal frontmatter fields ``list`` prints on proposal lines and records.
PROPOSAL_FIELDS = ("task_kind", "planning_effort", "dev_effort")
# The feedback frontmatter fields ``list`` prints on feedback lines and records.
FEEDBACK_FIELDS = ("severity", "scope", "target")


@dataclass(frozen=True)
class WhereItem:
    """One ``--where FIELD=A,B`` item: the frontmatter field, its accepted values lower-cased, the text given."""

    field: str
    values: frozenset[str]
    given: str


Where = tuple[WhereItem, ...]


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


def _where(given: tuple[str, ...]) -> Where:
    """Parse ``--where FIELD=A,B`` items; a missing ``=``, field or value is an ``ARGUMENT_INVALID``."""
    parsed: list[WhereItem] = []
    for item in given:
        field, equals, listed = item.partition("=")
        values = frozenset(part.strip().lower() for part in listed.split(",") if part.strip())
        if not equals or not field.strip() or not values:
            raise ArgumentError(
                f"--where {item}: expected FIELD=VALUE[,VALUE...]",
                target_files=["--where"],
                fix="Pass --where with a frontmatter field and at least one value, e.g. --where severity=critical",
            )
        parsed.append(WhereItem(field.strip(), values, item))
    return tuple(parsed)


def _field_values(value: object) -> set[str]:
    """The lower-cased texts a parsed frontmatter value matches: a scalar its text (a boolean ``true``/``false``, a
    date or timestamp its ISO 8601 form), a list the texts of its scalar elements; a mapping or ``null`` nothing."""
    if isinstance(value, list):
        return {text for element in value if not isinstance(element, list) for text in _field_values(element)}
    if value is None or isinstance(value, dict):
        return set()
    if isinstance(value, bool):
        return {"true" if value else "false"}
    if isinstance(value, date):
        return {value.isoformat().lower()}
    return {str(value).strip().lower()}


def _matches(document: Document, where: Where) -> bool:
    return all(_field_values(document.frontmatter.get(item.field)) & item.values for item in where)


def _severity_rank(document: Document) -> int:
    """The position of a feedback document's ``severity`` in ``SEVERITY_ORDER``; ``0`` for other kinds."""
    if document.kind is not Kind.FEEDBACK:
        return 0
    severity = _text(document.frontmatter.get("severity")).lower()
    return SEVERITY_ORDER.index(severity) if severity in SEVERITY_ORDER else len(SEVERITY_ORDER)


def _proposal_fields(document: Document) -> dict[str, str | None]:
    """``task_kind``, ``planning_effort`` and ``dev_effort`` of a proposal document (``None`` when absent); empty for
    other kinds."""
    if document.kind is not Kind.PROPOSAL:
        return {}
    return {name: _text(document.frontmatter.get(name)) or None for name in PROPOSAL_FIELDS}


def _feedback_fields(document: Document) -> dict[str, str | None]:
    """``severity``, ``scope`` and ``target`` of a feedback document (``None`` when absent); empty for other kinds."""
    if document.kind is not Kind.FEEDBACK:
        return {}
    return {name: _text(document.frontmatter.get(name)) or None for name in FEEDBACK_FIELDS}


def _text(value: object) -> str:
    return str(value).strip() if value is not None and not isinstance(value, (list, dict)) else ""


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
@click.option(
    "--history", is_flag=True, help="Include the files of completed spec bundles (their feedback is always included)"
)
@click.option(
    "--where",
    "where_items",
    multiple=True,
    metavar="FIELD=VALUE[,VALUE...]",
    help="Keep documents whose frontmatter FIELD is one of the values (case-insensitive; a list field when one "
    "element is); repeat to require several fields",
)
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
    where_items: tuple[str, ...],
    file: str | None,
    namespace: str | None,
    all_namespaces: bool,
    limit: int,
    offset: int,
    workspace_root: str | None,
    output_format: str,
) -> None:
    """List documents of the given KINDs (default: all), current ones only unless --history.

    --file finds the documents that own a code path through their ``entrypoints``; --where filters by any
    frontmatter field, such as a feedback document's severity or scope. Feedback is ordered by severity. KIND is one
    of: capability, story, architecture, decision, proposal, proposal-decision, spec, plan, tasks, reconcile,
    feedback, material. In a workspace with namespaces, the namespace of the current directory (plus the
    global documents) is shown unless --namespace or --all-namespaces says otherwise.
    """
    _check_page(limit, offset)
    where = _where(where_items)
    if file is not None:
        normalize(file)  # SPEC_ENTRYPOINTS_PATH_INVALID, as derive reports it, rather than matching nothing
    index = _load(workspace_root)
    scope = NamespaceScope.of(index, namespace, all_namespaces)
    requested = (
        list(dict.fromkeys(part.strip().lower() for part in status.split(",") if part.strip())) if status else []
    )
    statuses = set(requested)
    wanted = {Kind(kind) for kind in kinds}
    planning = _planning(index)
    selected = [
        document
        for document in index.documents
        if (not wanted or document.kind in wanted)
        and (history or not index.is_historical(document))
        and (not statuses or _shown_status(document, planning).lower() in statuses)
        and (not area or area.lower() in document.area.lower())
        and (not query or query.lower() in document.id.lower() or query.lower() in document.title.lower())
        and _matches(document, where)
        and scope.accepts(document)
        and (file is None or _overlaps(document, file))
    ]
    selected.sort(
        key=lambda document: (_KIND_ORDER[document.kind], _severity_rank(document), document.id, document.path)
    )
    shown = page(selected, offset, limit)
    tasks = {document.path: _tasks(index.root, document) for document in shown}
    notices = [*index.problems, *_unknown_statuses(index, wanted, requested)]
    if is_json(output_format):
        echo_json(
            {
                "total": len(selected),
                "offset": offset,
                "limit": limit,
                "namespace": scope.selection.name,
                "documents": [
                    document.to_dict()
                    | _planning_fields(document, planning)
                    | {
                        "namespace": scope.namespace_of(document),
                        "historical": index.is_historical(document),
                        "tasks": tasks[document.path],
                    }
                    | _proposal_fields(document)
                    | _feedback_fields(document)
                    for document in shown
                ],
                "notices": [notice.to_dict() for notice in notices],
            }
        )
    else:
        for document in shown:
            click.echo(
                sentinel(
                    "DOCUMENT",
                    document.id,
                    kind=document.kind,
                    status=_shown_status(document, planning),
                    path=document.path,
                    **{key: value for key, value in _planning_fields(document, planning).items() if key != "status"},
                    tasks=tasks[document.path],
                    **_proposal_fields(document),
                    **_feedback_fields(document),
                    **scope.fields(document),
                    title=document.title,
                )
            )
        args = ["list", *kinds]
        for flag, given in (("--status", status), ("--area", area), ("--query", query), ("--file", file)):
            if given is not None:
                args += [flag, given]
        args += ["--history"] if history else []
        for item in where:
            args += ["--where", item.given]
        args += scope.args(namespace, all_namespaces)
        echo_page(len(selected), offset, limit, len(shown), [*args, *_paging_args(workspace_root, limit)])
    _finish(notices)


def _planning(index: DocumentIndex) -> dict[str, str]:
    """``slug -> plan-<slug> ref`` of the proposals whose Planning branch exists (``planning_branches``)."""
    return planning_branches(index.root)


def _shown_status(document: Document, planning: dict[str, str]) -> str:
    """The status ``list`` shows: a draft proposal whose ``plan-<slug>`` exists is ``reviewing`` (01 §5.1). Only the
    display changes; the base's ``status`` is not written."""
    if document.kind == Kind.PROPOSAL and document.status == "draft" and document.id.removeprefix("PROP-") in planning:
        return "reviewing"
    return document.status


def _planning_fields(document: Document, planning: dict[str, str]) -> dict[str, object]:
    """``status`` and ``planning_branch`` of a draft proposal shown as ``reviewing``; nothing for any other."""
    shown = _shown_status(document, planning)
    if shown == document.status:
        return {}
    return {"status": shown, "planning_branch": planning[document.id.removeprefix("PROP-")]}


def _unknown_statuses(index: DocumentIndex, wanted: set[Kind], requested: list[str]) -> list[AdvisoryError]:
    """``SPEC_LIST_STATUS_UNKNOWN`` for the requested statuses that no indexed document of the wanted kinds (every
    kind when none is wanted) carries, whatever its history or namespace; empty when each one occurs."""
    if not requested:
        return []
    known = {document.status.lower() for document in index.documents if not wanted or document.kind in wanted}
    known.discard("")
    unknown = [value for value in requested if value not in known]
    if not unknown:
        return []
    kinds = " or ".join(str(kind) for kind in sorted(wanted, key=_KIND_ORDER.__getitem__))
    fix = (
        f"Pass one of the statuses these documents carry: {', '.join(sorted(known))}"
        if known
        else "No document of these kinds carries a status; drop --status"
    )
    return [
        ListStatusUnknownNotice(
            f"--status {','.join(unknown)}: no {kinds + ' ' if kinds else ''}document carries "
            f"{'this status' if len(unknown) == 1 else 'these statuses'}; the filter was applied as given",
            target_files=["--status"],
            fix=fix,
        )
    ]


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
