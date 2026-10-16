"""Scaffold proposals: a bundle ``docs/proposals/PROP-<slug>/`` and the PADRs inside it.

A bundle holds ``proposal.md``, ``decisions/`` (``PADR-<slug>.md`` preliminary decisions), ``materials/`` and,
optionally, ``target-docs.md`` (the Living Spec blueprint). A proposal and a spec never share a slug, so a
handed-off ``PROP-<slug>`` maps to exactly one ``SPEC-<slug>``.

``proposal.md`` is the anchor of a devkit workflow unit: a new proposal is bound to workflow ``sdd-proposal`` when the
project has it. ``workflow`` and ``workflow_hash`` are that binding. ``task_kind`` (``feature`` or ``bugfix``) is the
provisional ``task-kind`` the proposal is confirmed with at ``plan-accept``; the spec follows ``sdd-spec-<task_kind>``
after handoff. ``supersedes`` names the accepted proposal a close by supersede replaces, and ``needs_decompose: true``
marks a draft Backlog splits before Planning starts. ``namespace`` names the document namespace (``devkit_spec.namespaces``) the bundle
belongs to; without it the bundle is global, and handoff carries it to ``spec.md``. ``summary`` is the one or two
English sentences ``RULE-document-summary`` requires of ``proposal.md``; handoff carries it to ``spec.md``, and a
PADR's ``summary`` stays in its promoted ADR.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml
from devkit.advisory import AdvisoryError
from devkit.core.errors import ArgumentError
from devkit.workflow import write_binding

from devkit_spec.branches import SLUG_LIMIT
from devkit_spec.config import GLOBAL, read_spec_config
from devkit_spec.documents import DocumentIndex
from devkit_spec.errors import (
    ProposalExistsError,
    ProposalNotFoundError,
    ProposalSlugConflictError,
    ProposalSlugError,
    ProposalUnboundNotice,
    ProposalWorkflowError,
    SpecError,
)
from devkit_spec.namespaces import detect, require
from devkit_spec.proposals.binding import DEFAULT_TASK_KIND, PROPOSAL_WORKFLOW, TASK_KINDS, resolve_binding
from devkit_spec.rules.document_summary import foreign_letters

PROPOSALS = "docs/proposals"
PROPOSAL_FILE = "proposal.md"
TARGET_DOCS = "target-docs.md"
DECISIONS = "decisions"
MATERIALS = "materials"
DEFAULT_TARGET_AREA = "capabilities/<area>/"

_UNSAFE = re.compile(r"[^a-zA-Z0-9_-]+")
_DASHES = re.compile(r"[_-]+")
_FIRST_SEGMENT_LETTER = re.compile(r"^[0-9]*[a-z]")


def clean_slug(raw: str) -> str:
    """``raw`` without a ``PROP-`` prefix or ``.md`` suffix, other characters than letters, digits, ``_`` and
    ``-`` collapsed to ``-``, outer dashes trimmed, lower-cased."""
    slug = raw.strip().removeprefix("PROP-").removesuffix(".md")
    return _UNSAFE.sub("-", slug).strip("-").lower()


def require_slug(raw: str, what: str = "slug") -> str:
    """``clean_slug(raw)``; ``ProposalSlugError`` when nothing is left."""
    slug = clean_slug(raw)
    if not slug:
        raise ProposalSlugError(f"{what} {raw!r} has no letter or digit", target_files=[raw])
    return slug


def new_slug(raw: str, what: str = "slug", error: type[SpecError] = ProposalSlugError, fix: str | None = None) -> str:
    """The slug of a new document: ``clean_slug(raw)`` with ``_`` written as ``-``.

    Raises ``error`` when nothing is left, when it is longer than ``SLUG_LIMIT`` (its activity branches
    ``plan-<slug>`` and ``dev-<slug>`` must fit devkit worktree's 64 characters), or when the first segment has no
    letter: ``RULE-id-convention`` reads ``2024-budget`` as a retired number-based ID (``fix`` replaces the default
    directive then). Lookups of existing documents use ``require_slug``.
    """
    slug = _DASHES.sub("-", clean_slug(raw)).strip("-")
    if not slug:
        raise error(f"{what} {raw!r} has no letter or digit", target_files=[raw])
    if len(slug) > SLUG_LIMIT:
        raise error(
            f"{what} {slug!r} is {len(slug)} characters; at most {SLUG_LIMIT}, so its activity branches plan-<slug>"
            " and dev-<slug> fit 64 characters",
            target_files=[raw],
            fix=f"Pass a shorter {what}",
        )
    if not first_segment_has_letter(slug):
        raise error(
            f"{what} {raw!r} gives {slug!r}, whose first segment has no letter",
            target_files=[raw],
            fix=fix or f"Pass a {what} whose first word has a letter (for example budget-2024 instead of 2024-budget)",
        )
    return slug


def first_segment_has_letter(slug: str) -> bool:
    """Whether the first ``-`` segment of ``slug`` has a letter; ``RULE-id-convention`` reads ``2024-budget`` as the
    retired number-based ID ``2024``."""
    return _FIRST_SEGMENT_LETTER.match(slug) is not None


def yaml_scalar(value: str) -> str:
    """``value`` as a YAML scalar for a frontmatter line, quoted only when YAML needs it (``A: B`` titles)."""
    dumped = yaml.safe_dump(value, allow_unicode=True, width=10**6)
    return dumped.removesuffix("\n...\n").removesuffix("\n")


def require_task_kind(value: str | None) -> str:
    """``value`` (default ``feature``) when it is one of ``TASK_KINDS``; ``ArgumentError`` (``--task-kind``) otherwise."""
    kind = (value or "").strip() or DEFAULT_TASK_KIND
    if kind in TASK_KINDS:
        return kind
    raise ArgumentError(
        f"--task-kind {value!r} is not one of {' | '.join(TASK_KINDS)}",
        target_files=["--task-kind"],
        fix=f"Pass --task-kind {' or '.join(TASK_KINDS)}",
    )


def _supersedes(value: str | None, slug: str) -> str | None:
    """The ``PROP-<slug>`` ID a new proposal supersedes, ``None`` without one; ``ArgumentError`` for anything else or
    for the proposal's own ID (a superseding draft takes a new slug)."""
    if value is None:
        return None
    old = clean_slug(value)
    if value.strip().startswith("PROP-") and old and old != slug:
        return f"PROP-{old}"
    raise ArgumentError(
        f"--supersedes {value!r} must name another proposal as PROP-<slug>",
        target_files=["--supersedes"],
        fix="Pass --supersedes PROP-<slug of the accepted proposal this draft replaces>; the new draft takes a new slug",
    )


def known_namespaces(root: Path) -> list[str]:
    """``global`` and the namespaces registered in the project at ``root`` (``SpecConfigError`` when malformed)."""
    return [GLOBAL, *(namespace.name for namespace in read_spec_config(root).namespaces)]


def bundle_namespace(root: Path, namespace: str | None, cwd: Path | None) -> tuple[str | None, str | None]:
    """The ``namespace`` field a new bundle gets (``None``: no field) and the namespace it reports.

    An explicit ``namespace`` must be ``global`` or registered in the project at ``root``. Without one, the bundle
    takes the namespace ``cwd`` lies in (``devkit_spec.namespaces.detect``), none outside every package or without
    ``cwd``. The reported namespace is the field, else ``global`` in a project that registers namespaces, else
    ``None``. Raises ``ArgumentError`` (``--namespace``) for an unregistered name, and ``SpecConfigError`` for a
    malformed ``[tool.spec]`` table unless the name is ``global``.
    """
    if namespace == GLOBAL:
        return GLOBAL, GLOBAL
    namespaces = read_spec_config(root).namespaces
    if namespace is not None:
        written: str | None = require(namespaces, namespace)
    else:
        written = detect(namespaces, root, cwd) if cwd is not None else None
    return written, written or (GLOBAL if namespaces else None)


def require_summary(summary: str | None) -> str | None:
    """``summary`` stripped when it is non-empty English text (``RULE-document-summary``'s check); ``None`` when
    omitted. Raises ``ArgumentError`` (``--summary``) for an empty summary or one with a letter outside the Latin
    script."""
    if summary is None:
        return None
    text = summary.strip()
    letters = foreign_letters(text)
    if text and not letters:
        return text
    problem = f"contains {''.join(letters[:5])}, not English" if letters else "is empty"
    raise ArgumentError(
        f"--summary {problem}",
        target_files=["--summary"],
        fix="Pass --summary with one or two English sentences saying what the document defines",
    )


def bundle_dir(root: Path, slug: str) -> Path:
    return root / PROPOSALS / f"PROP-{slug}"


def single_file(root: Path, slug: str) -> Path:
    return root / PROPOSALS / f"PROP-{slug}.md"


def check_spec_conflict(index: DocumentIndex, slug: str) -> None:
    """Raise ``ProposalSlugConflictError`` when a document declares ``SPEC-<slug>``.

    A broken document is a problem of the index, not a conflict, so it never blocks a proposal.
    """
    spec_id = f"SPEC-{slug}"
    found = index.by_id.get(spec_id, [])
    if found:
        path = found[0].path
        raise ProposalSlugConflictError(
            f"{spec_id} already exists at {path}; a proposal and a spec cannot share a slug", target_files=[path]
        )


@dataclass
class CreatedProposal:
    """A scaffolded bundle: its ``id``, directory and ``proposal.md`` (workspace-relative), ``target-docs.md``
    when it was requested, and the ``workflow`` ``proposal.md`` is bound to (``None``: unbound)."""

    id: str
    dir: str
    path: str
    target_docs: str | None
    workflow: str | None = None
    namespace: str | None = None
    notices: list[AdvisoryError] = field(default_factory=list)

    @property
    def next_command(self) -> str | None:
        return f"devkit workflow next --unit {self.dir}" if self.workflow else None

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "dir": self.dir,
            "path": self.path,
            "target_docs": self.target_docs,
            "workflow": self.workflow,
            "namespace": self.namespace,
            "next_command": self.next_command,
            "notices": [notice.to_dict() for notice in self.notices],
        }


