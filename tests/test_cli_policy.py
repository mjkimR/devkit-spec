from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner, Result
from conftest import Write
from devkit.cli import cli as devkit_cli

from devkit_spec.config import SpecConfig, read_spec_config
from devkit_spec.errors import SpecConfigError


def _policy(workspace: Path, *args: str) -> Result:
    return CliRunner().invoke(devkit_cli, ["spec", "policy", "-w", str(workspace), *args])


def test_defaults(workspace: Path) -> None:
    result = _policy(workspace)
    assert result.exit_code == 0
    assert result.stdout.splitlines() == [
        "[GATE_POLICY: plan-intent policy=ask source=fixed]",
        "[GATE_POLICY: plan-accept policy=ask source=fixed]",
        "[GATE_POLICY: dev-integration policy=ask source=default]",
        "[GIT_POLICY: worktree=auto pull_request=auto delete_branch=yes setup=-]",
        "[ROUTING_POLICY: depth_escalation=auto]",
        "[FEEDBACK_POLICY: capture=observed coverage=repo detail=standard reminder=contextual]",
    ]


def test_configured(workspace: Path, write: Write) -> None:
    write(
        ".devkit/config.toml",
        '[workflow.approvals]\ndev-integration = "auto"\nhandoff = "off"\n[workflow.stages]\ncollect-feedback = "off"\n'
        '[worktree]\npull_request = "required"\nsetup = "uv sync"\n[tool.spec]\nworktree = "required"\n'
        'depth_escalation = "ask"\n',
    )
    lines = _policy(workspace).stdout.splitlines()
    assert "[GATE_POLICY: dev-integration policy=auto source=config]" in lines
    assert "[GATE_POLICY: handoff policy=off source=config]" in lines
    assert "[STAGE_POLICY: collect-feedback state=off]" in lines
    assert lines[-3] == '[GIT_POLICY: worktree=required pull_request=required delete_branch=yes setup="uv sync"]'
    assert lines[-2] == "[ROUTING_POLICY: depth_escalation=ask]"
    payload = json.loads(_policy(workspace, "--format", "json").stdout)
    assert payload["git"] == {
        "worktree": "required",
        "pull_request": "required",
        "delete_branch": True,
        "setup": "uv sync",
    }
    assert payload["stages_off"] == ["collect-feedback"]
    assert payload["routing"] == {"depth_escalation": "ask"}


@pytest.mark.parametrize(
    "approvals",
    ['plan-intent = "auto"', 'plan-accept = "ask"', 'dev-integration = "off"'],
)
def test_a_person_decides_plan_gates_and_integration_is_never_skipped(
    workspace: Path, write: Write, approvals: str
) -> None:
    write(".devkit/config.toml", f"[workflow.approvals]\n{approvals}\n")
    result = _policy(workspace)
    assert result.exit_code == 2 and "SPEC_CONFIG_INVALID" in result.stderr


@pytest.mark.parametrize(
    "table",
    ['worktree = "yes"', "worktree = true", "worktree = false", 'depth_escalation = "never"', "other = 1", "spec = 1"],
)
def test_malformed_tool_spec(workspace: Path, write: Write, table: str) -> None:
    body = f"[tool.spec]\n{table}\n" if not table.startswith("spec") else f"[tool]\n{table}\n"
    write(".devkit/config.toml", body)
    with pytest.raises(Exception) as caught:
        read_spec_config(workspace)
    assert getattr(caught.value, "code", "") in ("SPEC_CONFIG_INVALID", "CONFIG_INVALID")
    result = _policy(workspace)
    assert result.exit_code == 2 and "CONFIG_INVALID" in result.stderr


def test_absent_table_is_the_default(workspace: Path) -> None:
    assert read_spec_config(workspace) == SpecConfig()
    assert SpecConfig().worktree == "auto" and SpecConfig().depth_escalation == "auto"


def test_a_boolean_pull_request_policy_stops_the_command(workspace: Path, write: Write) -> None:
    write(".devkit/config.toml", "[worktree]\npull_request = true\n")
    result = _policy(workspace)
    assert result.exit_code == 2 and "WORKTREE_CONFIG_INVALID" in result.stderr


def test_spec_config_error_is_a_config_error() -> None:
    from devkit.core.errors import ConfigError

    assert issubclass(SpecConfigError, ConfigError)
