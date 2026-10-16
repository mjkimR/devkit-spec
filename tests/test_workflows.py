"""The delivery workflows and role contracts the ``spec`` bundle ships, as ``devkit workflow`` sees them after sync."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

WORKFLOWS = ("sdd-session-feature", "sdd-session-bugfix", "sdd-spec-feature", "sdd-spec-bugfix", "sdd-proposal")
GATES = {"plan-intent", "plan-accept", "dev-integration", False}
ROLES = ("challenger", "reconciler", "reviewer", "scout")
AGENT_FILES = (".claude/agents/{role}.md", ".codex/agents/{role}.toml", ".agents/agents/{role}.md")


def _devkit(*args: str) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("DEVKIT_")}
    return subprocess.run(
        [sys.executable, "-m", "devkit", *args], capture_output=True, text=True, encoding="utf-8", env=env, check=False
    )


@pytest.fixture(scope="module")
def synced(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("synced")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    result = _devkit("sync", "-w", str(root))
    assert result.returncode == 0, result.stderr
    return root


def test_the_workflows_validate_with_roles_checked_and_shared_stages_equal(synced: Path) -> None:
    result = _devkit("workflow", "validate", "-w", str(synced), "--format", "json")
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["ok"] and report["roles_checked"], report
    assert not report["errors"] and not report["notices"], report
    assert sorted(item["id"] for item in report["definitions"]) == sorted(WORKFLOWS)
    assert "SHARED_STAGE_MISMATCH" not in result.stdout and "WORKFLOW_ROLES_UNCHECKED" not in result.stdout


def test_every_role_is_projected_for_every_agent(synced: Path) -> None:
    for role in ROLES:
        assert (synced / f".devkit/managed/spec/subagents/{role}.md").is_file()
        for pattern in AGENT_FILES:
            assert (synced / pattern.format(role=role)).is_file(), pattern.format(role=role)


@pytest.mark.parametrize("worker", ["development-worker", "planning-worker"])
def test_a_worker_is_projected_only_where_it_can_reach_a_worktree(synced: Path, worker: str) -> None:
    assert (synced / f".devkit/managed/spec/subagents/{worker}.md").is_file()
    assert (synced / f".claude/agents/{worker}.md").is_file()
    assert (synced / f".agents/agents/{worker}.md").is_file()
    assert not (synced / f".codex/agents/{worker}.toml").exists()


def test_no_skill_is_projected_for_a_procedure_only_a_role_runs(synced: Path) -> None:
    for skill in ("spec-scout", "spec-challenge"):
        assert not (synced / f".claude/skills/{skill}").exists(), skill
        assert not (synced / f".agents/skills/{skill}").exists(), skill
    assert (synced / ".claude/agents/scout.md").read_text(encoding="utf-8").count("\n## Procedure\n") == 1


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_show_renders_each_workflow(synced: Path, workflow: str) -> None:
    result = _devkit("workflow", "show", workflow, "-w", str(synced))
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.startswith(f"[WORKFLOW: {workflow} ")


@pytest.mark.parametrize("workflow", ["sdd-spec-feature", "sdd-spec-bugfix"])
def test_a_spec_unit_is_a_spec_bundle_that_starts_at_the_plan_intent_gate(synced: Path, workflow: str) -> None:
    slug = workflow.removeprefix("sdd-spec-")
    created = _devkit("workflow", "new", slug, "--workflow", workflow, "--date", "2026-01-15", "-w", str(synced))
    assert created.returncode == 0, created.stderr
    unit = synced / f"specs/2026-01/20260115-{slug}"
    assert (unit / "spec.md").is_file(), created.stdout
    assert f"workflow: {workflow}" in (unit / "spec.md").read_text(encoding="utf-8")

    step = _devkit("workflow", "next", "--unit", str(unit), "-w", str(synced))
    assert step.returncode == 0, step.stderr
    assert "[STAGE: intent human_gate=plan-intent" in step.stdout
    assert "[WAITING: human gate:plan-intent]" in step.stdout


def test_a_proposal_unit_is_a_proposal_bundle(synced: Path) -> None:
    created = _devkit("workflow", "new", "idea", "--workflow", "sdd-proposal", "-w", str(synced))
    assert created.returncode == 0, created.stderr
    unit = synced / "docs/proposals/PROP-idea"
    assert (unit / "proposal.md").is_file(), created.stdout

    step = _devkit("workflow", "next", "--unit", str(unit), "-w", str(synced))
    assert step.returncode == 0, step.stderr
    assert "[STAGE: intent-proposal human_gate=plan-intent" in step.stdout


def _definition(workflow: str) -> dict[str, object]:
    text = (Path(__file__).resolve().parents[1] / f"src/devkit_spec/bundle/workflows/{workflow}.md").read_text("utf-8")
    return yaml.safe_load(text.split("---\n", 2)[1])


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_the_gates_fix_their_policies_and_integration_is_answered_by_given(workflow: str) -> None:
    data = _definition(workflow)
    gates = {stage.get("human_gate") for stage in data["stages"]}  # type: ignore[union-attr]
    expected: dict[str, dict[str, object]] = {}
    for gate in ("plan-intent", "plan-accept"):  # always a person (01 §3): configuration cannot pass them
        if gate in gates:
            expected[gate] = {"policies": ["ask"]}
    if "dev-integration" in gates:  # ask or auto; off would skip integration
        expected["dev-integration"] = {"answer": "given", "policies": ["ask", "auto"]}
    assert data.get("gates") == expected


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_only_the_three_named_gates_are_used_and_development_has_no_direction_gate(workflow: str) -> None:
    stages = _definition(workflow)["stages"]
    assert {stage.get("human_gate") for stage in stages} <= GATES  # type: ignore[union-attr]
    assert "direction" not in {stage["id"] for stage in stages}  # type: ignore[union-attr]
    names = " ".join(str(stage["name"]) for stage in stages)  # type: ignore[union-attr]
    assert not any(token in names.split() for token in ("G1", "G2", "G3", "E"))
    for stage in stages:  # type: ignore[union-attr]
        assert all(ret["to"] != "direction" for ret in stage.get("returns", [])), stage["id"]


@pytest.mark.parametrize("workflow", ["sdd-session-feature", "sdd-session-bugfix"])
def test_a_session_requires_no_unit_envelope_spec_or_reconcile_artifact(workflow: str) -> None:
    data = _definition(workflow)
    assert "layout" not in data
    for stage in data["stages"]:  # type: ignore[union-attr]
        checks = " ".join([*stage["entry"], *stage["exit"]])
        assert not any(word in checks for word in ("envelope", "spec.md", "reconcile", "anchor", "tasks")), stage
        assert not any("envelopes/" in str(item) or "reconcile" in str(item) for item in stage["artifacts"]), stage


def test_the_session_bugfix_reproduces_before_it_fixes() -> None:
    order = [stage["id"] for stage in _definition("sdd-session-bugfix")["stages"]]  # type: ignore[union-attr]
    assert order.index("reproduce-session") < order.index("execute-verify")
    feature = [stage["id"] for stage in _definition("sdd-session-feature")["stages"]]  # type: ignore[union-attr]
    assert [stage for stage in order if stage != "reproduce-session"] == feature


def test_plan_accept_is_asked_only_for_a_proposal_in_review() -> None:
    stage = next(s for s in _definition("sdd-proposal")["stages"] if s["id"] == "direction-handoff")  # type: ignore[union-attr]
    assert stage["human_gate"] == "plan-accept"
    assert stage["exit"] == ["frontmatter(proposal.md status reviewing|accepted)"]
