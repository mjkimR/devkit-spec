"""Scope inputs: what a proposal or spec bundle declares, and what Git observes in a worktree.

- Proposal (``prop`` stage): the ``targets`` of ``docs/proposals/PROP-<slug>/target-docs.md`` are the document side,
  the ``entrypoints`` of the existing capability and story targets the code candidates.
- Spec bundle (``spec`` stage): ``reconcile.md`` ``targets`` (not ``waived``) are the document side, or, without
  ``reconcile.md``, ``target-docs.md`` (``prop`` stage); ``tasks.md`` ``_Boundary`` entries are declared code (they win
  over a candidate of the same path), the targets' ``entrypoints`` candidates. When both target lists exist, the
  paths only one names are reported as ``Diff`` and not merged.
- Observed (``build`` stage): the paths changed since the record's base revision (``base..HEAD``), staged, unstaged
  and untracked, relative to the workspace root.

``targets`` is a list of ``{file: <workspace-relative path>, resolution: ...}`` in both files. Paths follow the
entrypoint path contract. What cannot become a path is ``Unresolved`` with its reason, never dropped silently.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from devkit.core import FrontmatterError, GitError
from devkit.core.frontmatter import parse

from devkit_spec.entrypoints import classify_boundary, entrypoint_bearing, normalize, parse_boundaries
from devkit_spec.errors import (
    EntrypointsPathError,
    ProposalNotFoundError,
    ScopeInputInvalidError,
    ScopeSpecNotFoundError,
)
from devkit_spec.proposals.scaffold import PROPOSAL_FILE, PROPOSALS, TARGET_DOCS, clean_slug
from devkit_spec.scope.deadline import Deadline, git_lines
from devkit_spec.scope.model import Diff, Granularity, ScopePath, ScopeSet, Source, Stage, Unresolved

RECONCILE = "reconcile.md"
TASKS = "tasks.md"
SPEC = "spec.md"
WAIVED = "waived"


def kind_of(root: Path, path: str) -> Granularity:
    """Whether the workspace-relative ``path`` is a file or a directory of the working tree, else ``unknown``."""
    target = root / path
    if target.is_dir():
        return Granularity.DIR
    if target.is_file():
        return Granularity.FILE
    return Granularity.UNKNOWN


def _frontmatter(path: Path, relative: str) -> dict[str, Any] | None:
    """The frontmatter of ``path``; ``None`` when it has none; ``ScopeInputInvalidError`` when unreadable."""
    try:
        return parse(path.read_text(encoding="utf-8")).data
    except (OSError, UnicodeDecodeError) as exc:
        raise ScopeInputInvalidError(f"cannot read {relative}: {exc}", target_files=[relative]) from exc
    except FrontmatterError as exc:
        raise ScopeInputInvalidError(f"cannot read {relative}: {exc.message}", target_files=[relative]) from exc


def _declared_id(path: Path) -> str:
    """The ``id`` of a document's frontmatter, ``""`` when it has none or cannot be read."""
    try:
        data = parse(path.read_text(encoding="utf-8")).data or {}
    except (OSError, UnicodeDecodeError, FrontmatterError):
        return ""
    value = data.get("id")
    return value.strip() if isinstance(value, str) else ""


def _targets(path: Path, relative: str) -> list[tuple[str, str]] | None:
    """``(file, resolution)`` of each target; ``None`` when the file does not exist or declares no ``targets``."""
    if not path.is_file():
        return None
    data = _frontmatter(path, relative) or {}
    if "targets" not in data:
        return None
    value = data["targets"] or []
    if not isinstance(value, list):
        raise ScopeInputInvalidError(f"cannot read {relative}: targets must be a list", target_files=[relative])
    targets = []
    for position, entry in enumerate(value, 1):
        if not isinstance(entry, dict) or not isinstance(entry.get("file", ""), str):
            raise ScopeInputInvalidError(
                f"cannot read {relative}: targets[{position}] must be a mapping with a string file",
                target_files=[relative],
            )
        resolution = entry.get("resolution")
        targets.append((entry.get("file", "").strip(), resolution.strip() if isinstance(resolution, str) else ""))
    return targets


