"""Hand an approved proposal off to a spec bundle and retire the proposal.

``handoff_proposal`` validates everything before it writes (slug, approval, slug conflict, workflow binding, every
path it would create), then:

1. writes ``specs/<YYYY-MM>/<YYYYMMDD>-<slug>/`` with ``spec.md``, ``plan.md`` and ``tasks.md`` carried from the
   proposal body, each marked as a skeleton (``spec.md`` keeps the proposal's ``namespace``, which must be
   ``global`` or registered, and its ``summary``, which must be a string), and binds ``spec.md`` to
   ``sdd-spec-<task_kind>`` (the proposal's ``task_kind``, default ``feature``). A spec bound to ``sdd-spec-bugfix``
   gets ``spec.md`` only, with the proposal's target area and boundaries in its carried notes;
2. copies ``target-docs.md`` into the spec bundle;
3. promotes each ``decisions/PADR-<slug>.md`` to ``docs/decisions/<YYYY-MM>/<YYYYMMDD>-<slug>.md`` as an accepted
   ``ADR-<slug>`` (its frontmatter, ``summary`` included, is kept);
4. moves ``materials/`` to ``docs/materials/<YYYY-MM>/<YYYYMMDD>-<slug>/`` when it holds a file other than
   operating-system junk (``JUNK_FILES``), together with every other file of the bundle that steps 1 to 3 do not
   carry (``notes.md``, a non-PADR file in ``decisions/``; junk aside), at its path relative to the bundle. Symbolic
   links are moved as links, never followed. The proposal unit's devkit workflow records (decision records and
   envelopes, as devkit's loaders find them) are not carried: they are dropped with the proposal;
5. rewrites links and ID references that pointed into the proposal (``rewrite``);
6. removes the proposal;
7. carries the proposal's ``gate:plan-intent`` and ``gate:plan-accept`` records to the spec under the same names
   (``_proposal_gates``, ``_record_gates``): a carried approval is never turned into the approval of another decision.

A legacy proposal or PADR whose slug starts with a number (``PROP-2024-budget``) is refused: the ID it would become
breaks ``RULE-id-convention``. A failure of any kind in steps 1 to 4 removes what they wrote, moves what they moved
back and keeps the proposal; a directory still holding something that could not be moved back is kept and reported.
Across file systems step 4 copies and removes the sources only after every write succeeded. A single-file proposal
``docs/proposals/PROP-<slug>.md`` gets the plain skeleton (its body is not carried) and has no PADRs, materials or
blueprint.
"""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from devkit.advisory import AdvisoryError
from devkit.core import FrontmatterError, GitError, run_git
from devkit.core.frontmatter import parse
from devkit.workflow import (
    Binding,
    Decision,
    Workspace,
    load_decisions,
    load_envelopes,
    new_decision,
    record_answer,
    write_decision,
)

from devkit_spec.config import GLOBAL
from devkit_spec.documents import DocumentIndex, parse_document
from devkit_spec.errors import (
    ProposalCleanupWarning,
    ProposalGateNotCarriedWarning,
    ProposalHandoffError,
    ProposalInvalidError,
    ProposalLinkUnresolvedWarning,
    ProposalNeedsDecomposeError,
    ProposalNotApprovedError,
    ProposalNotFoundError,
    ProposalReferencesRewrittenNotice,
    ProposalSlugError,
    ProposalTargetExistsError,
    ProposalUnboundNotice,
    ProposalWrongWorktreeError,
)
from devkit_spec.proposals.binding import (
    DEFAULT_TASK_KIND,
    DEFAULT_WORKFLOW,
    TASK_KINDS,
    resolve_binding,
    spec_workflow,
)
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
    first_segment_has_letter,
    known_namespaces,
    require_slug,
    single_file,
)
from devkit_spec.proposals.specs import (
    SPEC_FILE,
    make_dirs,
    move_path,
    remove_paths,
    roll_back,
    spec_dir,
    spec_files,
    spec_only,
    text_value,
    text_values,
    write_spec_bundle,
)