def create_proposal(
    root: Path,
    slug: str,
    *,
    title: str | None = None,
    target_area: str | None = None,
    milestone: str | None = None,
    task_kind: str | None = None,
    namespace: str | None = None,
    summary: str | None = None,
    supersedes: str | None = None,
    needs_decompose: bool = False,
    with_target_docs: bool = False,
    today: date | None = None,
    cwd: Path | None = None,
) -> CreatedProposal:
    """Scaffold ``docs/proposals/PROP-<slug>/`` under the workspace ``root`` and bind ``proposal.md``.

    ``task_kind`` is always written (default ``feature``); ``summary`` only when given (without it, a commented
    placeholder line); ``supersedes`` (a ``PROP-<slug>`` ID) and ``needs_decompose`` only when given; ``namespace``
    when given, else the namespace ``cwd`` lies in (``bundle_namespace``, reported on the result). Handoff resolves
    ``sdd-spec-<task_kind>`` and carries the namespace and summary. ``proposal.md`` is bound to ``sdd-proposal`` when it
    resolves and validates, else left unbound with a ``SPEC_PROPOSAL_UNBOUND`` notice. Raises ``ProposalSlugError``
    for a slug without letters or digits, ``ArgumentError`` for a ``task_kind`` outside ``TASK_KINDS``, a
    ``supersedes`` that is not a proposal ID, a ``namespace`` that is neither ``global`` nor registered or a
    ``summary`` that is empty or not English, ``ProposalExistsError`` when the
    bundle or a single-file proposal of the slug exists, ``ProposalSlugConflictError`` when ``SPEC-<slug>`` exists.
    """
    root = root.resolve()
    slug = new_slug(slug)
    namespace, reported = bundle_namespace(root, namespace, cwd)
    summary = require_summary(summary)
    kind = require_task_kind(task_kind)
    replaced = _supersedes(supersedes, slug)
    title = (title or "").strip() or slug
    area = (target_area or "").strip() or DEFAULT_TARGET_AREA
    area = area if area.endswith("/") else area + "/"
    bundle = bundle_dir(root, slug)
    for existing in (bundle, single_file(root, slug)):
        if existing.exists():
            rel = existing.relative_to(root).as_posix()
            raise ProposalExistsError(f"proposal PROP-{slug} already exists: {rel}", target_files=[rel])
    check_spec_conflict(DocumentIndex.load(root), slug)
    binding, unbound = resolve_binding(
        root, None, PROPOSAL_FILE, default=PROPOSAL_WORKFLOW, error=ProposalWorkflowError
    )

    created = (today or date.today()).isoformat()
    (bundle / DECISIONS).mkdir(parents=True)
    (bundle / MATERIALS).mkdir()
    proposal = bundle / PROPOSAL_FILE
    text = _proposal(
        slug,
        title,
        area,
        (milestone or "").strip(),
        kind,
        namespace or "",
        summary or "",
        created,
        supersedes=replaced,
        needs_decompose=needs_decompose,
    )
    proposal.write_text(text, encoding="utf-8")
    if binding is not None:
        write_binding(proposal, binding)
    target_docs = None
    if with_target_docs:
        target_docs = bundle / TARGET_DOCS
        target_docs.write_text(_target_docs(slug, title, created), encoding="utf-8")
    result = CreatedProposal(
        id=f"PROP-{slug}",
        dir=bundle.relative_to(root).as_posix(),
        path=proposal.relative_to(root).as_posix(),
        target_docs=target_docs.relative_to(root).as_posix() if target_docs else None,
        workflow=binding.workflow if binding else None,
        namespace=reported,
    )
    if unbound is not None:
        result.notices.append(
            ProposalUnboundNotice(
                f"PROP-{slug} is not bound to a workflow: {PROPOSAL_WORKFLOW} is not available ({unbound.code})",
                target_files=[result.path],
                fix=f"Bind it with devkit workflow bind --unit {result.dir} --workflow <id> once a workflow fits it",
            )
        )
    return result


