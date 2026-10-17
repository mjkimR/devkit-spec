"""The ``devkit.integration.readiness`` provider (``spec``) and end-to-end ``IntegrationService`` tests."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner
from devkit.cli import cli as devkit_cli
from devkit.core import git as core_git
from devkit.host.mcp import ConfirmationReply
from devkit.integration import (
    IntegrationContext,
    IntegrationService,
    ReadinessError,
    Task,
    providers,
)
from devkit.worktree import PullRequestPolicyError, locate, plan_finish
from scope.support import git, write

from devkit_spec.integration import check


def _devkit(*args: str) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("DEVKIT_")}
    return subprocess.run(
        [sys.executable, "-m", "devkit", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )


def _cli(root: Path, *args: str) -> str:
    res = CliRunner().invoke(devkit_cli, [*args, "-w", str(root)])
    assert res.exit_code == 0, res.stdout + (res.stderr if hasattr(res, "stderr") else "")
    return res.stdout


@pytest.fixture(scope="module")
def synced_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("synced-integration")
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    res = _devkit("sync", "-w", str(root))
    assert res.returncode == 0, res.stderr
    return root


def _make_synced_repo(tmp_path: Path, template: Path, *, extra_config: str = "") -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "t")
    git(repo, "config", "commit.gpgsign", "false")
    shutil.copytree(template / ".devkit", repo / ".devkit")
    write(repo, ".gitignore", ".devkit/managed/\n")
    config_path = repo / ".devkit/config.toml"
    config_text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    if "[integration]" not in config_text:
        config_text += '\n[integration]\nprovider = "spec"\n'
    if extra_config:
        config_text += "\n" + extra_config.strip() + "\n"
    config_path.write_text(config_text.lstrip(), encoding="utf-8")
    write(
        repo,
        "docs/capabilities/delivery/CAP-DLV-sample.md",
        "---\nid: CAP-DLV-sample\ntitle: Sample\nsummary: Sample capability.\nstatus: active\narea: delivery\ncreated: 2026-10-01\nupdated: 2026-10-01\n---\n\n# [CAP-DLV-sample] Sample\n\n## 1. Overview\nSample capability.\n",
    )
    write(repo, "src/app.py", "VALUE = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "initial")
    return repo


def _start_worktree(repo: Path, branch: str, path: Path) -> Path:
    git(repo, "worktree", "add", "-q", "-b", branch, str(path), "main")
    git(repo, "config", f"branch.{branch}.devkitWorktree", "true")
    git(repo, "config", f"branch.{branch}.devkitBase", "main")
    shutil.copytree(repo / ".devkit/managed", path / ".devkit/managed", dirs_exist_ok=True)
    return path


def _complete_feature_spec(wt: Path, slug: str = "feat", *, date: str = "2026-10-17") -> str:
    month = date[:7]
    compact = date.replace("-", "")
    unit = f"specs/{month}/{compact}-{slug}"
    _cli(wt, "workflow", "new", slug, "--workflow", "sdd-spec-feature", "--date", date)
    _cli(
        wt, "workflow", "answer", "--unit", unit, "--request", "gate:plan-intent", "--action", "accept", "--by", "user"
    )
    write(
        wt,
        f"{unit}/spec.md",
        f"---\nid: SPEC-{slug}\ntitle: Feature {slug}\nsummary: Add feature {slug}.\nstatus: completed\ncreated: {date}\nworkflow: sdd-spec-feature\n---\n\n# [SPEC-{slug}] Feature {slug}\n\n## 1. Problem Statement & Motivation\nNeed feature {slug}.\n\n## 2. Acceptance Criteria\n\n### Scenario 1: [AC-01] Feature works\n- **Given** x\n- **When** y\n- **Then** z\n",
    )
    _cli(wt, "workflow", "bind", "--unit", unit, "--workflow", "sdd-spec-feature")
    write(
        wt,
        f"{unit}/plan.md",
        f"---\nid: PLAN-{slug}\nspec: SPEC-{slug}\n---\n\n# Technical Plan\n\n## 1. Design\nUpdate src/app.py.\n",
    )
    write(
        wt,
        f"{unit}/tasks.md",
        f"---\nid: TASKS-{slug}\nplan: PLAN-{slug}\n---\n\n# Tasks\n\n- [x] **Task 1: Update app**\n  - _Boundary: `src/app.py`\n  - _Requirements: AC-01_\n",
    )
    write(wt, "src/app.py", "VALUE = 2\n")
    write(
        wt,
        "docs/capabilities/delivery/CAP-DLV-sample.md",
        "---\nid: CAP-DLV-sample\ntitle: Sample\nsummary: Sample capability.\nstatus: active\narea: delivery\ncreated: 2026-10-01\nupdated: 2026-10-17\n---\n\n# [CAP-DLV-sample] Sample\n\n## 1. Overview\nSample capability updated.\n",
    )
    write(
        wt,
        f"{unit}/reconcile.md",
        f"---\nreconcile_id: REC-{slug}\nspec: SPEC-{slug}\nstatus: resolved\ntargets:\n  - file: docs/capabilities/delivery/CAP-DLV-sample.md\n    resolution: modified\n---\n\n# Reconcile\n\nUpdated sample capability.\n",
    )
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", "feat: implement feature")
    head = git(wt, "rev-parse", "HEAD")
    _cli(
        wt,
        "workflow",
        "envelope",
        "review",
        "--unit",
        unit,
        "--stage",
        "review-refine",
        "--summary",
        "Review passed.",
        "--head",
        head,
    )
    _cli(
        wt,
        "workflow",
        "envelope",
        "new",
        "--unit",
        unit,
        "--kind",
        "reconcile-check",
        "--stage",
        "living-spec-draft",
        "--summary",
        "Reconcile verified.",
        "--head",
        head,
    )
    _cli(
        wt,
        "workflow",
        "envelope",
        "new",
        "--unit",
        unit,
        "--kind",
        "feedback",
        "--stage",
        "collect-feedback",
        "--summary",
        "Sweep complete.",
        "--check",
        "swept=PASS 0 items",
    )
    _cli(
        wt,
        "workflow",
        "envelope",
        "new",
        "--unit",
        unit,
        "--kind",
        "final-report",
        "--stage",
        "final-change-report",
        "--summary",
        "All checks pass.",
        "--check",
        "tests=PASS pytest",
        "--check",
        "build=PASS build",
        "--check",
        "lint=PASS lint",
    )
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", "chore: record envelopes")
    return unit


def _complete_bugfix_spec(wt: Path, slug: str = "fix", *, date: str = "2026-10-17") -> str:
    month = date[:7]
    compact = date.replace("-", "")
    unit = f"specs/{month}/{compact}-{slug}"
    _cli(wt, "workflow", "new", slug, "--workflow", "sdd-spec-bugfix", "--date", date)
    _cli(
        wt, "workflow", "answer", "--unit", unit, "--request", "gate:plan-intent", "--action", "accept", "--by", "user"
    )
    write(
        wt,
        f"{unit}/spec.md",
        f"---\nid: SPEC-{slug}\ntitle: Bugfix {slug}\nsummary: Fix bug {slug}.\nstatus: completed\ncreated: {date}\nworkflow: sdd-spec-bugfix\n---\n\n# [SPEC-{slug}] Bugfix {slug}\n\n## 1. Defect Characterization\nBug details.\n\n## 2. Acceptance Criteria\n\n### Scenario 1: [AC-01] Bug fixed\n- **Given** x\n- **When** y\n- **Then** z\n",
    )
    _cli(wt, "workflow", "bind", "--unit", unit, "--workflow", "sdd-spec-bugfix")
    write(
        wt,
        f"{unit}/plan.md",
        f"---\nid: PLAN-{slug}\nspec: SPEC-{slug}\n---\n\n# Fix Plan\n\n## 1. Design\nFix src/app.py.\n",
    )
    write(
        wt,
        f"{unit}/tasks.md",
        f"---\nid: TASKS-{slug}\nplan: PLAN-{slug}\n---\n\n# Tasks\n\n- [x] **Task 1: Fix bug**\n  - _Boundary: `src/app.py`\n  - _Requirements: AC-01_\n",
    )
    write(wt, "src/app.py", "VALUE = 3\n")
    write(
        wt,
        f"{unit}/reconcile.md",
        f"---\nreconcile_id: REC-{slug}\nspec: SPEC-{slug}\nstatus: resolved\ntargets:\n  - file: docs/capabilities/delivery/CAP-DLV-sample.md\n    resolution: waived\n    rationale: Behavior already matches documented contract.\n---\n\n# Reconcile\n\nNo doc change needed.\n",
    )
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", "fix: resolve defect")
    head = git(wt, "rev-parse", "HEAD")
    _cli(
        wt,
        "workflow",
        "envelope",
        "new",
        "--unit",
        unit,
        "--kind",
        "red",
        "--stage",
        "reproduce",
        "--summary",
        "Reproduced failure.",
        "--check",
        "reproduced=PASS pytest failed before fix",
        "--head",
        head,
    )
    _cli(
        wt,
        "workflow",
        "envelope",
        "new",
        "--unit",
        unit,
        "--kind",
        "green",
        "--stage",
        "fix-verify",
        "--summary",
        "Verified fix.",
        "--check",
        "resolved=PASS pytest passed",
        "--check",
        "preserved=PASS regression suite passed",
        "--head",
        head,
    )
    _cli(
        wt,
        "workflow",
        "envelope",
        "review",
        "--unit",
        unit,
        "--stage",
        "review-refine",
        "--summary",
        "Review passed.",
        "--head",
        head,
    )
    _cli(
        wt,
        "workflow",
        "envelope",
        "new",
        "--unit",
        unit,
        "--kind",
        "reconcile-check",
        "--stage",
        "living-spec-draft",
        "--summary",
        "Reconcile verified.",
        "--head",
        head,
    )
    _cli(
        wt,
        "workflow",
        "envelope",
        "new",
        "--unit",
        unit,
        "--kind",
        "feedback",
        "--stage",
        "collect-feedback",
        "--summary",
        "Sweep complete.",
        "--check",
        "swept=PASS 0 items",
    )
    _cli(
        wt,
        "workflow",
        "envelope",
        "new",
        "--unit",
        unit,
        "--kind",
        "final-report",
        "--stage",
        "final-change-report",
        "--summary",
        "All checks pass.",
        "--check",
        "tests=PASS pytest",
        "--check",
        "build=PASS build",
        "--check",
        "lint=PASS lint",
    )
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", "chore: record bugfix envelopes")
    return unit


def _complete_proposal(wt: Path, slug: str = "idea") -> str:
    unit = f"docs/proposals/PROP-{slug}"
    _cli(wt, "spec", "proposal", "new", slug, "--title", "Idea", "--summary", "Proposal summary.")
    _cli(
        wt, "workflow", "answer", "--unit", unit, "--request", "gate:plan-intent", "--action", "accept", "--by", "user"
    )
    _cli(
        wt,
        "workflow",
        "envelope",
        "new",
        "--unit",
        unit,
        "--kind",
        "feedback",
        "--stage",
        "collect-feedback",
        "--summary",
        "Sweep complete.",
        "--check",
        "swept=PASS 0 items",
    )
    prop_file = wt / unit / "proposal.md"
    prop_file.write_text(
        prop_file.read_text(encoding="utf-8").replace("status: draft", "status: accepted"),
        encoding="utf-8",
    )
    _cli(
        wt, "workflow", "answer", "--unit", unit, "--request", "gate:plan-accept", "--action", "accept", "--by", "user"
    )
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", "docs(proposal): accept proposal")
    return unit


def test_unit_readiness_passes_for_completed_feature_bugfix_and_proposal(tmp_path: Path, synced_template: Path) -> None:
    repo = _make_synced_repo(tmp_path / "f", synced_template)
    wt_feat = _start_worktree(repo, "dev-feat", tmp_path / "wt-feat")
    unit_feat = _complete_feature_spec(wt_feat, "feat")
    plan_feat = plan_finish(locate(repo), "dev-feat")
    ctx_feat = IntegrationContext(plan_feat, Task(kind="unit", id="SPEC-feat", unit=unit_feat))

    r1 = check(ctx_feat)
    r2 = check(ctx_feat)
    assert r1 == r2
    assert r1.reasons == ()
    codes = {item.code: item.value for item in r1.evidence}
    assert codes["TASK_KIND"] == "unit"
    assert codes["WORKFLOW"] == "sdd-spec-feature"
    assert codes["UNIT"] == unit_feat
    assert codes["HOLD_STATUS"] == "clear"
    assert codes["CI_RULES"] == "pass"

    wt_fix = _start_worktree(repo, "dev-fix", tmp_path / "wt-fix")
    unit_fix = _complete_bugfix_spec(wt_fix, "fix")
    plan_fix = plan_finish(locate(repo), "dev-fix")
    ctx_fix = IntegrationContext(plan_fix, Task(kind="unit", id="SPEC-fix", unit=unit_fix))
    r_fix = check(ctx_fix)
    assert r_fix.reasons == ()
    assert dict((e.code, e.value) for e in r_fix.evidence)["WORKFLOW"] == "sdd-spec-bugfix"

    wt_prop = _start_worktree(repo, "plan-idea", tmp_path / "wt-idea")
    unit_prop = _complete_proposal(wt_prop, "idea")
    plan_prop = plan_finish(locate(repo), "plan-idea")
    ctx_prop = IntegrationContext(plan_prop, Task(kind="unit", id="PROP-idea", unit=unit_prop))
    r_prop = check(ctx_prop)
    assert r_prop.reasons == ()
    assert dict((e.code, e.value) for e in r_prop.evidence)["WORKFLOW"] == "sdd-proposal"


def test_unit_readiness_refuses_incomplete_held_mismatched_or_ci_violating_units(
    tmp_path: Path, synced_template: Path
) -> None:
    repo = _make_synced_repo(tmp_path, synced_template)
    wt = _start_worktree(repo, "dev-feat", tmp_path / "wt-feat")
    unit = _complete_feature_spec(wt, "feat")

    # 1. Wrong task.id is refused with non-empty coded evidence.
    plan = plan_finish(locate(repo), "dev-feat")
    bad_id = check(IntegrationContext(plan, Task(kind="unit", id="SPEC-other", unit=unit)))
    assert bad_id.evidence and any("task.id" in reason for reason in bad_id.reasons)

    # 2. Unchecked task in tasks.md is refused.
    tasks_file = wt / unit / "tasks.md"
    tasks_file.write_text(tasks_file.read_text(encoding="utf-8").replace("- [x]", "- [ ]"), encoding="utf-8")
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", "uncheck task")
    plan_unchecked = plan_finish(locate(repo), "dev-feat")
    r_unchecked = check(IntegrationContext(plan_unchecked, Task(kind="unit", id="SPEC-feat", unit=unit)))
    assert r_unchecked.evidence and any("tasks-all-checked" in reason for reason in r_unchecked.reasons)

    # Restore tasks.md, add a failed worker envelope with an unresolved problem (hold).
    tasks_file.write_text(tasks_file.read_text(encoding="utf-8").replace("- [ ]", "- [x]"), encoding="utf-8")
    _cli(
        wt,
        "workflow",
        "envelope",
        "worker",
        "--unit",
        unit,
        "--stage",
        "build-verify",
        "--status",
        "failed",
        "--summary",
        "Blocked on contract.",
        "--problem",
        "Contract contradiction.",
        "--recovery",
        "Return to specify.",
        "--effort",
        "medium",
    )
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", "record blocked worker")
    plan_held = plan_finish(locate(repo), "dev-feat")
    r_held = check(IntegrationContext(plan_held, Task(kind="unit", id="SPEC-feat", unit=unit)))
    assert any("held" in reason for reason in r_held.reasons)

    # 3. Phase.CI rule violation (dangling SPEC-nonexistent reference) is refused.
    write(
        wt,
        "docs/capabilities/delivery/CAP-DLV-sample.md",
        "---\nid: CAP-DLV-sample\ntitle: Sample\nsummary: Sample capability.\nstatus: active\ncreated: 2026-10-01\nupdated: 2026-10-17\n---\n\n# [CAP-DLV-sample] Sample\n\n## 1. Overview\nReferences `SPEC-does-not-exist`.\n",
    )
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", "introduce broken doc reference")
    plan_ci = plan_finish(locate(repo), "dev-feat")
    r_ci = check(IntegrationContext(plan_ci, Task(kind="unit", id="SPEC-feat", unit=unit)))
    assert any("CI rule violation" in reason for reason in r_ci.reasons)

    with pytest.raises(ReadinessError):
        IntegrationService(repo).prepare("dev-feat", Task(kind="unit", id="SPEC-feat", unit=unit))


def test_session_readiness_verifies_claims_and_refuses_invalid_claims_or_plan_branch(
    tmp_path: Path, synced_template: Path
) -> None:
    repo = _make_synced_repo(tmp_path, synced_template)
    wt = _start_worktree(repo, "dev-quick", tmp_path / "wt-quick")
    write(wt, "src/app.py", "VALUE = 10\n")
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", "fix: quick session fix")
    plan = plan_finish(locate(repo), "dev-quick")

    valid_bugfix = Task(
        kind="session",
        id="quick",
        claims_json=json.dumps(
            {
                "task_kind": "bugfix",
                "effort": "low",
                "review": "passed",
                "tests": "PASS pytest",
                "lint": True,
                "reproduced": True,
                "resolved": True,
            }
        ),
    )
    r_ok = check(IntegrationContext(plan, valid_bugfix))
    assert r_ok.reasons == ()
    assert dict((e.code, e.value) for e in r_ok.evidence)["WORKFLOW"] == "sdd-session-bugfix"

    missing_repro = Task(
        kind="session",
        id="quick",
        claims_json=json.dumps(
            {
                "task_kind": "bugfix",
                "effort": "low",
                "review": True,
                "tests": True,
                "lint": True,
            }
        ),
    )
    r_bad = check(IntegrationContext(plan, missing_repro))
    assert any("reproduced" in reason for reason in r_bad.reasons)

    # A plan-<slug> branch cannot be integrated as a session task.
    wt_plan = _start_worktree(repo, "plan-quick", tmp_path / "wt-plan-quick")
    write(wt_plan, "src/app.py", "VALUE = 11\n")
    git(wt_plan, "add", "-A")
    git(wt_plan, "commit", "-q", "-m", "plan edit")
    plan_branch = plan_finish(locate(repo), "plan-quick")
    r_plan = check(IntegrationContext(plan_branch, valid_bugfix))
    assert any("dev-<slug>" in reason for reason in r_plan.reasons)

    # Touching an unaccepted proposal unit on a session branch is also refused.
    write(
        wt,
        "docs/proposals/PROP-other/proposal.md",
        "---\nid: PROP-other\ntitle: Other\nsummary: Draft.\nstatus: draft\ncreated: 2026-10-17\nupdated: 2026-10-17\n---\n\n# [PROP-other] Other\n\n## 1. Summary\nDraft.\n",
    )
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", "touch draft proposal")
    plan_touched_prop = plan_finish(locate(repo), "dev-quick")
    r_prop = check(IntegrationContext(plan_touched_prop, valid_bugfix))
    assert any("touched proposal unit docs/proposals/PROP-other is not accepted" in reason for reason in r_prop.reasons)


def test_integration_service_end_to_end_approval_cleanup_non_approval_and_no_network(
    tmp_path: Path, synced_template: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _make_synced_repo(tmp_path, synced_template)
    (repo / "docs/proposals/PROP-feat/decisions").mkdir(parents=True)
    wt = _start_worktree(repo, "dev-feat", tmp_path / "wt-feat")
    unit = _complete_feature_spec(wt, "feat")
    assert "[SCOPE: SPEC-feat " in _cli(wt, "spec", "scope", "register", "--spec", unit)

    # Forbid any git network subcommand (fetch, push, ls-remote) during prepare and integrate.
    real_run_git = core_git.run_git

    def _no_network_git(root: Path, *args: str, **kwargs: object) -> bytes:
        assert not ({"fetch", "push", "ls-remote"} & set(args)), f"unexpected network git call: {args}"
        return real_run_git(root, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(core_git, "run_git", _no_network_git)

    service = IntegrationService(repo)
    task = Task(kind="unit", id="SPEC-feat", unit=unit)

    # 1. Declined / unapproved confirmation leaves worktree, branch, base, and scope record untouched.
    async def _decline(_msg: str, _schema: dict) -> ConfirmationReply:
        return ConfirmationReply(action="decline", content={"approve": False})

    declined = asyncio.run(service.integrate("dev-feat", task, _decline))
    assert declined.status == "declined"
    assert wt.is_dir()
    assert "SPEC-feat" in _cli(repo, "spec", "scope", "query")

    # 2. Affirmative confirmation fast-forwards base, removes worktree & branch, prunes proposal dir, sweeps scope record.
    async def _accept(_msg: str, _schema: dict) -> ConfirmationReply:
        return ConfirmationReply(action="accept", content={"approve": True})

    completed = asyncio.run(service.integrate("dev-feat", task, _accept))
    assert completed.status == "completed", completed.to_dict()
    assert completed.authority == "mcp-elicitation"
    assert completed.steps["merge"] == "completed"
    assert completed.steps["worktree_remove"] == "completed"
    assert completed.steps["branch_delete"] == "completed"
    assert completed.steps["post_finish"] == "completed"
    assert completed.cleanup_steps == {"spec": "completed"}
    assert not wt.exists()
    assert not (repo / "docs/proposals/PROP-feat").exists()
    assert "SPEC-feat" not in _cli(repo, "spec", "scope", "query")


def test_integration_service_respects_delete_branch_false_and_pull_request_required(
    tmp_path: Path, synced_template: Path
) -> None:
    repo = _make_synced_repo(
        tmp_path / "keep",
        synced_template,
        extra_config="[worktree]\ndelete_branch = false\n",
    )
    wt = _start_worktree(repo, "dev-feat", tmp_path / "wt-keep")
    unit = _complete_feature_spec(wt, "feat")
    service = IntegrationService(repo)
    task = Task(kind="unit", id="SPEC-feat", unit=unit)

    async def _accept(_msg: str, _schema: dict) -> ConfirmationReply:
        return ConfirmationReply(action="accept", content={"approve": True})

    res = asyncio.run(service.integrate("dev-feat", task, _accept))
    assert res.status == "completed"
    assert res.steps["branch_delete"] == "skipped"
    assert res.steps["marker_clear"] == "completed"
    assert git(repo, "rev-parse", "--verify", "refs/heads/dev-feat") == res.request.context.finish.source_sha

    # pull_request = "required" fails closed during prepare.
    pr_repo = _make_synced_repo(
        tmp_path / "pr",
        synced_template,
        extra_config='[worktree]\npull_request = "required"\n',
    )
    wt_pr = _start_worktree(pr_repo, "dev-feat", tmp_path / "wt-pr")
    unit_pr = _complete_feature_spec(wt_pr, "feat")
    with pytest.raises(PullRequestPolicyError):
        IntegrationService(pr_repo).prepare("dev-feat", Task(kind="unit", id="SPEC-feat", unit=unit_pr))


def test_integration_service_partial_post_finish_and_resume(tmp_path: Path, synced_template: Path) -> None:
    repo = _make_synced_repo(tmp_path, synced_template)
    locked = repo / "docs/proposals/PROP-feat/decisions/locked"
    locked.mkdir(parents=True)
    wt = _start_worktree(repo, "dev-feat", tmp_path / "wt-feat")
    unit = _complete_feature_spec(wt, "feat")
    assert "[SCOPE: SPEC-feat " in _cli(wt, "spec", "scope", "register", "--spec", unit)

    service = IntegrationService(repo)
    task = Task(kind="unit", id="SPEC-feat", unit=unit)

    async def _accept(_msg: str, _schema: dict) -> ConfirmationReply:
        return ConfirmationReply(action="accept", content={"approve": True})

    locked.chmod(0)
    try:
        partial = asyncio.run(service.integrate("dev-feat", task, _accept))
    finally:
        locked.chmod(0o755)

    assert partial.status == "partial"
    assert partial.failing_operation == "post_finish"
    assert partial.steps["merge"] == "completed"
    assert partial.cleanup_steps == {"spec": "failed"}
    # Scope record was still swept even though proposal prune failed.
    assert "SPEC-feat" not in _cli(repo, "spec", "scope", "query")

    resumed = service.resume(partial.request.id)
    assert resumed.status == "completed"
    assert resumed.steps["post_finish"] == "completed"
    assert resumed.cleanup_steps == {"spec": "completed"}
    assert not (repo / "docs/proposals/PROP-feat").exists()
    assert providers.provider("spec")[1] is not None