TASK_KIND = "task_kind"
"""The proposal frontmatter key holding its ``task-kind``; the spec follows ``sdd-spec-<task_kind>`` after handoff
(``workflow`` is devkit's own binding of the proposal)."""
NEEDS_DECOMPOSE = "needs_decompose"
NAMESPACE = "namespace"
SUMMARY = "summary"
ACCEPTED = "accepted"
INTENT_GATE = "gate:plan-intent"
ACCEPT_GATE = "gate:plan-accept"
# The proposal's approvals the spec carries by name, in this order (handoff never re-labels them).
CARRIED_GATES = (INTENT_GATE, ACCEPT_GATE)
RETURN_PREFIX = "return:"
DEVELOPMENT_PREFIX = "dev-"  # the handoff is the first step of Development, on its activity branch dev-<slug>

# Files an operating system leaves behind; never carried, they are deleted with the proposal.
JUNK_FILES = frozenset({".DS_Store", "Thumbs.db", "desktop.ini"})

_PADR = re.compile(r"\bPADR-[a-z0-9]+(?:-[a-z0-9]+)*")
# A frontmatter ``status: draft`` (or ``proposed``, plain or quoted); a trailing comment ("#" after whitespace) stays.
_DRAFT_STATUS = re.compile(
    r"""^status:[ \t]*(?:draft|proposed|"(?:draft|proposed)"|'(?:draft|proposed)')(?=[ \t]*\r?$|[ \t]+#)""",
    re.MULTILINE,
)
_DRAFT_BODY_STATUS = re.compile(r"^- \*\*Status\*\*:[ \t]*(?:Draft|Proposed)[ \t]*$", re.MULTILINE)


@dataclass(frozen=True)
class PromotedDecision:
    """A PADR promoted to an ADR: the ADR's ``id`` and path (workspace-relative), and the PADR's ``padr`` ID."""

    id: str
    path: str
    padr: str

    def to_dict(self) -> dict[str, object]:
        return {"id": self.id, "path": self.path, "padr": self.padr}


@dataclass(frozen=True)
class CarriedGate:
    """A gate of the spec the handoff recorded from the proposal: the ``request`` and its ``decision`` record's path
    (workspace-relative)."""

    request: str
    decision: str

    def to_dict(self) -> dict[str, object]:
        return {"request": self.request, "decision": self.decision}


@dataclass
class HandoffResult:
    """What a handoff wrote, moved and rewrote; paths are workspace-relative.

    ``workflow`` is the workflow ``spec.md`` is bound to (``None``: unbound), ``rewritten_files`` the files whose
    links or references changed, ``unresolved`` what pointed into the proposal and could not be mapped.
    ``dropped_records`` are the proposal unit's workflow records removed with it, ``carried_gates`` the proposal's own
    approvals recorded in the spec under their names. ``notices`` are the warnings and notices the caller reports
    with the result.
    """

    proposal: str
    spec: str
    dir: str
    workflow: str | None
    target_docs: str | None = None
    materials: str | None = None
    decisions: list[PromotedDecision] = field(default_factory=list)
    dropped_records: list[str] = field(default_factory=list)
    carried_gates: list[CarriedGate] = field(default_factory=list)
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
            "dropped_records": self.dropped_records,
            "carried_gates": [gate.to_dict() for gate in self.carried_gates],
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


