"""Spec bundles: the ``spec.md``, ``plan.md`` and ``tasks.md`` skeletons a handoff or ``devkit spec new`` writes.

A spec bundle is ``specs/<YYYY-MM>/<YYYYMMDD>-<slug>/`` with ``SPEC-<slug>``, ``PLAN-<slug>`` and ``TASKS-<slug>``.
Each file carries devkit's skeleton marker as its first body line, so a workflow's ``not-skeleton`` check keeps the
stage open until the file is written for real. ``spec.md`` is the workflow anchor: it is bound to the workflow, and
the bound workflow is the only record of the work's ``task-kind`` (no ``kind`` field).

``create_spec`` creates a bundle without a proposal (``devkit spec new``): unlike ``devkit workflow new`` it writes
the document IDs the rules expect. ``spec.md``'s ``namespace`` names the document namespace the bundle belongs to;
without it the bundle is global. Its ``summary`` (one or two English sentences, ``RULE-document-summary``) is written
when given; a skeleton-marked ``spec.md`` is exempt from the rule until it is written.
"""

from __future__ import annotations

import errno
import logging
import os
import shutil
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from devkit.advisory import AdvisoryError
from devkit.core import remove_empty_tree
from devkit.core.frontmatter import locate
from devkit.workflow import Binding, write_binding

from devkit_spec.branches import require_development_branch
from devkit_spec.documents import DocumentIndex
from devkit_spec.errors import (
    SpecExistsError,
    SpecSlugError,
    SpecUnboundNotice,
    SpecWorkflowError,
    SpecWriteError,
    SpecWrongBranchError,
)
from devkit_spec.proposals.binding import BUGFIX_WORKFLOW, DEFAULT_WORKFLOW, resolve_binding
from devkit_spec.proposals.body import CarriedProposal, ensure_ac_ids
from devkit_spec.proposals.scaffold import (
    bundle_dir,
    bundle_namespace,
    new_slug,
    require_summary,
    single_file,
    yaml_scalar,
)

# devkit's not-skeleton check: specify stays open until the spec, plan and tasks are written and the line removed.
SKELETON_MARKER = "<!-- devkit:skeleton -->"
SPEC_FILE = "spec.md"

_log = logging.getLogger(__name__)


def text_value(value: object) -> str:
    """A frontmatter scalar as stripped text; ``""`` for nothing, a mapping or a list."""
    if value is None or isinstance(value, (dict, list)):
        return ""
    return str(value).strip()


def text_values(value: object) -> list[str]:
    """The non-empty items of a frontmatter list as text; ``[]`` for anything else."""
    return [text for item in value if (text := text_value(item))] if isinstance(value, list) else []


def mark_skeleton(content: str) -> str:
    """``content`` with the skeleton marker as the first body line, right after the frontmatter."""
    block = locate(content)
    if block is None:
        return content
    return content[: block.end] + SKELETON_MARKER + "\n" + content[block.end :]


def spec_dir(root: Path, slug: str, day: date) -> Path:
    return root / "specs" / day.strftime("%Y-%m") / f"{day.strftime('%Y%m%d')}-{slug}"


def _boundary_list(items: list[str]) -> str:
    return "".join(f"- `{item}`\n" for item in items)


_STORY_SECTION = """## 2. User Stories

- **US-1**: As a developer/agent, I want to implement {title} so that system capabilities are extended.

"""
# A defect is characterized, not told as a story (spec-specify references/bugfix.md, stage characterize).
_BUGFIX_SECTIONS = """## 2. Defect Characterization

- **Current behavior**: <trigger, environment and the observed wrong result, with evidence>
- **Expected behavior and its basis**: <the result the existing contract requires, citing its capability, story, ADR or test>
- **Behavior to preserve**: <call paths, input boundaries and contracts that must keep working, with their tests>
- **Reproduction conditions**: <the command, data and environment that reproduce the defect>

"""