def _entrypoints(root: Path, file: str) -> list[str]:
    try:
        data = parse((root / file).read_text(encoding="utf-8")).data or {}
    except (OSError, UnicodeDecodeError, FrontmatterError):
        return []
    value = data.get("entrypoints")
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _add_doc_targets(root: Path, scope: ScopeSet, targets: list[tuple[str, str]], stage: Stage) -> None:
    """Record document targets and the code candidates their entrypoints provide.

    A waived target, an invalid path, a planned document (not in the working tree; it still counts as a document,
    so a shared planned path overlaps) and a capability or story without entrypoints are unresolved.
    """
    seen_docs = {path.path for path in scope.docs}
    seen_code = {path.path for path in scope.code}
    for raw, resolution in targets:
        if not raw:
            continue
        if resolution.lower() == WAIVED:
            scope.unresolved.append(Unresolved(raw, "waived", Source.DECLARED_DOC))
            continue
        try:
            file = normalize(raw)
        except EntrypointsPathError:
            scope.unresolved.append(Unresolved(raw, "invalid-path", Source.DECLARED_DOC))
            continue
        if file in seen_docs:
            continue
        seen_docs.add(file)
        kind = kind_of(root, file)
        scope.docs.append(ScopePath(file, kind, Source.DECLARED_DOC, stage))
        if kind is Granularity.UNKNOWN:
            scope.unresolved.append(Unresolved(file, "planned-doc", Source.DECLARED_DOC))
            continue
        if not entrypoint_bearing(file):
            continue
        entries = _entrypoints(root, file)
        if not entries:
            scope.unresolved.append(Unresolved(file, "no-entrypoints", Source.CANDIDATE))
            continue
        for entry in entries:
            try:
                code = normalize(entry)
            except EntrypointsPathError:
                continue
            if code not in seen_code:
                seen_code.add(code)
                scope.code.append(ScopePath(code, kind_of(root, code), Source.CANDIDATE, stage))
    scope.docs.sort(key=lambda path: path.path)
    scope.code.sort(key=lambda path: path.path)


def _diff(blueprint: list[tuple[str, str]], reconcile: list[tuple[str, str]]) -> list[Diff]:
    def paths(targets: list[tuple[str, str]]) -> set[str]:
        found = set()
        for raw, resolution in targets:
            if resolution.lower() == WAIVED:
                continue
            try:
                found.add(normalize(raw))
            except EntrypointsPathError:
                continue
        return found

    planned, reconciled = paths(blueprint), paths(reconcile)
    diff = [Diff(path, "target-docs") for path in planned - reconciled]
    diff += [Diff(path, "reconcile") for path in reconciled - planned]
    return sorted(diff, key=lambda item: (item.path, item.side))


def from_proposal(root: Path, slug: str) -> ScopeSet:
    """The ``prop``-stage scope of proposal ``slug`` (a ``PROP-`` prefix is accepted).

    Raises ``ProposalNotFoundError`` when no bundle or single-file proposal has the slug.
    """
    clean = clean_slug(slug)
    bundle = root / PROPOSALS / f"PROP-{clean}"
    single = root / PROPOSALS / f"PROP-{clean}.md"
    if (bundle / PROPOSAL_FILE).is_file():
        anchor = bundle / PROPOSAL_FILE
    elif single.is_file():
        anchor = single
    else:
        raise ProposalNotFoundError(f"no proposal has the slug {clean!r}", target_files=[f"{PROPOSALS}/PROP-{clean}"])
    scope = ScopeSet(id=_declared_id(anchor) or f"PROP-{clean}")
    relative = f"{PROPOSALS}/PROP-{clean}/{TARGET_DOCS}"
    blueprint = bundle / TARGET_DOCS
    targets = _targets(blueprint, relative)
    if targets is None:
        reason = "no-targets" if blueprint.is_file() else "missing-target-docs"
        scope.unresolved.append(Unresolved(TARGET_DOCS, reason, Source.DECLARED_DOC))
        return scope
    _add_doc_targets(root, scope, targets, Stage.PROP)
    return scope