def handoff_proposal(root: Path, slug: str, *, today: date | None = None) -> HandoffResult:
    """Hand proposal ``slug`` off to a spec bundle under the workspace ``root`` (see the module docstring).

    Approval is ``status: accepted``, written once ``plan-accept`` was given; it is never inferred. The spec carries
    the proposal's own ``gate:plan-intent`` and ``gate:plan-accept`` records under their names; a failure there is a
    ``ProposalGateNotCarriedWarning``. Raises, before writing anything: ``ProposalSlugError`` (also for a
    proposal or PADR slug whose first segment has no letter), ``ProposalNotFoundError``, ``ProposalInvalidError``
    (also a ``task_kind`` outside ``TASK_KINDS``), ``ProposalNotApprovedError``, ``ProposalNeedsDecomposeError``,
    ``ProposalSlugConflictError``, ``ProposalWorkflowError``,
    ``ProposalTargetExistsError``, ``ProposalWrongWorktreeError`` (``_check_worktree``). A failure while writing
    removes what was written, moves the materials and carried files back and keeps the proposal, then raises
    ``ProposalHandoffError`` (with what the roll-back could not undo in its details), or the ``AdvisoryError``
    itself when the failure was one (such as a ``FrontmatterError`` binding ``spec.md``) and the roll-back was
    complete.
    """
    root = root.resolve()
    slug = require_slug(slug)
    _check_worktree(root, slug)
    day = today or date.today()
    bundle, single = bundle_dir(root, slug), single_file(root, slug)
    is_bundle = bundle.is_dir()
    if not is_bundle and not single.is_file():
        raise ProposalNotFoundError(f"proposal PROP-{slug} not found", target_files=[f"PROP-{slug}"])
    proposal_path = bundle / PROPOSAL_FILE if is_bundle else single
    proposal_rel = proposal_path.relative_to(root).as_posix()
    _require_lettered_slug(f"PROP-{slug}", slug, proposal_rel, "SPEC")
    text = _read(proposal_path, root)
    try:
        meta: dict[str, Any] = parse(text).data or {}
    except FrontmatterError as exc:
        raise ProposalInvalidError(f"{proposal_rel}: {exc.message}", target_files=[proposal_rel]) from exc

    status = text_value(meta.get("status")).lower()
    if status != ACCEPTED:
        raise ProposalNotApprovedError(
            f"proposal PROP-{slug} has status {status or '-'}; handoff needs accepted (given at plan-accept)",
            target_files=[proposal_rel],
        )
    if meta.get(NEEDS_DECOMPOSE) is True:
        raise ProposalNeedsDecomposeError(
            f"proposal PROP-{slug} is marked {NEEDS_DECOMPOSE}: true; it is split in Backlog, never handed off",
            target_files=[proposal_rel],
        )
    namespace = _namespace(root, meta, proposal_rel)
    summary = _summary(meta, proposal_rel)
    kind = _task_kind(meta, proposal_rel)
    index = DocumentIndex.load(root)
    check_spec_conflict(index, slug)
    # The default task-kind binds like no field: a project without its workflow gets an unbound spec and a notice.
    explicit = spec_workflow(kind) if kind and kind != DEFAULT_TASK_KIND else None
    binding, unbound = resolve_binding(root, explicit, proposal_rel, field=TASK_KIND)

    month, stamp = day.strftime("%Y-%m"), day.strftime("%Y%m%d")
    target_dir = spec_dir(root, slug, day)
    targets: list[Path] = [target_dir]
    materials_dir = bundle / MATERIALS
    move_materials = is_bundle and _has_material(materials_dir)
    materials_target: Path | None = None
    target_docs_text: str | None = None
    decisions: list[_Decision] = []
    extras: list[tuple[Path, Path]] = []
    records: list[Path] = []
    gates: list[Decision] = []
    if is_bundle:
        if (bundle / TARGET_DOCS).is_file():
            target_docs_text = _read(bundle / TARGET_DOCS, root)
        decisions = _plan_decisions(root, bundle / DECISIONS, month, stamp)
        targets += [decision.target for decision in decisions]
        records = _unit_records(bundle)
        gates = _proposal_gates(bundle, text_value(meta.get("workflow")))
        preserved = root / "docs" / MATERIALS / month / f"{stamp}-{slug}"
        extras = _plan_extras(root, bundle, decisions, records, preserved, move_materials)
        if move_materials or extras:
            materials_target = preserved
            targets.append(materials_target)
    _check_targets(root, index, targets, decisions)
    for destination in [*targets, *(destination for _, destination in extras)]:
        _require_inside(root, destination)

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
    bugfix = spec_only(binding)
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
        namespace=namespace,
        summary=summary,
        target_docs_ref=target_docs_ref,
    )
    if bugfix:
        # sdd-spec-bugfix writes plan.md and tasks.md in its plan-tasks stage; skeletons would have to match the
        # characterized criteria for the characterize stage's lint-clean exit.
        files = {SPEC_FILE: files[SPEC_FILE]}

    written: list[Path] = []
    moved: list[tuple[Path, Path]] = []
    leftovers: list[Path] = []  # sources copied across file systems, removed once every write succeeded
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
        if materials_target is not None and move_materials:
            make_dirs(materials_target.parent, written)
            move_path(materials_dir, materials_target, written, moved, leftovers)
        for source, destination in extras:
            _require_inside(root, destination)  # the moved materials/ may hold a symbolic link
            make_dirs(destination.parent, written)
            move_path(source, destination, written, moved, leftovers)
    except Exception as exc:
        problems = roll_back(written, moved)
        if isinstance(exc, AdvisoryError) and not problems:
            raise
        what = (
            "the files it wrote were removed and the proposal is kept"
            if not problems
            else "the roll-back was incomplete; inspect the paths in the details before retrying"
        )
        raise ProposalHandoffError(f"handoff of PROP-{slug} failed; {what}", str(exc), *problems) from exc
    remove_paths(leftovers)

    plan = RelocationPlan(proposal=str(bundle if is_bundle else single))
    if is_bundle:
        plan.dir_target = str(target_dir)
        # Carried proposal text and the copied blueprint were written for the bundle directory.
        plan.moved[str(target_dir)] = str(bundle)
        plan.exact[str(bundle / PROPOSAL_FILE)] = str(target_dir / SPEC_FILE)
        if target_docs_text is not None:
            plan.exact[str(bundle / TARGET_DOCS)] = str(target_dir / TARGET_DOCS)
        plan.exact.update(promoted)
        # A promoted ADR was written for decisions/: its relative links resolve from there.
        plan.moved_files.update({str(d.target): str(d.padr) for d in decisions})
        if materials_target is not None and move_materials:
            plan.prefixes[str(materials_dir)] = str(materials_target)
            plan.moved[str(materials_target)] = str(materials_dir)
        for source, destination in extras:
            plan.exact[str(source)] = str(destination)
            plan.moved_files[str(destination)] = str(source)
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
    carried = _record_gates(root, target_dir, slug, binding, gates, notices) if gates and binding is not None else []
    result = _result(
        root, slug, target_dir, binding, unbound, target_docs_text, materials_target, decisions, report, notices
    )
    result.dropped_records = [path.relative_to(root).as_posix() for path in records]
    result.carried_gates = carried
    return result