def spec_files(
    slug: str,
    title: str,
    created: str,
    *,
    origin: str,
    carried: CarriedProposal | None = None,
    meta: dict[str, Any] | None = None,
    namespace: str | None = None,
    summary: str | None = None,
    target_docs_ref: str = "",
    bugfix: bool = False,
) -> dict[str, str]:
    """``spec.md``, ``plan.md`` and ``tasks.md`` of a spec bundle, each marked as a skeleton.

    ``bugfix`` gives ``spec.md`` the characterization sections of a defect (current, expected and preserved
    behavior, reproduction conditions) instead of a feature-style user story. ``origin`` opens the problem statement; ``carried`` fills the sections from a proposal body; ``meta`` is the
    proposal frontmatter (``milestone``, ``target_area``, ``boundaries``); ``namespace`` and ``summary`` become
    ``spec.md``'s ``namespace`` and ``summary`` (none written when ``None``).
    """
    carried = carried or CarriedProposal()
    meta = meta or {}
    problem = origin + ("\n" + carried.problem if carried.problem else "\n")
    non_goals = carried.non_goals or "1. **Scope Excluded**: <what this change will not do>\n\n"
    acceptance, ac_ids = ensure_ac_ids(carried.acceptance)
    notes = (
        "\n## 5. Carried Proposal Notes\n\nSections of the proposal that did not map to a spec section. Trim or "
        "promote them while drafting; they are not contracts.\n\n" + carried.notes
        if carried.notes
        else ""
    )
    milestone = text_value(meta.get("milestone"))
    extra = f"\nnamespace: {yaml_scalar(namespace)}" if namespace else ""
    extra += f"\nmilestone: {yaml_scalar(milestone)}" if milestone else ""
    summary_line = f"\nsummary: {yaml_scalar(summary)}" if summary else ""
    spec = f"""---
id: SPEC-{slug}
title: {yaml_scalar(title)}{summary_line}
status: planned
created: {created}{extra}
related_capabilities: []
related_stories: []
---

# [SPEC-{slug}] {title}

## 1. Problem Statement & Motivation

{problem}{_BUGFIX_SECTIONS if bugfix else _STORY_SECTION.format(title=title)}## 3. Non-Goals

{non_goals}## 4. Acceptance Criteria & Behavioral Contracts

{acceptance}{notes}"""

    target_area = text_value(meta.get("target_area")) or "<target area>"
    boundaries = meta.get("boundaries")
    boundaries = boundaries if isinstance(boundaries, dict) else {}
    owns, excludes = text_values(boundaries.get("owns")), text_values(boundaries.get("excludes"))
    planned = ""
    if owns:
        planned = "\n### Planned Boundaries:\n" + _boundary_list(owns)
        if excludes:
            planned += "\n### Excluded Boundaries:\n" + _boundary_list(excludes)
    plan = f"""---
id: PLAN-{slug}
spec: SPEC-{slug}
---

# Technical Plan: `SPEC-{slug}` {title}

## 1. Architecture Overview & Impact
- Target Area: {target_area}{target_docs_ref}

## 2. Component Breakdown & Interface Contracts
{planned}
## 3. Verification & Test Plan
- <commands and checks that verify the acceptance criteria>
"""

    task_boundary = ", ".join(owns) if owns else target_area
    tasks = f"""---
id: TASKS-{slug}
spec: SPEC-{slug}
plan: PLAN-{slug}
---

# Task Breakdown: `SPEC-{slug}` {title}

## Phase 1: Implementation
- [ ] **Task 1.1**: Core Implementation
  - **_Boundary**: {task_boundary}
  - _Requirements: {", ".join(ac_ids)}_
  - **Verification**: <command that verifies the task>
"""
    return {
        name: mark_skeleton(content) for name, content in ((SPEC_FILE, spec), ("plan.md", plan), ("tasks.md", tasks))
    }


def spec_only(binding: Binding | None) -> bool:
    """Whether a bundle bound to ``binding`` starts with ``spec.md`` alone: ``sdd-spec-bugfix`` writes the plan and
    tasks in its ``plan-tasks`` stage, after the defect is characterized."""
    return binding is not None and binding.workflow == BUGFIX_WORKFLOW


def write_spec_bundle(directory: Path, files: dict[str, str], binding: Binding | None, written: list[Path]) -> None:
    """Create ``directory`` (recorded in ``written``), write ``files`` and bind ``spec.md``."""
    make_dirs(directory, written)
    for name, content in files.items():
        (directory / name).write_text(content, encoding="utf-8")
    if binding is not None:
        write_binding(directory / SPEC_FILE, binding)


def make_dirs(path: Path, written: list[Path]) -> None:
    """Create ``path`` and its parents, recording the outermost directory created for a roll-back."""
    missing = path
    while not missing.parent.exists():
        missing = missing.parent
    if not path.exists():
        path.mkdir(parents=True)
        written.append(missing)


