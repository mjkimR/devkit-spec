"""``devkit.integration.readiness`` provider (``spec``): SDD completion readiness at ``source_sha``.

``devkit.integration`` calls ``check(context)`` during ``prepare(branch, task)`` and again immediately before merging
an approved ``IntegrationRequest``. Because ``IntegrationService`` requires ``check(context) == request.readiness`` at
merge time, readiness verification reads only the committed Git trees of ``context.finish.source_sha`` and
``context.finish.target_sha`` (never uncommitted working-tree files or wall-clock timestamps) and always returns a
non-empty tuple of deterministic ``Evidence`` items, with any unmet conditions listed in ``Readiness.reasons``.
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Sequence
from pathlib import Path

from devkit.advisory import AdvisoryError
from devkit.core import FrontmatterError, is_safe_relpath, load_receipt, run_git
from devkit.core.frontmatter import parse
from devkit.integration import Evidence, IntegrationContext, Readiness
from devkit.rules import Phase, Snapshot, materialize_snapshot, run_project_rules
from devkit.workflow import Workspace, is_ancestor, load_decisions, load_envelopes, load_workflow_config

from devkit_spec.attach import (
    PROPOSAL_UNIT,
    PROPOSAL_WORKFLOW,
    SPEC_UNIT,
    attach_check,
)
from devkit_spec.config import check_approvals, read_spec_config

REGULAR_MODES = {"100644", "100755"}
SYMLINK_MODE = "120000"
GITLINK_MODE = "160000"
SPEC_WORKFLOWS = frozenset({"sdd-spec-feature", "sdd-spec-bugfix"})
SESSION_KINDS = frozenset({"feature", "bugfix"})
SESSION_EFFORTS = frozenset({"low", "medium", "high"})


def _decode(raw: bytes) -> str:
    return raw.decode("utf-8", errors="surrogateescape")


def _snapshot_root(base: Path, worktree: Path) -> Path:
    if worktree.is_dir() and (worktree / ".devkit" / "managed").is_dir():
        return worktree.resolve()
    return base.resolve()


def _build_snapshot(root: Path, source_sha: str, target_sha: str) -> Snapshot:
    tree = run_git(root, "rev-parse", "--verify", "--quiet", f"{source_sha}^{{tree}}").decode().strip()
    prior = run_git(root, "merge-base", "--", target_sha, source_sha).decode().strip()
    output = run_git(root, "diff", "--name-status", "-z", "--no-renames", prior, tree, "--")
    parts = [part for part in output.split(b"\0") if part]
    changed: list[str] = []
    deleted: list[str] = []
    for status, name in zip(parts[0::2], parts[1::2], strict=True):
        path = _decode(name)
        changed.append(path)
        if status.startswith(b"D"):
            deleted.append(path)
    files: list[tuple[str, str, str]] = []
    regular: set[str] = set()
    for entry in run_git(root, "ls-tree", "-r", "--full-tree", "-z", tree).split(b"\0"):
        if not entry:
            continue
        meta, _, raw_path = entry.partition(b"\t")
        file_mode, _kind, sha = meta.decode().split(" ")
        name = _decode(raw_path)
        if file_mode not in REGULAR_MODES | {SYMLINK_MODE, GITLINK_MODE} or not is_safe_relpath(name, canonical=True):
            continue
        files.append((name, sha, file_mode))
        if file_mode in REGULAR_MODES:
            regular.add(name)
    return Snapshot(
        root=root,
        mode="ci",
        tree=tree,
        base=prior,
        changed=tuple(path for path in changed if path in regular),
        deleted=tuple(deleted),
        files=tuple(files),
    )


def _populate_managed_files(workspace: Path, sources: Sequence[Path]) -> None:
    try:
        receipt = load_receipt(workspace)
    except AdvisoryError:
        return
    if receipt is None:
        return
    for rel, record in receipt.file_records.items():
        dest = workspace / rel
        if dest.exists() or dest.is_symlink():
            continue
        for src in sources:
            candidate = src / rel
            try:
                if not candidate.is_file() or candidate.is_symlink():
                    continue
                data = candidate.read_bytes()
                if not record.matches(data):
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                if record.mode == 0o755:
                    dest.chmod(0o755)
                break
            except OSError:
                continue


def _check_project_policies(base: Path, workspace: Path) -> list[str]:
    reasons: list[str] = []
    for label, root in (("base", base), ("source", workspace)):
        try:
            read_spec_config(root)
        except AdvisoryError as exc:
            reasons.append(f"{label} [tool.spec] policy invalid ({exc.code}): {exc.message}")
        try:
            wf_config = load_workflow_config(root)
            check_approvals(wf_config.approvals)
        except AdvisoryError as exc:
            reasons.append(f"{label} workflow policy invalid ({exc.code}): {exc.message}")
    return reasons


def _check_ci_rules(snapshot: Snapshot) -> tuple[str, list[str]]:
    reasons: list[str] = []
    try:
        run = run_project_rules(snapshot.root, snapshot=snapshot, phase=Phase.LINTER)
    except AdvisoryError as exc:
        return f"error:{exc.code}", [f"CI rules failed to run ({exc.code}): {exc.message}"]
    for err in run.errors:
        reasons.append(f"CI rule problem ({err.code}): {err.message}")
    for violation in run.blocking_violations:
        reasons.append(
            f"CI rule violation {violation.rule_id} at {violation.file}:{violation.line}: {violation.message}"
        )
    if reasons:
        return f"fail:errors={len(run.errors)},violations={len(run.blocking_violations)}", reasons
    return "pass", []


def _read_frontmatter(path: Path) -> tuple[dict[str, object], str | None]:
    if not path.is_file():
        return {}, f"missing {path.name}"
    try:
        doc = parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, FrontmatterError) as exc:
        return {}, f"{path.name} frontmatter is unreadable: {exc}"
    return dict(doc.data or {}), None


def _check_unit_task(
    context: IntegrationContext,
    base: Path,
    workspace: Path,
) -> tuple[list[Evidence], list[str]]:
    branch = context.finish.branch
    activity, _, slug = branch.partition("-")
    unit_rel = (context.task.unit or "").strip("/")
    reasons: list[str] = []

    reasons.extend(attach_check(base, branch, unit_rel, context.finish.source_sha))
    if activity == "dev" and SPEC_UNIT.fullmatch(unit_rel) is None:
        reasons.append(
            f"{unit_rel} is not a handed-off spec bundle specs/<YYYY-MM>/<YYYYMMDD>-{slug}; "
            f"hand off the proposal before integrating {branch}"
        )

    ws = Workspace(workspace, ancestor=lambda _root, anc, desc: is_ancestor(base, anc, desc))
    if ws.discovery_errors:
        for err in ws.discovery_errors:
            reasons.append(f"workflow discovery error ({err.code}): {err.message}")

    workflow_id = "unknown"
    stage_status = "unresolved"
    hold_status = "unknown"

    try:
        ref = ws.resolve_unit(unit_rel)
        workflow_id = ref.doc.id
    except AdvisoryError as exc:
        reasons.append(f"unit {unit_rel} could not be resolved ({exc.code}): {exc.message}")
        return (
            [
                Evidence("TASK_KIND", "unit"),
                Evidence("WORKFLOW", workflow_id),
                Evidence("UNIT", unit_rel or "none"),
                Evidence("SOURCE_SHA", context.finish.source_sha),
                Evidence("TARGET_SHA", context.finish.target_sha),
                Evidence("STAGE_STATUS", stage_status),
                Evidence("HOLD_STATUS", hold_status),
            ],
            reasons,
        )

    if not ref.binding.bound:
        reasons.append(f"unit {unit_rel} is not bound to workflow {workflow_id}")

    anchor_data, anchor_err = _read_frontmatter(ref.anchor_path)
    if anchor_err:
        reasons.append(f"{unit_rel}/{ref.anchor}: {anchor_err}")
    doc_id = anchor_data.get("id")
    expected_ids = {slug, f"SPEC-{slug}" if activity == "dev" else f"PROP-{slug}"}
    if isinstance(doc_id, str) and doc_id:
        expected_ids.add(doc_id)
    if context.task.id not in expected_ids:
        reasons.append(f"task.id {context.task.id!r} does not match unit {unit_rel} ({sorted(expected_ids)})")

    given = ("dev-integration", "lint-ci-clean") if workflow_id in SPEC_WORKFLOWS else ()
    try:
        evaluation = ws.evaluate_unit(ref, given=given)
    except AdvisoryError as exc:
        reasons.append(f"workflow evaluation failed ({exc.code}): {exc.message}")
        return (
            [
                Evidence("TASK_KIND", "unit"),
                Evidence("WORKFLOW", workflow_id),
                Evidence("UNIT", unit_rel),
                Evidence("SOURCE_SHA", context.finish.source_sha),
                Evidence("TARGET_SHA", context.finish.target_sha),
                Evidence("STAGE_STATUS", f"error:{exc.code}"),
                Evidence("HOLD_STATUS", hold_status),
            ],
            reasons,
        )

    for err in evaluation.errors:
        reasons.append(f"workflow error ({err.code}): {err.message}")
    if evaluation.stale_approvals:
        stale = ", ".join(decision.file for decision in evaluation.stale_approvals)
        reasons.append(f"unit {unit_rel} has stale approvals: {stale}")

    problems = len(evaluation.hold.problems)
    questions = len(evaluation.hold.questions)
    if problems or questions:
        hold_status = f"held:problems={problems},questions={questions}"
        reasons.append(f"unit {unit_rel} is held (problems={problems}, pending_questions={questions})")
    else:
        hold_status = "clear"

    if activity == "dev":
        if workflow_id not in SPEC_WORKFLOWS:
            reasons.append(f"dev branch {branch} requires workflow in {sorted(SPEC_WORKFLOWS)}, got {workflow_id}")
        decisions = load_decisions(ref.dir)
        for decision in decisions.records:
            if decision.request == "gate:plan-accept" and decision.action != "accept":
                reasons.append(f"carried gate:plan-accept in {decision.file} is {decision.action!r}, not 'accept'")
        if evaluation.stage is not None and evaluation.stage.id == "merge" and "integrate" in evaluation.done:
            stage_status = f"ready:{','.join(evaluation.done)}"
        else:
            current = evaluation.stage.id if evaluation.stage is not None else "complete"
            stage_status = f"incomplete:{current}"
            unmet = ", ".join(check.name for check in evaluation.unmet)
            if evaluation.gate is not None and not evaluation.gate.satisfied:
                reasons.append(f"stage {current} is waiting on gate:{evaluation.gate.name}")
            if unmet:
                reasons.append(f"stage {current} has unmet checks: {unmet}")
            elif evaluation.stage is None or evaluation.stage.id != "merge":
                reasons.append(f"unit {unit_rel} is at stage {current!r}, not ready for merge")
    elif activity == "plan":
        if workflow_id != PROPOSAL_WORKFLOW:
            reasons.append(f"plan branch {branch} requires workflow {PROPOSAL_WORKFLOW}, got {workflow_id}")
        status = anchor_data.get("status")
        if status != "accepted":
            reasons.append(f"{unit_rel}/proposal.md status must be 'accepted' for integration, got {status!r}")
        if anchor_data.get("needs_decompose") is True:
            reasons.append(f"{unit_rel}/proposal.md has needs_decompose=true")
        passed_gates = {gate.name for _stage, gate in evaluation.passed_gates if gate.satisfied}
        for required_gate in ("plan-intent", "plan-accept"):
            if required_gate not in passed_gates:
                reasons.append(f"{unit_rel} has not passed gate:{required_gate}")
        if evaluation.complete and "direction-handoff" in evaluation.done:
            stage_status = f"ready:{','.join(evaluation.done)}"
        else:
            current = evaluation.stage.id if evaluation.stage is not None else "incomplete"
            stage_status = f"incomplete:{current}"
            unmet = ", ".join(check.name for check in evaluation.unmet)
            if evaluation.gate is not None and not evaluation.gate.satisfied:
                reasons.append(f"stage {current} is waiting on gate:{evaluation.gate.name}")
            if unmet:
                reasons.append(f"stage {current} has unmet checks: {unmet}")

    evidence = [
        Evidence("TASK_KIND", "unit"),
        Evidence("WORKFLOW", workflow_id),
        Evidence("UNIT", unit_rel),
        Evidence("SOURCE_SHA", context.finish.source_sha),
        Evidence("TARGET_SHA", context.finish.target_sha),
        Evidence("STAGE_STATUS", stage_status),
        Evidence("HOLD_STATUS", hold_status),
    ]
    return evidence, reasons


def _claim_passed(value: object) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        normalized = value.strip().upper()
        return normalized == "PASSED" or normalized == "PASS" or normalized.startswith("PASS ")
    return False


def _touched_units(snapshot: Snapshot, workspace: Path) -> set[str]:
    units: set[str] = set()
    for rel in (*snapshot.changed, *snapshot.deleted):
        parts = Path(rel).parts
        if len(parts) >= 3 and parts[0] == "specs":
            candidate = f"{parts[0]}/{parts[1]}/{parts[2]}"
            if SPEC_UNIT.fullmatch(candidate) and (workspace / candidate).is_dir():
                units.add(candidate)
        elif len(parts) >= 3 and parts[0] == "docs" and parts[1] == "proposals":
            candidate = f"{parts[0]}/{parts[1]}/{parts[2]}"
            if PROPOSAL_UNIT.fullmatch(candidate) and (workspace / candidate).is_dir():
                units.add(candidate)
    return units


def _check_session_task(
    context: IntegrationContext,
    snapshot: Snapshot,
    workspace: Path,
) -> tuple[list[Evidence], list[str]]:
    branch = context.finish.branch
    activity, _, slug = branch.partition("-")
    reasons: list[str] = []
    if activity != "dev":
        reasons.append(f"session tasks must run on a dev-<slug> branch, not {branch}")

    # Verify the branch does not carry a spec/proposal unit for this slug or leave a touched unit held/incomplete.
    for spec_dir in sorted((workspace / "specs").glob(f"*/*-{slug}")) if (workspace / "specs").is_dir() else ():
        rel = spec_dir.relative_to(workspace).as_posix()
        if SPEC_UNIT.fullmatch(rel):
            reasons.append(f"branch {branch} has spec unit {rel}; integrate it as a unit task, not a session task")
    for unit_rel in sorted(_touched_units(snapshot, workspace)):
        unit_dir = workspace / unit_rel
        envelopes = load_envelopes(unit_dir)
        if envelopes.errors:
            reasons.append(f"touched unit {unit_rel} has malformed envelopes")
        hold = envelopes.hold()
        if hold.problems or hold.questions:
            reasons.append(f"touched unit {unit_rel} has an unresolved problem or pending question hold")
        if SPEC_UNIT.fullmatch(unit_rel):
            data, err = _read_frontmatter(unit_dir / "spec.md")
            if err or data.get("status") != "completed":
                reasons.append(f"touched spec unit {unit_rel} is not completed")

    try:
        claims = json.loads(context.task.claims_json)
    except ValueError:
        claims = {}
    if not isinstance(claims, dict):
        claims = {}

    task_kind = claims.get("task_kind")
    effort = claims.get("effort")
    if task_kind not in SESSION_KINDS:
        reasons.append("session claims require task_kind in 'feature' or 'bugfix'")
    if effort not in SESSION_EFFORTS:
        reasons.append("session claims require effort in 'low', 'medium' or 'high'")
    for field in ("review", "tests", "lint"):
        if not _claim_passed(claims.get(field)):
            reasons.append(f"session claims require passing {field} verification")
    if task_kind == "bugfix":
        for field in ("reproduced", "resolved"):
            if not _claim_passed(claims.get(field)):
                reasons.append(f"bugfix session claims require passing {field} verification")
    if claims.get("blocked") is True or claims.get("pending_questions") is True:
        reasons.append("session claims report a blocked problem or pending question")

    workflow_id = f"sdd-session-{task_kind}" if isinstance(task_kind, str) and task_kind in SESSION_KINDS else "unknown"
    claims_summary = (
        f"kind={task_kind or 'invalid'},effort={effort or 'invalid'},"
        f"review={'pass' if _claim_passed(claims.get('review')) else 'fail'},"
        f"tests={'pass' if _claim_passed(claims.get('tests')) else 'fail'},"
        f"lint={'pass' if _claim_passed(claims.get('lint')) else 'fail'}"
    )
    if task_kind == "bugfix":
        claims_summary += (
            f",reproduced={'pass' if _claim_passed(claims.get('reproduced')) else 'fail'},"
            f"resolved={'pass' if _claim_passed(claims.get('resolved')) else 'fail'}"
        )
    evidence = [
        Evidence("TASK_KIND", "session"),
        Evidence("WORKFLOW", workflow_id),
        Evidence("SOURCE_SHA", context.finish.source_sha),
        Evidence("TARGET_SHA", context.finish.target_sha),
        Evidence("SESSION_CLAIMS", claims_summary),
    ]
    return evidence, reasons


def check(context: IntegrationContext) -> Readiness:
    """Verify SDD completion readiness for ``context`` from committed Git state."""
    base = Path(context.finish.base).resolve()
    worktree = Path(context.finish.path)
    snap_root = _snapshot_root(base, worktree)
    snapshot = _build_snapshot(snap_root, context.finish.source_sha, context.finish.target_sha)
    sources = (worktree.resolve(), base) if worktree.is_dir() else (base,)

    with tempfile.TemporaryDirectory(prefix="devkit-spec-readiness-") as temp_dir:
        workspace = Path(temp_dir).resolve()
        materialize_snapshot(snapshot, workspace)
        _populate_managed_files(workspace, sources)

        reasons = _check_project_policies(base, workspace)
        if context.task.kind == "unit":
            evidence, task_reasons = _check_unit_task(context, base, workspace)
        else:
            evidence, task_reasons = _check_session_task(context, snapshot, workspace)
        reasons.extend(task_reasons)

    ci_status, ci_reasons = _check_ci_rules(snapshot)
    evidence.append(Evidence("CI_RULES", ci_status))
    reasons.extend(ci_reasons)

    return Readiness(
        source_sha=context.finish.source_sha,
        target_sha=context.finish.target_sha,
        evidence=tuple(evidence),
        reasons=tuple(reasons),
    )
