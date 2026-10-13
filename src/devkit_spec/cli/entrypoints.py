"""``devkit spec entrypoints derive``: derive capability/story entrypoints from spec bundles, and write chosen ones.

Text output (paths are workspace-relative):

- ``[CANDIDATES: <doc-id> path= new= missing= folded= declared=]`` per document, in document path order: its
  candidate paths by state, comma-separated (``-`` for none). ``new`` paths exist and are not declared yet,
  ``missing`` ones are new but absent from the working tree, ``folded`` ones are covered by a same-bundle ancestor
  candidate, ``declared`` ones are already covered by an entrypoint. With ``--all`` each path carries its spec count,
  ``src/a.py(2)``. ``--format json`` lists every pair with its spec and task (or count and specs);
- ``[SKIPPED: <value> kind=boundary|target|bundle|apply reason=]`` per input or candidate left out, with ``spec=``
  and ``task=`` when known;
- ``[APPLIED: <doc-id> path= added=]`` per document ``--apply`` wrote;
- ``[SUMMARY: pairs= new= declared= skipped= applied=]`` last.

Nothing is written without ``--apply``. Files that could not be indexed are ``SPEC_DOCUMENT_INVALID`` warnings; a
document ``--apply`` could not write is a ``SPEC_ENTRYPOINTS_APPLY_FAILED`` error after the result.
"""

from __future__ import annotations

import posixpath
from collections.abc import Sequence
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

from devkit_spec.cli.output import fields_line, sentinel
from devkit_spec.documents import Document, DocumentIndex, Kind, is_id
from devkit_spec.entrypoints import (
    Applied,
    Pair,
    Reason,
    SkipKind,
    Skipped,
    State,
    aggregate,
    apply,
    derive,
    exclude,
    load_bundle,
    select,
)
from devkit_spec.errors import (
    EntrypointsApplyError,
    EntrypointsInputInvalidError,
    EntrypointsInputMissingError,
    EntrypointsTargetError,
    UnresolvedIdError,
)

DEFAULT_STATUS = "completed,in-progress"


@click.group(name="entrypoints")
def entrypoints_group() -> None:
    """Code entrypoints of capabilities and stories, derived from spec bundles."""


@entrypoints_group.command(name="derive")
@click.option("--spec", "spec_dir", default=None, help="One spec bundle directory (specs/<YYYY-MM>/<YYYYMMDD>-<slug>)")
@click.option("--all", "every", is_flag=True, help="Aggregate every spec bundle under specs/")
@click.option("--status", default=None, help=f"With --all: comma-separated spec statuses [default: {DEFAULT_STATUS}]")
@click.option(
    "--min-count", type=int, default=None, help="With --all: keep pairs seen in at least N specs [default: 1]"
)
@click.option("--apply", "write", is_flag=True, help="Write new, existing candidate paths into the documents")
@click.option("--target", "targets", multiple=True, help="With --apply: write only this document ID or path (repeat)")
@click.option("--code", "codes", multiple=True, help="Keep only candidates equal to or under this path (repeat)")
@click.option("--exclude", "excludes", multiple=True, help="Drop candidates equal to or under this path (repeat)")
@workspace_option()
@FORMAT_OPTION
@boundary
def derive_cmd(
    spec_dir: str | None,
    every: bool,
    status: str | None,
    min_count: int | None,
    write: bool,
    targets: tuple[str, ...],
    codes: tuple[str, ...],
    excludes: tuple[str, ...],
    workspace_root: str | None,
    output_format: str,
) -> None:
    """Join tasks.md _Boundary paths with reconcile.md capability/story targets into document-code pairs.

    Exactly one of --spec and --all. Pairs are declarations joined mechanically, not proof that the code
    implements the document: review them, then --apply with --target and --code for the chosen ones. --apply
    appends to the documents' entrypoints frontmatter, keeps every other byte and is idempotent.
    """
    _check_options(spec_dir, every, status, min_count, write, targets)
    root = resolve_root(workspace_root)
    index = DocumentIndex.load(root)
    documents = {document.path: document for document in index.documents}
    skipped: list[Skipped] = []
    if spec_dir is not None:
        pairs, skipped = derive(root, load_bundle(root, _bundle_dir(root, spec_dir)), documents)
    else:
        per_bundle: list[list[Pair]] = []
        for spec in _specs(index, status or DEFAULT_STATUS):
            bundle_dir = spec.path.rsplit("/", 1)[0]
            try:
                bundle = load_bundle(root, bundle_dir)
            except (EntrypointsInputMissingError, EntrypointsInputInvalidError) as exc:
                reason = Reason.INPUT_MISSING if isinstance(exc, EntrypointsInputMissingError) else Reason.INVALID_INPUT
                skipped.append(Skipped(SkipKind.BUNDLE, bundle_dir, reason, spec=spec.id))
                continue
            bundle_pairs, bundle_skipped = derive(root, bundle, documents)
            per_bundle.append(bundle_pairs)
            skipped += bundle_skipped
        pairs = aggregate(per_bundle, 1 if min_count is None else min_count)

    derived = {pair.doc_path for pair in pairs}
    pairs = select(pairs, codes)
    pairs, excluded = exclude(pairs, excludes)
    skipped += excluded
    applied: list[Applied] = []
    errors: list[AdvisoryError] = []
    if write:
        only = _resolve_targets(index, targets, derived)
        result = apply(root, pairs, only)
        applied, skipped = result.applied, skipped + result.skipped
        if result.failures:
            paths = [path for path, _ in result.failures]
            errors.append(
                EntrypointsApplyError(
                    f"{len(paths)} document(s) could not be written",
                    *(f"{path}: {problem}" for path, problem in result.failures),
                    target_files=paths,
                )
            )
    summary = {
        "pairs": len(pairs),
        "new": sum(pair.state is State.NEW for pair in pairs),
        "declared": sum(pair.state is State.DECLARED for pair in pairs),
        "skipped": len(skipped),
        "applied": len(applied),
    }
    if is_json(output_format):
        echo_json(
            {
                "pairs": [pair.to_dict() for pair in pairs],
                "skipped": [item.to_dict() for item in skipped],
                "applied": [item.to_dict() for item in applied],
                "summary": summary,
                "errors": [error.to_dict() for error in errors],
                "notices": [notice.to_dict() for notice in index.problems],
            }
        )
    else:
        _echo_text(pairs, skipped, applied, summary)
    echo_notices(index.problems)
    exit_on_problems(errors)
    exit_on_warnings(index.problems)