def _check_worktree(root: Path, slug: str) -> None:
    """Refuse a handoff in a linked worktree on another branch than ``dev-<slug>``, Development's activity branch, at
    either ``[tool.spec] worktree`` level.

    Outside Git and in the base checkout nothing is checked; a detached HEAD counts as another branch. A ``GitError``
    without an exit status (Git missing, a timeout) propagates.
    """
    try:
        dirs = run_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir", "--git-dir").splitlines()
    except GitError as exc:
        if exc.returncode is None:
            raise
        return
    common, git_dir = (Path(line.decode()).resolve() for line in dirs[:2])
    if common == git_dir:
        return
    try:
        branch = run_git(root, "symbolic-ref", "--quiet", "--short", "HEAD").decode().strip()
    except GitError as exc:
        if exc.returncode is None:
            raise
        branch = ""
    expected = f"{DEVELOPMENT_PREFIX}{slug}"
    if branch == expected:
        return
    raise ProposalWrongWorktreeError(
        f"handoff of PROP-{slug} in the worktree of branch {branch or '- (detached HEAD)'}; it runs in the worktree "
        f"of branch {expected}",
        target_files=[str(root)],
        fix=f"Run devkit worktree start {expected} in the base checkout, cd to the path it prints, then rerun "
        f"devkit spec proposal handoff {slug} there",
    )