def _proposal(
    slug: str,
    title: str,
    area: str,
    milestone: str,
    task_kind: str,
    namespace: str,
    summary: str,
    created: str,
    *,
    supersedes: str | None = None,
    needs_decompose: bool = False,
) -> str:
    summary_line = (
        f"summary: {yaml_scalar(summary)}"
        if summary
        else "# summary: <one or two English sentences: what this proposal changes and why>"
    )
    namespace_line = f"namespace: {yaml_scalar(namespace)}\n" if namespace else ""
    milestone_line = f"milestone: {yaml_scalar(milestone)}\n" if milestone else ""
    task_kind_line = f"task_kind: {task_kind:<26} # feature | bugfix: the spec follows sdd-spec-<task_kind>"
    supersedes_line = f"supersedes: {supersedes}\n" if supersedes else ""
    decompose_line = (
        "needs_decompose: true                 # split in Backlog before Planning starts\n" if needs_decompose else ""
    )
    return f"""---
id: PROP-{slug}
title: {yaml_scalar(title)}
{summary_line}
status: draft                         # draft | reviewing | accepted | rejected
created_at: {created}
target_area: {yaml_scalar(area)}
{namespace_line}priority: high                        # critical | high | medium | low
size: M                               # S | M | L | XL
{milestone_line}boundaries:
  owns:
    - {yaml_scalar(area)}
  excludes:
    - docs/decisions/
{task_kind_line}
{supersedes_line}{decompose_line}---

# [PROP-{slug}] {title}

## 1. Background & Hypothesis
<!-- Describe background, current challenges, and core hypothesis to address -->

## 2. Technical Spike Questions
<!-- Define key uncertainties and technical questions to answer -->
- **Q1**:
- **Q2**:

## 3. Proposed Design & Impact
<!-- Describe expected architectural design, CLI commands, and structural impact -->

## 4. Lifecycle & Retirement Criteria
<!--
- Preliminary decisions: devkit spec proposal padr {slug} "<title>" --summary "<what it decides>" records a PADR in decisions/.
- Research: collect benchmarks and references in materials/.
- On acceptance (plan-accept): record gate:plan-accept, set status: accepted and merge the Planning branch; Development
  starts with devkit spec proposal handoff {slug}.
- On rejection: change only status: rejected, with the user's reason in the commit message; a later hygiene pass
  writes the rejection ADR and deletes the proposal directory.
-->
"""


