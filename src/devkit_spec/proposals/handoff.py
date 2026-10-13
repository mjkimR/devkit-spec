"""Hand an approved proposal off to a spec bundle and retire the proposal.

``handoff_proposal`` validates everything before it writes (slug, approval, slug conflict, workflow binding, every
path it would create), then:

1. writes ``specs/<YYYY-MM>/<YYYYMMDD>-<slug>/`` with ``spec.md``, ``plan.md`` and ``tasks.md`` carried from the
   proposal body, each marked as a skeleton, and binds ``spec.md`` to the proposal's ``handoff_workflow``
   (default ``direct-delivery``; ``kind: bugfix`` for ``bugfix``). A spec bound to ``bugfix`` gets ``spec.md`` only, with the proposal's target area and
   boundaries in its carried notes;
2. copies ``target-docs.md`` into the spec bundle;
3. promotes each ``decisions/PADR-<slug>.md`` to ``docs/decisions/<YYYY-MM>/<YYYYMMDD>-<slug>.md`` as an accepted
   ``ADR-<slug>``;
4. moves a non-empty ``materials/`` to ``docs/materials/<YYYY-MM>/<YYYYMMDD>-<slug>/``;
5. rewrites links and ID references that pointed into the proposal (``rewrite``);
6. removes the proposal.

A failure in steps 1 to 4 removes what they wrote and keeps the proposal. A single-file proposal
``docs/proposals/PROP-<slug>.md`` gets the plain skeleton (its body is not carried) and has no PADRs, materials or
blueprint.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from devkit.advisory import AdvisoryError
from devkit.core import FrontmatterError
from devkit.core.frontmatter import parse
from devkit.workflow import Binding

from devkit_spec.documents import DocumentIndex, parse_document
from devkit_spec.errors import (
    ProposalCleanupWarning,
    ProposalHandoffError,
    ProposalInvalidError,
    ProposalLinkUnresolvedWarning,
    ProposalNotApprovedError,
    ProposalNotFoundError,
    ProposalReferencesRewrittenNotice,
    ProposalTargetExistsError,
    ProposalUnboundNotice,
)
from devkit_spec.proposals.binding import BUGFIX_WORKFLOW, DEFAULT_WORKFLOW, resolve_binding
from devkit_spec.proposals.body import CarriedProposal, carry_proposal_body
from devkit_spec.proposals.rewrite import (
    ID,
    RelocationPlan,
    RewriteReport,
    Rewritten,
    Unresolved,
    completed_bundles,
    markdown_files,
    rewrite_ids,
    rewrite_links,
)
from devkit_spec.proposals.scaffold import (
    DECISIONS,
    MATERIALS,
    PROPOSAL_FILE,
    TARGET_DOCS,
    bundle_dir,
    check_spec_conflict,
    clean_slug,
    require_slug,
    single_file,
)
from devkit_spec.proposals.specs import (
    SPEC_FILE,
    make_dirs,
    roll_back,
    spec_dir,
    spec_files,
    spec_kind,
    text_value,
    text_values,
    write_spec_bundle,
)

HANDOFF_WORKFLOW = "handoff_workflow"
"""The proposal frontmatter key naming the workflow its spec follows (``workflow`` is devkit's own binding)."""
ACCEPTED = "accepted"
DIRECTION_STATUSES = ("draft", "reviewing")

_PADR = re.compile(r"\bPADR-([a-z0-9]+(?:-[a-z0-9]+)*)")
_DRAFT_STATUS = re.compile(r"^status:[ \t]*(?:draft|proposed)[ \t]*$", re.MULTILINE)
_DRAFT_BODY_STATUS = re.compile(r"^- \*\*Status\*\*:[ \t]*(?:Draft|Proposed)[ \t]*$", re.MULTILINE)


@dataclass(frozen=True)
class PromotedDecision:
    """A PADR promoted to an ADR: the ADR's ``id`` and path (workspace-relative), and the PADR's ``padr`` ID."""

    id: str
    path: str
    padr: str

    def to_dict(self) -> dict[str, object]:
        return {"id": self.id, "path": self.path, "padr": self.padr}


@dataclass
class HandoffResult:
    """What a handoff wrote, moved and rewrote; paths are workspace-relative.

    ``workflow`` is the workflow ``spec.md`` is bound to (``None``: unbound), ``rewritten_files`` the files whose
    links or references changed, ``unresolved`` what pointed into the proposal and could not be mapped.
    ``notices`` are the warnings and notices the caller reports with the result.
    """

    proposal: str
    spec: str
    dir: str
    workflow: str | None
    target_docs: str | None = None
    materials: str | None = None
    decisions: list[PromotedDecision] = field(default_factory=list)
    rewritten_files: list[str] = field(default_factory=list)
    rewritten: list[Rewritten] = field(default_factory=list)
    unresolved: list[Unresolved] = field(default_factory=list)
    notices: list[AdvisoryError] = field(default_factory=list)

    @property
    def next_command(self) -> str | None:
        return f"devkit workflow next --unit {self.dir}" if self.workflow else None

    def to_dict(self) -> dict[str, object]:
        return {
            "proposal": self.proposal,
            "spec": self.spec,
            "dir": self.dir,
            "workflow": self.workflow,
            "target_docs": self.target_docs,
            "materials": self.materials,
            "decisions": [decision.to_dict() for decision in self.decisions],
            "rewritten_files": self.rewritten_files,
            "rewritten": [item.to_dict() for item in self.rewritten],
            "unresolved": [item.to_dict() for item in self.unresolved],
            "next_command": self.next_command,
            "notices": [notice.to_dict() for notice in self.notices],
        }


@dataclass(frozen=True)
class _Decision:
    padr: Path
    padr_id: str
    target: Path
    adr_id: str
    text: str


def _read(path: Path, root: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        rel = path.relative_to(root).as_posix()
        raise ProposalInvalidError(f"{rel} cannot be read: {exc}", target_files=[rel]) from exc


def handoff_proposal(
    root: Path, slug: str, *, direction_chosen: bool = False, today: date | None = None
) -> HandoffResult:
    """Hand proposal ``slug`` off to a spec bundle under the workspace ``root`` (see the module docstring).

    Approval is ``status: accepted``, or ``draft``/``reviewing`` with ``direction_chosen`` (the user chose the
    direction explicitly); it is never inferred. Raises, before writing anything: ``ProposalSlugError``,
    ``ProposalNotFoundError``, ``ProposalInvalidError``, ``ProposalNotApprovedError``,
    ``ProposalSlugConflictError``, ``ProposalWorkflowError``, ``ProposalTargetExistsError``; and
    ``ProposalHandoffError`` when a write fails (what was written is removed).
    """
    root = root.resolve()
    slug = require_slug(slug)
    day = today or date.today()
    bundle, single = bundle_dir(root, slug), single_file(root, slug)
    is_bundle = bundle.is_dir()
    if not is_bundle and not single.is_file():
        raise ProposalNotFoundError(f"proposal PROP-{slug} not found", target_files=[f"PROP-{slug}"])
    proposal_path = bundle / PROPOSAL_FILE if is_bundle else single
    proposal_rel = proposal_path.relative_to(root).as_posix()
    text = _read(proposal_path, root)
    try:
        meta: dict[str, Any] = parse(text).data or {}
    except FrontmatterError as exc:
        raise ProposalInvalidError(f"{proposal_rel}: {exc.message}", target_files=[proposal_rel]) from exc

    status = text_value(meta.get("status")).lower()
    if not (status == ACCEPTED or (direction_chosen and status in DIRECTION_STATUSES)):
        needed = (
            "accepted, draft or reviewing"
            if direction_chosen
            else "accepted (draft or reviewing with --direction-chosen)"
        )
        raise ProposalNotApprovedError(
            f"proposal PROP-{slug} has status {status or '-'}; handoff needs {needed}", target_files=[proposal_rel]
        )
    index = DocumentIndex.load(root)
    check_spec_conflict(index, slug)
    binding, unbound = resolve_binding(root, meta.get(HANDOFF_WORKFLOW), proposal_rel, field=HANDOFF_WORKFLOW)

    month, stamp = day.strftime("%Y-%m"), day.strftime("%Y%m%d")
    target_dir = spec_dir(root, slug, day)
    targets: list[Path] = [target_dir]
    materials_dir = bundle / MATERIALS
    materials_target: Path | None = None
    target_docs_text: str | None = None
    decisions: list[_Decision] = []
    if is_bundle:
        if materials_dir.is_dir() and any(materials_dir.iterdir()):
            materials_target = root / "docs" / MATERIALS / month / f"{stamp}-{slug}"
            targets.append(materials_target)
        if (bundle / TARGET_DOCS).is_file():
            target_docs_text = _read(bundle / TARGET_DOCS, root)
        decisions = _plan_decisions(root, bundle / DECISIONS, month, stamp)
        targets += [decision.target for decision in decisions]
    _check_targets(root, index, targets, decisions)

    title = text_value(meta.get("title")) or slug
    materials_ref = (
        f"\n- **Preserved Materials**: `{materials_target.relative_to(root).as_posix()}`" if materials_target else ""
    )
    target_docs_ref = (
        f"\n- Target Docs Blueprint: {_target_docs_reference(target_docs_text)} "
        "(Living Spec targets for this plan and reconcile.md)"
        if target_docs_text is not None
        else ""
    )
    carried = carry_proposal_body(text) if is_bundle else CarriedProposal()
    bugfix = spec_kind(binding) == BUGFIX_WORKFLOW
    if bugfix:
        # No plan.md: what it would hold from the proposal is carried in spec.md's notes.
        carried.notes += _scope_notes(meta)
    created = day.isoformat()
    files = spec_files(
        slug,
        title,
        created,
        origin=f"Handed off from proposal PROP-{slug} on {created}.{materials_ref}{target_docs_ref}\n",
        carried=carried,
        meta=meta,
        kind=spec_kind(binding),
        target_docs_ref=target_docs_ref,
    )
    if bugfix:
        # bugfix writes plan.md and tasks.md in its plan-tasks stage; skeletons would have to match the
        # characterized criteria for the characterize stage's lint-clean exit.
        files = {SPEC_FILE: files[SPEC_FILE]}

    written: list[Path] = []
    moved: tuple[Path, Path] | None = None
    promoted: dict[str, str] = {}
    try:
        write_spec_bundle(target_dir, files, binding, written)
        if target_docs_text is not None:
            (target_dir / TARGET_DOCS).write_text(target_docs_text, encoding="utf-8")
        for decision in decisions:
            make_dirs(decision.target.parent, written)
            written.append(decision.target)
            decision.target.write_text(decision.text, encoding="utf-8")
            promoted[str(decision.padr)] = str(decision.target)
        if materials_target is not None:
            make_dirs(materials_target.parent, written)
            shutil.move(materials_dir, materials_target)
            moved = (materials_target, materials_dir)
    except OSError as exc:
        roll_back(written, moved)
        raise ProposalHandoffError(
            f"handoff of PROP-{slug} failed; the files it wrote were removed and the proposal is kept", str(exc)
        ) from exc

    plan = RelocationPlan(proposal=str(bundle if is_bundle else single))
    if is_bundle:
        plan.dir_target = str(target_dir)
        # Carried proposal text and the copied blueprint were written for the bundle directory.
        plan.moved[str(target_dir)] = str(bundle)
        plan.exact[str(bundle / PROPOSAL_FILE)] = str(target_dir / SPEC_FILE)
        if target_docs_text is not None:
            plan.exact[str(bundle / TARGET_DOCS)] = str(target_dir / TARGET_DOCS)
        plan.exact.update(promoted)
        if materials_target is not None:
            plan.prefixes[str(materials_dir)] = str(materials_target)
            plan.moved[str(materials_target)] = str(materials_dir)
    else:
        plan.exact[str(single)] = str(target_dir / SPEC_FILE)
    index = DocumentIndex.load(root)
    sources = markdown_files(root, plan, completed_bundles(index))
    report = RewriteReport()
    rewrite_links(root, sources, plan, report)
    rewrite_ids(root, sources, plan, index, report)

    notices: list[AdvisoryError] = []
    try:
        if is_bundle:
            shutil.rmtree(bundle)
        else:
            single.unlink()
    except OSError as exc:
        removed = plan.proposal
        rel = Path(removed).relative_to(root).as_posix()
        notices.append(ProposalCleanupWarning(f"{rel} could not be removed: {exc}", target_files=[rel]))
    return _result(
        root, slug, target_dir, binding, unbound, target_docs_text, materials_target, decisions, report, notices
    )


def _scope_notes(meta: dict[str, Any]) -> str:
    """The proposal's target area and boundaries as a carried-notes section, ``""`` when it declares none."""
    boundaries = meta.get("boundaries")
    boundaries = boundaries if isinstance(boundaries, dict) else {}
    lines = []
    if area := text_value(meta.get("target_area")):
        lines.append(f"- Target Area: {area}")
    for label, key in (("Planned Boundaries", "owns"), ("Excluded Boundaries", "excludes")):
        if items := text_values(boundaries.get(key)):
            lines.append(f"- {label}: " + ", ".join(f"`{item}`" for item in items))
    return "### Target Area & Boundaries\n\n" + "\n".join(lines) + "\n\n" if lines else ""


def _plan_decisions(root: Path, decisions_dir: Path, month: str, stamp: str) -> list[_Decision]:
    """The ADRs the bundle's ``PADR-*.md`` files become, with their promoted text."""
    if not decisions_dir.is_dir():
        return []
    planned = []
    for padr in sorted(p for p in decisions_dir.iterdir() if p.is_file() and p.name.startswith("PADR-")):
        if not padr.name.endswith(".md"):
            continue
        adr_slug = clean_slug(padr.name.removeprefix("PADR-").removesuffix(".md"))
        if not adr_slug:
            continue
        original = _read(padr, root)
        promoted = _PADR.sub(r"ADR-\1", original)
        promoted = _DRAFT_STATUS.sub("status: accepted", promoted)
        promoted = _DRAFT_BODY_STATUS.sub("- **Status**: Accepted", promoted)
        rel = padr.relative_to(root).as_posix()
        try:
            old, new = parse_document(rel, original), parse_document(rel, promoted)
        except FrontmatterError as exc:
            raise ProposalInvalidError(f"{rel}: {exc.message}", target_files=[rel]) from exc
        target = root / "docs" / DECISIONS / month / f"{stamp}-{adr_slug}.md"
        planned.append(
            _Decision(
                padr=padr,
                padr_id=old.id if old else f"PADR-{adr_slug}",
                target=target,
                adr_id=new.id if new else f"ADR-{adr_slug}",
                text=promoted,
            )
        )
    return planned


def _check_targets(root: Path, index: DocumentIndex, targets: list[Path], decisions: list[_Decision]) -> None:
    """Refuse a handoff that would overwrite a path, write one path twice, or declare an ADR ID twice."""
    clashes = [path for path in targets if path.exists() or path.is_symlink()]
    clashes += [path for position, path in enumerate(targets) if path in targets[:position]]
    for decision in decisions:
        clashes += [root / document.path for document in index.by_id.get(decision.adr_id, [])]
    if clashes:
        rels = list(dict.fromkeys(path.relative_to(root).as_posix() for path in clashes))
        raise ProposalTargetExistsError(f"the handoff would overwrite {', '.join(rels)}", target_files=rels)


def _target_docs_reference(text: str) -> str:
    try:
        document = parse_document(TARGET_DOCS, text)
    except FrontmatterError:
        document = None
    return f"`{document.id}`" if document else f"[{TARGET_DOCS}]({TARGET_DOCS})"


def _result(
    root: Path,
    slug: str,
    target_dir: Path,
    binding: Binding | None,
    unbound: AdvisoryError | None,
    target_docs_text: str | None,
    materials_target: Path | None,
    decisions: list[_Decision],
    report: RewriteReport,
    notices: list[AdvisoryError],
) -> HandoffResult:
    def rel(path: Path) -> str:
        return path.relative_to(root).as_posix()

    spec_rel = rel(target_dir)
    result = HandoffResult(
        proposal=f"PROP-{slug}",
        spec=f"SPEC-{slug}",
        dir=spec_rel,
        workflow=binding.workflow if binding else None,
        target_docs=f"{spec_rel}/{TARGET_DOCS}" if target_docs_text is not None else None,
        materials=rel(materials_target) if materials_target else None,
        decisions=[PromotedDecision(d.adr_id, rel(d.target), d.padr_id) for d in decisions],
        rewritten_files=sorted(set(report.files)),
        rewritten=sorted(report.rewritten, key=lambda r: (r.path, r.line, r.kind)),
        unresolved=sorted(report.unresolved, key=lambda u: (u.path, u.line, u.kind)),
    )
    if unbound is not None:
        notices.append(
            ProposalUnboundNotice(
                f"SPEC-{slug} is not bound to a workflow: {DEFAULT_WORKFLOW} is not available ({unbound.code})",
                target_files=[f"{spec_rel}/{SPEC_FILE}"],
                fix=f"Bind it with devkit workflow bind --unit {spec_rel} --workflow <id> once a workflow fits it",
            )
        )
    if result.unresolved:
        files = list(dict.fromkeys(item.path for item in result.unresolved))
        notices.append(
            ProposalLinkUnresolvedWarning(
                f"{len(result.unresolved)} link(s) or reference(s) into PROP-{slug} have no new target",
                target_files=files,
            )
        )
    id_rewrites = [item for item in result.rewritten if item.kind == ID]
    if id_rewrites:
        notices.append(
            ProposalReferencesRewrittenNotice(
                f"{len(id_rewrites)} ID reference(s) to PROP-{slug} or its PADRs now name the spec or the ADRs",
                target_files=list(dict.fromkeys(item.path for item in id_rewrites)),
            )
        )
    result.notices = notices
    return result