def _check_options(
    spec_dir: str | None,
    every: bool,
    status: str | None,
    min_count: int | None,
    write: bool,
    targets: Sequence[str],
) -> None:
    if (spec_dir is None) == (not every):
        raise ArgumentError(
            "derive needs exactly one of --spec and --all",
            target_files=["--spec", "--all"],
            fix="Pass --spec specs/<YYYY-MM>/<YYYYMMDD>-<slug> for one bundle or --all for every bundle",
        )
    if spec_dir is not None and (status is not None or min_count is not None):
        raise ArgumentError(
            "--status and --min-count apply to --all only",
            target_files=["--status", "--min-count"],
            fix="Drop --status and --min-count, or use --all instead of --spec",
        )
    if min_count is not None and min_count < 1:
        raise ArgumentError(
            f"--min-count {min_count}: must be at least 1",
            target_files=["--min-count"],
            fix="Pass --min-count 1 or more",
        )
    if targets and not write:
        raise ArgumentError("--target requires --apply", target_files=["--target"], fix="Add --apply or drop --target")


def _bundle_dir(root: Path, value: str) -> str:
    """The workspace-relative form of ``--spec`` (absolute, or relative to the workspace root)."""
    path = Path(value)
    absolute = path.resolve() if path.is_absolute() else Path(posixpath.normpath((root / path).as_posix()))
    try:
        relative = absolute.relative_to(root).as_posix()
    except ValueError:
        relative = ""
    if not relative or relative == ".":
        raise ArgumentError(
            f"--spec {value}: not a directory inside the workspace",
            target_files=["--spec"],
            fix="Pass the bundle directory relative to the workspace root: specs/<YYYY-MM>/<YYYYMMDD>-<slug>",
        )
    return relative


def _specs(index: DocumentIndex, status: str) -> list[Document]:
    """The ``spec.md`` of every bundle (``specs/<YYYY-MM>/<bundle>/spec.md``) whose status is in ``status``, by ID."""
    wanted = {part.strip().lower() for part in status.split(",") if part.strip()}
    found = [
        document
        for document in index.documents
        if document.kind is Kind.SPEC
        and len(parts := document.path.split("/")) == 4
        and parts[0] == "specs"
        and parts[3] == "spec.md"
        and (not wanted or document.status.lower() in wanted)
    ]
    return sorted(found, key=lambda document: (document.id, document.path))


def _resolve_targets(index: DocumentIndex, targets: Sequence[str], derived: set[str]) -> set[str] | None:
    """The document paths ``--target`` names (IDs or workspace-relative paths); ``None`` without targets."""
    if not targets:
        return None
    only: set[str] = set()
    for target in targets:
        value = target.strip()
        if is_id(value):
            try:
                path = index.resolve(value).path
            except UnresolvedIdError as exc:
                raise EntrypointsTargetError(
                    f"--target {value}: no document has this ID", target_files=[value]
                ) from exc
        else:
            path = posixpath.normpath(value)
        if path not in derived:
            raise EntrypointsTargetError(f"--target {value}: not among the derived documents", target_files=[path])
        only.add(path)
    return only


CANDIDATE_GROUPS = ("new", "missing", "folded", "declared")


def _candidates(pairs: Sequence[Pair]) -> list[tuple[str, str, dict[str, list[str]]]]:
    """The pairs grouped per document (in pair order): each candidate path under its group of ``CANDIDATE_GROUPS``."""
    grouped: dict[tuple[str, str], dict[str, list[str]]] = {}
    for pair in pairs:
        groups = grouped.setdefault((pair.doc, pair.doc_path), {name: [] for name in CANDIDATE_GROUPS})
        if pair.state is State.DECLARED:
            group = "declared"
        elif pair.folded_into is not None:
            group = "folded"
        else:
            group = "new" if pair.exists else "missing"
        groups[group].append(pair.code if pair.count is None else f"{pair.code}({pair.count})")
    return [(doc, doc_path, groups) for (doc, doc_path), groups in grouped.items()]


def _echo_text(pairs: Sequence[Pair], skipped: Sequence[Skipped], applied: Sequence[Applied], summary: dict) -> None:
    for doc, doc_path, groups in _candidates(pairs):
        click.echo(
            sentinel("CANDIDATES", doc, path=doc_path, **{name: ",".join(paths) for name, paths in groups.items()})
        )
    for item in skipped:
        extra: dict[str, object] = {"kind": str(item.kind)}
        if item.spec:
            extra["spec"] = item.spec
        if item.task:
            extra["task"] = item.task
        click.echo(sentinel("SKIPPED", item.value, **extra, reason=str(item.reason)))
    for item in applied:
        click.echo(sentinel("APPLIED", item.doc, path=item.doc_path, added=",".join(item.added)))
    click.echo(fields_line("SUMMARY", **summary))