def move_path(
    source: Path,
    destination: Path,
    written: list[Path],
    moved: list[tuple[Path, Path]],
    leftovers: list[Path],
) -> None:
    """Move ``source`` to the absent ``destination`` so that ``roll_back`` undoes it whichever step fails.

    A rename is recorded in ``moved``. Across file systems (``EXDEV``) ``source`` is copied instead: ``destination``
    is recorded in ``written`` before the copy starts, so a partial copy is removed on roll-back, and the untouched
    ``source`` is appended to ``leftovers`` for the caller to remove (``remove_paths``) once every write succeeded.
    """
    try:
        os.rename(source, destination)
    except OSError as exc:
        if exc.errno != errno.EXDEV:
            raise
    else:
        moved.append((destination, source))
        return
    written.append(destination)
    if source.is_dir() and not source.is_symlink():
        shutil.copytree(source, destination, symlinks=True)
    else:
        shutil.copy2(source, destination, follow_symlinks=False)
    leftovers.append(source)


def remove_paths(paths: Sequence[Path]) -> None:
    """Remove each of ``paths`` (a directory with its contents), newest first; a failure is logged, not raised."""
    for path in reversed(paths):
        try:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink(missing_ok=True)
        except OSError as exc:
            _log.info("%s could not be removed: %s", path, exc)


def _relocate(path: Path, moves: Sequence[tuple[Path, Path]]) -> Path:
    """Where ``path`` is after ``moves`` (``(source, destination)`` in the order they ran) carried it or a parent."""
    for source, destination in moves:
        if path == source or path.is_relative_to(source):
            path = destination / path.relative_to(source)
    return path


def roll_back(written: list[Path], moved: Sequence[tuple[Path, Path]] = ()) -> list[str]:
    """Undo a failed write: move each ``(new, old)`` of ``moved`` back, newest first, then remove what was written,
    newest first; returns what could not be undone (also logged), ``[]`` when everything was.

    A written path a move-back carried along (a directory ``make_dirs`` created inside a moved directory) is followed
    to where it went: a file is removed there, a directory only when it holds no file (``remove_empty_tree``). A
    written directory that holds something whose move-back failed is never removed, so nothing moved is lost; such a
    path is reported where it is after the later move-backs, which may have carried it along too.
    """
    problems: list[str] = []
    back: list[tuple[Path, Path]] = []
    # A path left at its new location, where it should have gone, why not, and how many move-backs ran before it.
    stuck: list[tuple[Path, Path, OSError, int]] = []
    for new, old in reversed(moved):
        try:
            shutil.move(new, old)
        except OSError as exc:
            stuck.append((new, old, exc, len(back)))
        else:
            back.append((new, old))
    kept = [_relocate(path, back[ran:]) for path, _, _, ran in stuck]
    for here, (_, old, exc, _) in zip(kept, stuck, strict=True):
        problems.append(f"{here} could not be moved back to {old}: {exc}")
    for path in reversed(written):
        here = _relocate(path, back)
        holding = [item for item in kept if item == here or item.is_relative_to(here)]
        try:
            if holding:
                problems.append(f"{here} was kept: it holds {', '.join(map(str, holding))}, not moved back")
            elif here != path and here.is_dir() and not here.is_symlink():
                if not remove_empty_tree(here) and here.exists():
                    problems.append(f"{here} was kept: it is not empty")
            elif here.is_dir() and not here.is_symlink():
                shutil.rmtree(here)
            else:
                here.unlink(missing_ok=True)
        except OSError as exc:
            problems.append(f"{here} could not be removed: {exc}")
    for problem in problems:
        _log.info("roll-back: %s", problem)
    return problems


@dataclass
class CreatedSpec:
    """A spec bundle created without a proposal: its ``id``, directory (workspace-relative) and bound workflow."""

    id: str
    dir: str
    workflow: str | None
    namespace: str | None = None
    notices: list[AdvisoryError] = field(default_factory=list)

    @property
    def next_command(self) -> str | None:
        return f"devkit workflow next --unit {self.dir}" if self.workflow else None

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "dir": self.dir,
            "workflow": self.workflow,
            "namespace": self.namespace,
            "next_command": self.next_command,
            "notices": [notice.to_dict() for notice in self.notices],
        }