def _target_docs(slug: str, title: str, created: str) -> str:
    return f"""---
id: PROP-{slug}-target
title: Target Living Spec Structure for PROP-{slug}
status: draft
proposal: PROP-{slug}
created_at: {created}
# The Living Spec files this proposal changes, one "- file: <workspace-relative path>" each;
# devkit spec scope compare reads them to find overlaps with other work.
targets: []
---

# [Blueprint] PROP-{slug}: Target Living Spec Structure for {title}

This document defines the target blueprint of how the docs/ backbone (Living Spec) will evolve if proposal PROP-{slug} is accepted. It represents a hypothesis plan subject to adjustment during implementation. Upon handoff, it is copied into specs/ to serve as a baseline for plan.md boundaries and reconcile.md targets.

---

## 1. System Capabilities Plan (docs/capabilities/)

<Specify new, modified, or deprecated CAP documents, rationale, and key changes.>

---

## 2. User Stories Plan (docs/stories/)

<Specify new or modified US documents and updated acceptance criteria.>

---

## 3. Architecture & Decision Impact (docs/architecture/ & docs/decisions/)

<Specify impacted ARCH documents and candidate ADRs (PADRs).>

---

## 4. Development Conventions & Governance (docs/development/ & .devkit/)

<Specify new rules, workflows, skills, or CLI changes.>

---

## 5. System Before & After Comparison (Before & After)

<Compare As-Is and To-Be structures, optionally with Mermaid diagrams.>
"""


