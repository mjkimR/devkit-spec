"""The delivery workflows and role contracts the ``spec`` bundle ships, as ``devkit workflow`` sees them after sync."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

WORKFLOWS = ("s-lane", "direct-delivery", "bugfix", "incubated-delivery")
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


def test_a_direct_delivery_unit_is_a_spec_bundle_that_starts_at_the_intent_gate(synced: Path) -> None:
    created = _devkit(
        "workflow", "new", "login", "--workflow", "direct-delivery", "--date", "2026-01-15", "-w", str(synced)
    )
    assert created.returncode == 0, created.stderr
    unit = synced / "specs/2026-01/20260115-login"
    assert (unit / "spec.md").is_file(), created.stdout
    assert "workflow: direct-delivery" in (unit / "spec.md").read_text(encoding="utf-8")

    step = _devkit("workflow", "next", "--unit", str(unit), "-w", str(synced))
    assert step.returncode == 0, step.stderr
    assert "[STAGE: intent human_gate=intent" in step.stdout
    assert "[WAITING: human gate:intent]" in step.stdout


def test_an_incubated_delivery_unit_is_a_proposal_bundle(synced: Path) -> None:
    created = _devkit("workflow", "new", "idea", "--workflow", "incubated-delivery", "-w", str(synced))
    assert created.returncode == 0, created.stderr
    unit = synced / "docs/proposals/PROP-idea"
    assert (unit / "proposal.md").is_file(), created.stdout

    step = _devkit("workflow", "next", "--unit", str(unit), "-w", str(synced))
    assert step.returncode == 0, step.stderr
    assert "[STAGE: intent-proposal human_gate=intent" in step.stdout


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_the_integration_gate_is_answered_by_given(workflow: str) -> None:
    text = (Path(__file__).resolve().parents[1] / f"src/devkit_spec/bundle/workflows/{workflow}.md").read_text("utf-8")
    data = yaml.safe_load(text.split("---\n", 2)[1])
    gates = {stage.get("human_gate") for stage in data["stages"]}
    expected = {"integration": {"answer": "given"}} if "integration" in gates else None
    assert data.get("gates") == expected