def from_spec(root: Path, spec_dir: str) -> ScopeSet:
    """The ``spec``-stage scope of the bundle at the workspace-relative ``spec_dir`` (declarations only).

    Raises ``ScopeSpecNotFoundError`` when it is not a directory and ``ScopeInputInvalidError`` when an input
    cannot be read.
    """
    base = root / spec_dir
    if not base.is_dir():
        raise ScopeSpecNotFoundError(f"spec bundle not found: {spec_dir}", target_files=[spec_dir])
    scope = ScopeSet(id=_declared_id(base / SPEC) or base.name)
    tasks_path = base / TASKS
    if not tasks_path.is_file():
        scope.unresolved.append(Unresolved(TASKS, "missing-tasks", Source.DECLARED_CODE))
    else:
        try:
            text = tasks_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            relative = f"{spec_dir}/{TASKS}"
            raise ScopeInputInvalidError(f"cannot read {relative}: {exc}", target_files=[relative]) from exc
        seen: set[str] = set()
        for task in parse_boundaries(text):
            for raw in task.values:
                code, reason = classify_boundary(raw)
                if code is None:
                    scope.unresolved.append(Unresolved(raw, str(reason), Source.DECLARED_CODE))
                elif code not in seen:
                    seen.add(code)
                    scope.code.append(ScopePath(code, kind_of(root, code), Source.DECLARED_CODE, Stage.SPEC))
    reconcile = _targets(base / RECONCILE, f"{spec_dir}/{RECONCILE}")
    blueprint = _targets(base / TARGET_DOCS, f"{spec_dir}/{TARGET_DOCS}")
    if reconcile is not None:
        _add_doc_targets(root, scope, reconcile, Stage.SPEC)
        if blueprint is not None:
            scope.diff = _diff(blueprint, reconcile)
    else:
        scope.unresolved.append(Unresolved(RECONCILE, "missing-reconcile", Source.DECLARED_DOC))
        if blueprint is not None:
            _add_doc_targets(root, scope, blueprint, Stage.PROP)
    scope.code.sort(key=lambda path: path.path)
    return scope


def observe_git(
    root: Path, base_revision: str, deadline: Deadline, first_seen: str
) -> tuple[list[ScopePath], list[Unresolved]]:
    """The paths changed in the worktree at ``root``: ``base_revision..HEAD``, staged, unstaged and untracked.

    Paths are relative to ``root`` and limited to it. Renames are not detected, so a moved file contributes both its
    old and its new path. A path outside the entrypoint path contract (a glob character or a colon in its name) is
    left out. An empty or unknown ``base_revision`` skips the committed range and is
    unresolved. Raises ``ScopeTimeoutError`` when the deadline passes and ``GitError`` when Git fails otherwise.
    """
    seen: set[str] = set()
    observed: list[ScopePath] = []
    unresolved: list[Unresolved] = []

    def add(paths: list[str]) -> None:
        for raw in paths:
            try:
                path = normalize(raw)
            except EntrypointsPathError:
                continue
            if path not in seen:
                seen.add(path)
                observed.append(ScopePath(path, kind_of(root, path), Source.OBSERVED, Stage.BUILD, first_seen))

    changed = ("diff", "--name-only", "--no-renames", "-z", "--relative")
    if not base_revision:
        unresolved.append(Unresolved("", "missing-base-revision", Source.OBSERVED))
    else:
        try:
            add(git_lines(root, *changed, f"{base_revision}..HEAD", deadline=deadline))
        except GitError as exc:
            if exc.returncode is None:
                raise
            unresolved.append(Unresolved(base_revision, "unknown-base-revision", Source.OBSERVED))
    add(git_lines(root, *changed, "--cached", deadline=deadline))
    add(git_lines(root, *changed, deadline=deadline))
    add(git_lines(root, "ls-files", "-z", "--others", "--exclude-standard", deadline=deadline))
    observed.sort(key=lambda path: path.path)
    return observed, unresolved