@dataclass(frozen=True)
class CreatedDecision:
    """A scaffolded PADR: its ``id``, path (workspace-relative) and the ``proposal`` it belongs to."""

    id: str
    path: str
    proposal: str

    def to_dict(self) -> dict[str, object]:
        return {"id": self.id, "path": self.path, "proposal": self.proposal}


def create_padr(
    root: Path,
    slug: str,
    title: str,
    *,
    summary: str | None = None,
    padr_slug: str | None = None,
    today: date | None = None,
) -> CreatedDecision:
    """Scaffold ``decisions/PADR-<padr slug>.md`` in the bundle of proposal ``slug``.

    The PADR slug is ``padr_slug`` when given (a leading ``PADR-`` dropped), else the title's (``new_slug``); the
    title stays free text, so ``"2024 roadmap"`` works with ``padr_slug="roadmap-2024"``. ``summary`` is written only
    when given; the promoted ADR keeps it. Raises ``ProposalSlugError`` for a slug without letters or digits or a
    PADR slug whose first segment has no letter, ``ArgumentError`` for a ``summary`` that is empty or not English,
    ``ProposalNotFoundError`` when the bundle does not exist, ``ProposalExistsError`` when any document already
    declares the PADR ID.
    """
    root = root.resolve()
    slug = require_slug(slug)
    summary = require_summary(summary)
    title = title.strip()
    if padr_slug is not None:
        padr_id = f"PADR-{new_slug(padr_slug.strip().removeprefix('PADR-'), '--slug')}"
    else:
        padr_id = "PADR-" + new_slug(
            title,
            "title",
            fix="Pass --slug with a slug whose first word has a letter (for example --slug roadmap-2024), keeping the"
            " title as it is",
        )
    bundle = bundle_dir(root, slug)
    if not bundle.is_dir():
        rel = bundle.relative_to(root).as_posix()
        raise ProposalNotFoundError(
            f"proposal bundle {rel} does not exist",
            target_files=[rel],
            fix=f"Create the bundle first with devkit spec proposal new {slug}",
        )
    path = bundle / DECISIONS / f"{padr_id}.md"
    existing = [document.path for document in DocumentIndex.load(root).by_id.get(padr_id, [])]
    if path.exists() and path.relative_to(root).as_posix() not in existing:
        existing.append(path.relative_to(root).as_posix())
    if existing:
        raise ProposalExistsError(f"PADR ID {padr_id} already exists: {', '.join(existing)}", target_files=existing)
    created = (today or date.today()).isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_padr(padr_id, title, summary, slug, created), encoding="utf-8")
    return CreatedDecision(id=padr_id, path=path.relative_to(root).as_posix(), proposal=f"PROP-{slug}")


def _padr(padr_id: str, title: str, summary: str | None, slug: str, created: str) -> str:
    summary_line = (
        f"summary: {yaml_scalar(summary)}\n"
        if summary
        else "# summary: <one or two English sentences: what is decided and why>\n"
    )
    return f"""---
id: {padr_id}
title: {yaml_scalar(title)}
{summary_line}proposal: PROP-{slug}
status: draft
created_at: {created}
---

# [{padr_id}] {title}

- **Status**: Draft
- **Date**: {created}

---

## 1. Context & Problem Statement

## 2. Decision Drivers

## 3. Considered Options

## 4. Decision Outcome

## 5. Consequences
"""
