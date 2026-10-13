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
        "[GATE_POLICY: intent policy=ask source=default]",
        "[GATE_POLICY: direction policy=ask source=default]",
        "[GATE_POLICY: integration policy=ask source=default]",
        "[GIT_POLICY: worktree=yes pull_request=no delete_branch=yes setup=-]",
    ]


def test_configured(workspace: Path, write: Write) -> None:
    write(
        ".devkit/config.toml",
        '[workflow.approvals]\ndirection = "auto"\nhandoff = "off"\n[workflow.stages]\ncollect-feedback = "off"\n'
        '[worktree]\npull_request = false\nsetup = "uv sync"\n[tool.spec]\nworktree = false\n',
    )
    lines = _policy(workspace).stdout.splitlines()
    assert "[GATE_POLICY: direction policy=auto source=config]" in lines
    assert "[GATE_POLICY: handoff policy=off source=config]" in lines
    assert "[STAGE_POLICY: collect-feedback state=off]" in lines
    assert lines[-1] == '[GIT_POLICY: worktree=no pull_request=no delete_branch=yes setup="uv sync"]'
    payload = json.loads(_policy(workspace, "--format", "json").stdout)
    assert payload["git"] == {"worktree": False, "pull_request": False, "delete_branch": True, "setup": "uv sync"}
    assert payload["stages_off"] == ["collect-feedback"]


@pytest.mark.parametrize("table", ['worktree = "yes"', "other = 1", "spec = 1"])
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


def test_spec_config_error_is_a_config_error() -> None:
    from devkit.core.errors import ConfigError

    assert issubclass(SpecConfigError, ConfigError)