def _namespace(root: Path, meta: dict[str, Any], proposal_rel: str) -> str | None:
    """The proposal's ``namespace``, carried to ``spec.md``; ``None`` when it has none.

    Raises ``ProposalInvalidError`` when it is not a string naming ``global`` or a registered namespace, and
    ``SpecConfigError`` when ``[tool.spec]`` is malformed.
    """
    if NAMESPACE not in meta:
        return None
    value = meta[NAMESPACE]
    known = [GLOBAL] if value == GLOBAL else known_namespaces(root)
    if isinstance(value, str) and value in known:
        return value
    raise ProposalInvalidError(
        f"{proposal_rel}: namespace {value!r} is not global or a registered namespace",
        target_files=[proposal_rel],
        fix=(
            f"Set the proposal's namespace to one of {', '.join(known)} (registered in [[tool.spec.namespaces]] of"
            " .devkit/config.toml), or remove the field to hand it off as global, then rerun the handoff"
        ),
    )


def _summary(meta: dict[str, Any], proposal_rel: str) -> str | None:
    """The proposal's ``summary``, carried to ``spec.md``; ``None`` when it has none or it is blank.

    Raises ``ProposalInvalidError`` when it is not a string.
    """
    value = meta.get(SUMMARY)
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    raise ProposalInvalidError(
        f"{proposal_rel}: summary {value!r} is not a string",
        target_files=[proposal_rel],
        fix=(
            "Write the proposal's summary as one or two English sentences in quotes, or remove the field, then rerun"
            " the handoff"
        ),
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


def _require_lettered_slug(name: str, slug: str, rel: str, prefix: str) -> None:
    """Refuse a legacy ``name`` whose slug starts with a number: its ``<prefix>-<slug>`` would fail
    ``RULE-id-convention`` (``2024-budget`` reads as the retired number-based ID ``2024``)."""
    if first_segment_has_letter(slug):
        return
    raise ProposalSlugError(
        f"{name} has slug {slug!r}, whose first segment has no letter; {prefix}-{slug} would break RULE-id-convention",
        target_files=[rel],
        fix=f"Rename {name} (its file or directory and its id) so the first segment of its slug has a letter (for"
        " example budget-2024 instead of 2024-budget), update references to it, then rerun the handoff",
    )


def _plan_decisions(root: Path, decisions_dir: Path, month: str, stamp: str) -> list[_Decision]:
    """The ADRs the bundle's ``PADR-*.md`` files become, with their promoted text."""
    if not decisions_dir.is_dir():
        return []
    sources = []
    for padr in sorted(p for p in decisions_dir.iterdir() if p.is_file() and p.name.startswith("PADR-")):
        if not padr.name.endswith(".md"):
            continue
        adr_slug = clean_slug(padr.name.removeprefix("PADR-").removesuffix(".md"))
        if not adr_slug:
            continue
        rel = padr.relative_to(root).as_posix()
        _require_lettered_slug(f"PADR-{adr_slug}", adr_slug, rel, "ADR")
        original = _read(padr, root)
        try:
            old = parse_document(rel, original)
        except FrontmatterError as exc:
            raise ProposalInvalidError(f"{rel}: {exc.message}", target_files=[rel]) from exc
        sources.append((padr, adr_slug, original, rel, old.id if old else f"PADR-{adr_slug}"))
    padr_ids = {source[4] for source in sources}

    def promote_id(match: re.Match[str]) -> str:
        # Only the PADRs promoted here become ADRs; a file name (PADR-x.md in a link) is left to the link rewrite.
        if match.group() not in padr_ids or match.string.startswith(".md", match.end()):
            return match.group()
        return match.group().removeprefix("P")

    planned = []
    for padr, adr_slug, original, rel, padr_id in sources:
        promoted = _PADR.sub(promote_id, original)
        promoted = _DRAFT_STATUS.sub("status: accepted", promoted)
        promoted = _DRAFT_BODY_STATUS.sub("- **Status**: Accepted", promoted)
        try:
            new = parse_document(rel, promoted)
        except FrontmatterError as exc:
            raise ProposalInvalidError(f"{rel}: {exc.message}", target_files=[rel]) from exc
        target = root / "docs" / DECISIONS / month / f"{stamp}-{adr_slug}.md"
        planned.append(
            _Decision(
                padr=padr,
                padr_id=padr_id,
                target=target,
                adr_id=new.id if new else f"ADR-{adr_slug}",
                text=promoted,
            )
        )
    return planned


def _unit_records(bundle: Path) -> list[Path]:
    """The proposal unit's devkit workflow records: every decision record and envelope devkit's loaders find in
    ``bundle``, malformed ones included, sorted. A PADR or another file under ``decisions/`` is not one of them."""
    decisions, envelopes = load_decisions(bundle), load_envelopes(bundle)
    files = [record.file for record in decisions.records]
    files += [envelope.file for items in envelopes.by_kind.values() for envelope in items]
    files += [error.file for error in [*decisions.errors, *envelopes.errors]]
    return sorted({bundle / file for file in files if file})


def _task_kind(meta: dict[str, Any], proposal_rel: str) -> str | None:
    """The proposal's ``task_kind``; ``None`` when it has none (the default, ``feature``).

    Raises ``ProposalInvalidError`` when it is not one of ``TASK_KINDS``.
    """
    if TASK_KIND not in meta:
        return None
    value = meta[TASK_KIND]
    if isinstance(value, str) and value.strip() in TASK_KINDS:
        return value.strip()
    raise ProposalInvalidError(
        f"{proposal_rel}: {TASK_KIND} {value!r} is not one of {' | '.join(TASK_KINDS)}",
        target_files=[proposal_rel],
        fix=f"Set the proposal's {TASK_KIND} to the task-kind confirmed at plan-accept ({' or '.join(TASK_KINDS)}),"
        " then rerun the handoff",
    )


def _proposal_gates(bundle: Path, workflow: str) -> list[Decision]:
    """The proposal's approvals the spec carries (``CARRIED_GATES``, in order): for each, the latest record of the
    unit's bound ``workflow`` that is not ``cancel``, when it is ``accept`` and no return record that is not a
    ``cancel`` follows it. Stricter than devkit's voiding, so a doubtful approval is asked again rather than carried.
    """
    if not workflow:
        return []
    records = load_decisions(bundle).segment(workflow, 0)
    carried = []
    for request in CARRIED_GATES:
        answer = records.effective(request)
        if answer is None or answer.action != "accept":
            continue
        if any(
            record.request.startswith(RETURN_PREFIX) and record.action != "cancel" and record.seq > answer.seq
            for record in records.records
        ):
            continue
        carried.append(answer)
    return carried


def _record_gates(
    root: Path,
    target_dir: Path,
    slug: str,
    binding: Binding,
    gates: list[Decision],
    notices: list[AdvisoryError],
) -> list[CarriedGate]:
    """Record each of the proposal's ``gates`` in the spec under its own name, with its ``by`` and a note naming
    ``PROP-<slug>``. A gate that is an open request of the bound spec (``gate:plan-intent`` at its ``intent`` stage)
    is answered with devkit's ``record_answer``; one the spec's workflow never asks (``gate:plan-accept``) is written
    as a decision record of the spec's workflow with the proposal's stage, kept for the audit trail and counting for
    no stage. A gate the spec answered by policy is skipped. The first failure of any kind stops and is added to
    ``notices`` as a ``ProposalGateNotCarriedWarning``: the handoff itself is done by then."""
    rel = target_dir.relative_to(root).as_posix()
    note = f"PROP-{slug}"
    carried: list[CarriedGate] = []
    request = gates[0].request
    try:
        workspace = Workspace(root, lint=None, ancestor=None)
        for gate in gates:
            request = gate.request
            unit = workspace.resolve_unit(rel)
            evaluation = workspace.evaluate_unit(unit, lint=False)
            if request in {open_request.id for open_request in evaluation.requests}:
                decision = record_answer(workspace, unit, request, "accept", note=note, by=gate.by, lint=False)
            elif any(stage.gate == request.removeprefix("gate:") for stage in unit.doc.stages):
                continue  # the spec's own gate, not open: answered by policy or already recorded
            else:
                record = new_decision(
                    load_decisions(target_dir),
                    request,
                    "accept",
                    workflow=binding.workflow,
                    stage=gate.stage,
                    note=note,
                    by=gate.by,
                )
                decision = write_decision(target_dir, record)
            carried.append(CarriedGate(request, f"{rel}/{decision.file}"))
    except Exception as exc:  # the handoff is done: any failure here is reported, never raised
        detail = f"{exc.code}: {exc.message}" if isinstance(exc, AdvisoryError) else str(exc)
        notices.append(
            ProposalGateNotCarriedWarning(
                f"{request} of SPEC-{slug} was not carried from {note}",
                detail,
                target_files=[f"{rel}/{SPEC_FILE}"],
                fix=f"Once the cause is resolved, ask the user again for each gate devkit workflow next --unit {rel} "
                "reports as waiting and record the answer with devkit workflow answer",
            )
        )
    return carried


def _has_material(materials_dir: Path) -> bool:
    """Whether ``materials_dir`` holds anything worth preserving: a file other than ``JUNK_FILES`` or a symbolic link,
    at any depth (empty directories and junk are deleted with the proposal). A symbolic link ``materials_dir`` is
    preserved as the link."""
    if materials_dir.is_symlink():
        return True
    if not materials_dir.is_dir():
        return False
    for current, dirnames, filenames in os.walk(materials_dir):
        here = Path(current)
        if any(name not in JUNK_FILES or (here / name).is_symlink() for name in filenames):
            return True
        if any((here / name).is_symlink() for name in dirnames):
            return True
    return False


def _plan_extras(
    root: Path,
    bundle: Path,
    decisions: list[_Decision],
    records: list[Path],
    materials: Path,
    move_materials: bool,
) -> list[tuple[Path, Path]]:
    """Every bundle file the handoff does not carry otherwise, with its destination under ``materials`` at its path
    relative to the bundle (``materials/`` itself moves as a whole when ``move_materials``). ``JUNK_FILES`` and the
    unit's workflow ``records`` are not carried; other hidden files are. Symbolic links are never followed: one is
    carried as a file.

    Raises ``ProposalTargetExistsError`` when a destination is also the destination of a path in ``materials/``, or
    lies below a file or symbolic link there or below a ``materials/`` that is a symbolic link (moving into it would
    leave the preserved directory).
    """
    carried = {bundle / PROPOSAL_FILE, bundle / TARGET_DOCS, *(decision.padr for decision in decisions), *records}
    materials_dir = bundle / MATERIALS

    def taken(rel: Path) -> bool:
        """Whether moving ``materials/`` already puts something at ``rel``, or a file or symlink at a parent (a
        ``materials/`` that is itself one takes every destination)."""
        if materials_dir.is_symlink() or materials_dir.is_file() or os.path.lexists(materials_dir / rel):
            return True
        return any(
            (materials_dir / parent).is_symlink() or (materials_dir / parent).is_file() for parent in rel.parents[:-1]
        )

    extras = []
    for path in sorted(bundle.rglob("*")):
        if (path.is_dir() and not path.is_symlink()) or path in carried:
            continue
        if (materials_dir.is_dir() or materials_dir.is_symlink()) and path.is_relative_to(materials_dir):
            continue  # moved as a whole, or junk deleted with the proposal
        if path.name in JUNK_FILES and not path.is_symlink():
            continue
        extras.append((path, materials / path.relative_to(bundle)))
    clashes = [source for source, _ in extras if move_materials and taken(source.relative_to(bundle))]
    if clashes:
        rels = [path.relative_to(root).as_posix() for path in clashes]
        raise ProposalTargetExistsError(
            f"the handoff would move {', '.join(rels)} onto a path of materials/ (the same path, or below a file or"
            " symbolic link)",
            target_files=rels,
            fix="Rename or move the path in [TARGET] (or its counterpart in materials/), then rerun the handoff",
        )
    return extras


def _require_inside(root: Path, destination: Path) -> None:
    """Refuse to write or carry anything to ``destination`` when its directory resolves outside the workspace
    ``root`` (a symbolic link on the way)."""
    if destination.parent.resolve().is_relative_to(root):
        return
    rel = destination.relative_to(root).as_posix()
    raise ProposalTargetExistsError(
        f"the handoff would write {rel}, whose directory resolves outside the workspace",
        target_files=[rel],
        fix="Replace the symbolic link on the way to [TARGET] with a directory, then rerun the handoff",
    )


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
