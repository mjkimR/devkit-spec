"""Spec bundles: the ``spec.md``, ``plan.md`` and ``tasks.md`` skeletons a handoff or ``devkit spec new`` writes.

A spec bundle is ``specs/<YYYY-MM>/<YYYYMMDD>-<slug>/`` with ``SPEC-<slug>``, ``PLAN-<slug>`` and ``TASKS-<slug>``.
Each file carries devkit's skeleton marker as its first body line, so a workflow's ``not-skeleton`` check keeps the
stage open until the file is written for real. ``spec.md`` is the workflow anchor: it is bound to the workflow and,
for ``bugfix``, carries ``kind: bugfix``.

``create_spec`` creates a bundle without a proposal (``devkit spec new``): unlike ``devkit workflow new`` it writes
the document IDs the rules expect. ``spec.md``'s ``namespace`` names the document namespace the bundle belongs to;
without it the bundle is global. Its ``summary`` (one or two English sentences, ``RULE-document-summary``) is written
when given; a skeleton-marked ``spec.md`` is exempt from the rule until it is written.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from devkit.advisory import AdvisoryError
from devkit.core.frontmatter import locate
from devkit.workflow import Binding, write_binding

from devkit_spec.documents import DocumentIndex
from devkit_spec.errors import SpecExistsError, SpecSlugError, SpecUnboundNotice, SpecWorkflowError, SpecWriteError
from devkit_spec.proposals.binding import BUGFIX_WORKFLOW, DEFAULT_WORKFLOW, resolve_binding
from devkit_spec.proposals.body import CarriedProposal, ensure_ac_ids
from devkit_spec.proposals.scaffold import (
    bundle_dir,
    clean_slug,
    require_namespace,
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


def spec_files(
    slug: str,
    title: str,
    created: str,
    *,
    origin: str,
    carried: CarriedProposal | None = None,
    meta: dict[str, Any] | None = None,
    kind: str | None = None,
    namespace: str | None = None,
    summary: str | None = None,
    target_docs_ref: str = "",
) -> dict[str, str]:
    """``spec.md``, ``plan.md`` and ``tasks.md`` of a spec bundle, each marked as a skeleton.

    ``origin`` opens the problem statement; ``carried`` fills the sections from a proposal body; ``meta`` is the
    proposal frontmatter (``milestone``, ``target_area``, ``boundaries``); ``kind``, ``namespace`` and ``summary``
    become ``spec.md``'s ``kind``, ``namespace`` and ``summary`` (none written when ``None``).
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
    kind_line = f"\nkind: {yaml_scalar(kind)}" if kind else ""
    summary_line = f"\nsummary: {yaml_scalar(summary)}" if summary else ""
    spec = f"""---
id: SPEC-{slug}
title: {yaml_scalar(title)}{summary_line}
status: planned{kind_line}
created: {created}{extra}
related_capabilities: []
related_stories: []
---

# [SPEC-{slug}] {title}

## 1. Problem Statement & Motivation

{problem}## 2. User Stories

- **US-1**: As a developer/agent, I want to implement {title} so that system capabilities are extended.

## 3. Non-Goals

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


def spec_kind(binding: Binding | None) -> str | None:
    """The ``kind`` ``spec.md`` carries for its workflow: ``bugfix`` for workflow ``bugfix``."""
    return BUGFIX_WORKFLOW if binding is not None and binding.workflow == BUGFIX_WORKFLOW else None


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


def roll_back(written: list[Path], moved: tuple[Path, Path] | None = None) -> None:
    """Undo a failed write: move ``moved[0]`` back to ``moved[1]``, then remove what was written, newest first."""
    if moved is not None:
        try:
            shutil.move(moved[0], moved[1])
        except OSError as exc:
            _log.info("%s could not be moved back to %s: %s", moved[0], moved[1], exc)
    for path in reversed(written):
        try:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink(missing_ok=True)
        except OSError as exc:
            _log.info("%s could not be removed: %s", path, exc)


@dataclass
class CreatedSpec:
    """A spec bundle created without a proposal: its ``id``, directory (workspace-relative) and bound workflow."""

    id: str
    dir: str
    workflow: str | None
    notices: list[AdvisoryError] = field(default_factory=list)

    @property
    def next_command(self) -> str | None:
        return f"devkit workflow next --unit {self.dir}" if self.workflow else None

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "dir": self.dir,
            "workflow": self.workflow,
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
) -> CreatedSpec:
    """Create ``specs/<YYYY-MM>/<YYYYMMDD>-<slug>/`` under the workspace ``root`` and bind ``spec.md``.

    ``workflow`` defaults to ``direct-delivery`` (unbound, with a ``SPEC_UNBOUND`` notice, when the project does not
    have it). A ``bugfix`` bundle gets only ``spec.md`` (``kind: bugfix``); its workflow writes the plan and tasks.
    ``namespace`` and ``summary`` are written to ``spec.md`` only when given. Raises before writing:
    ``SpecSlugError``, ``ArgumentError`` (a ``namespace`` that is neither ``global`` nor registered, a ``summary``
    that is empty or not English), ``SpecExistsError``
    (``SPEC-<slug>`` or ``PROP-<slug>`` is declared, a proposal of the slug exists, or the directory exists),
    ``SpecWorkflowError`` (an explicit workflow that does not resolve or validate); ``SpecWriteError`` when a write
    fails (what was written is removed).
    """
    root = root.resolve()
    raw = slug
    slug = clean_slug(slug.strip().removeprefix("SPEC-"))
    if not slug:
        raise SpecSlugError(f"slug {raw!r} has no letter or digit", target_files=[raw])
    namespace = require_namespace(root, namespace)
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
        kind=spec_kind(binding),
        namespace=namespace,
        summary=summary,
    )
    if spec_kind(binding) == BUGFIX_WORKFLOW:
        # bugfix writes plan.md and tasks.md in its plan-tasks stage; a skeleton tasks.md would have to match the
        # characterized spec's criteria for the characterize stage's lint-clean exit.
        files = {SPEC_FILE: files[SPEC_FILE]}
    written: list[Path] = []
    try:
        write_spec_bundle(directory, files, binding, written)
    except OSError as exc:
        roll_back(written)
        raise SpecWriteError(f"creating SPEC-{slug} failed; the files it wrote were removed", str(exc)) from exc
    rel = directory.relative_to(root).as_posix()
    created = CreatedSpec(id=f"SPEC-{slug}", dir=rel, workflow=binding.workflow if binding else None)
    if unbound is not None:
        created.notices.append(
            SpecUnboundNotice(
                f"SPEC-{slug} is not bound to a workflow: {DEFAULT_WORKFLOW} is not available ({unbound.code})",
                target_files=[f"{rel}/{SPEC_FILE}"],
                fix=f"Bind it with devkit workflow bind --unit {rel} --workflow <id> once a workflow fits it",
            )
        )
    return created