def create_spec(
    root: Path,
    slug: str,
    *,
    title: str | None = None,
    workflow: str | None = None,
    namespace: str | None = None,
    summary: str | None = None,
    day: date | None = None,
    cwd: Path | None = None,
) -> CreatedSpec:
    """Create ``specs/<YYYY-MM>/<YYYYMMDD>-<slug>/`` under the workspace ``root`` and bind ``spec.md``.

    ``workflow`` defaults to ``sdd-spec-feature`` (unbound, with a ``SPEC_UNBOUND`` notice, when the project does not
    have it). An ``sdd-spec-bugfix`` bundle gets only ``spec.md`` (``spec_only``); its workflow writes the plan and
    tasks.
    ``summary`` is written to ``spec.md`` only when given; ``namespace`` when given, else the namespace ``cwd`` lies
    in (``bundle_namespace``, reported on the result). Raises before writing:
    ``SpecSlugError``, ``SpecWrongBranchError`` (in Git, a checkout not on ``dev-<slug>``), ``ArgumentError`` (a ``namespace`` that is neither ``global`` nor registered, a ``summary``
    that is empty or not English), ``SpecExistsError``
    (``SPEC-<slug>`` or ``PROP-<slug>`` is declared, a proposal of the slug exists, or the directory exists),
    ``SpecWorkflowError`` (an explicit workflow that does not resolve or validate). A failure while writing removes
    what was written, then raises ``SpecWriteError``, or the ``AdvisoryError`` itself when the failure was one (such
    as a ``FrontmatterError`` binding ``spec.md``) and the roll-back was complete; what the roll-back could not remove is
    in the ``SpecWriteError`` details.
    """
    root = root.resolve()
    slug = new_slug(slug.strip().removeprefix("SPEC-"), error=SpecSlugError)
    require_development_branch(root, slug, "devkit spec new", SpecWrongBranchError)
    namespace, reported = bundle_namespace(root, namespace, cwd)
    summary = require_summary(summary)
    day = day or date.today()
    directory = spec_dir(root, slug, day)
    index = DocumentIndex.load(root)
    taken = [d.path for document_id in (f"SPEC-{slug}", f"PROP-{slug}") for d in index.by_id.get(document_id, [])]
    taken += [
        path.relative_to(root).as_posix()
        for path in (bundle_dir(root, slug), single_file(root, slug), directory)
        if path.exists()
    ]
    if taken:
        taken = list(dict.fromkeys(taken))
        raise SpecExistsError(f"slug {slug} is taken: {', '.join(taken)}", target_files=taken)
    binding, unbound = resolve_binding(root, workflow, "--workflow", field="--workflow", error=SpecWorkflowError)

    title = (title or "").strip() or slug
    files = spec_files(
        slug,
        title,
        day.isoformat(),
        origin="<Describe the problem, who has it and why it matters now.>\n",
        namespace=namespace,
        summary=summary,
        bugfix=spec_only(binding),
    )
    if spec_only(binding):
        # sdd-spec-bugfix writes plan.md and tasks.md in its plan-tasks stage; a skeleton tasks.md would have to match the
        # characterized spec's criteria for the characterize stage's lint-clean exit.
        files = {SPEC_FILE: files[SPEC_FILE]}
    written: list[Path] = []
    try:
        write_spec_bundle(directory, files, binding, written)
    except Exception as exc:
        problems = roll_back(written)
        if isinstance(exc, AdvisoryError) and not problems:
            raise
        what = (
            "the files it wrote were removed"
            if not problems
            else "the roll-back was incomplete; inspect the paths in the details before retrying"
        )
        raise SpecWriteError(f"creating SPEC-{slug} failed; {what}", str(exc), *problems) from exc
    rel = directory.relative_to(root).as_posix()
    created = CreatedSpec(
        id=f"SPEC-{slug}", dir=rel, workflow=binding.workflow if binding else None, namespace=reported
    )
    if unbound is not None:
        created.notices.append(
            SpecUnboundNotice(
                f"SPEC-{slug} is not bound to a workflow: {DEFAULT_WORKFLOW} is not available ({unbound.code})",
                target_files=[f"{rel}/{SPEC_FILE}"],
                fix=f"Bind it with devkit workflow bind --unit {rel} --workflow <id> once a workflow fits it",
            )
        )
    return created
