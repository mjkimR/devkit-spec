"""Feedback config validation and the agent-facing effective policy contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from conftest import Write
from devkit.cli import cli as devkit_cli

from devkit_spec.config import FEEDBACK_CHOICES, FeedbackConfig, read_spec_config
from devkit_spec.errors import SpecConfigError


def test_missing_and_empty_tables_use_repository_defaults(workspace: Path, write: Write) -> None:
    assert read_spec_config(workspace).feedback == FeedbackConfig()
    write(".devkit/config.toml", "[tool.spec.feedback]\n")
    assert read_spec_config(workspace).feedback == FeedbackConfig()


@pytest.mark.parametrize("key,value", [(key, value) for key, values in FEEDBACK_CHOICES.items() for value in values])
def test_each_supported_choice(workspace: Path, write: Write, key: str, value: str) -> None:
    write(".devkit/config.toml", f'[tool.spec.feedback]\n{key} = "{value}"\n')
    config = read_spec_config(workspace).feedback
    assert getattr(config, key) == value
    for other in FEEDBACK_CHOICES:
        if other != key:
            assert getattr(config, other) == getattr(FeedbackConfig(), other)


@pytest.mark.parametrize("key", list(FEEDBACK_CHOICES))
@pytest.mark.parametrize("value", ['"invalid"', '""', '"REPO"', "true", "1", "[]", "{}"])
def test_invalid_choices_fail_with_advisory(workspace: Path, write: Write, key: str, value: str) -> None:
    write(".devkit/config.toml", f"[tool.spec.feedback]\n{key} = {value}\n")
    with pytest.raises(SpecConfigError, match=rf"tool\.spec\.feedback\.{key}"):
        read_spec_config(workspace)
    result = CliRunner().invoke(devkit_cli, ["spec", "policy", "-w", str(workspace), "--format", "json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["error"]["code"] == "SPEC_CONFIG_INVALID"


@pytest.mark.parametrize(
    "body", ["[tool.spec]\nfeedback = true", "[tool.spec]\nfeedback = []", "[tool.spec.feedback]\nenabled = true"]
)
def test_invalid_shape_or_unknown_keys(workspace: Path, write: Write, body: str) -> None:
    write(".devkit/config.toml", body + "\n")
    with pytest.raises(SpecConfigError, match=r"tool\.spec\.feedback"):
        read_spec_config(workspace)


def test_policy_exposes_configured_values_alongside_stage_switch(workspace: Path, write: Write) -> None:
    write(
        ".devkit/config.toml",
        '[workflow.stages]\ncollect-feedback = "off"\n'
        '[tool.spec.feedback]\ncapture = "requested-only"\ncoverage = "repo-and-upstream"\n'
        'detail = "detailed"\nreminder = "off"\n',
    )
    runner = CliRunner()
    args = ["spec", "policy", "-w", str(workspace)]
    result = runner.invoke(devkit_cli, args)
    assert result.exit_code == 0
    assert "[STAGE_POLICY: collect-feedback state=off]" in result.stdout
    assert result.stdout.splitlines()[-1] == (
        "[FEEDBACK_POLICY: capture=requested-only coverage=repo-and-upstream detail=detailed reminder=off]"
    )
    result = runner.invoke(devkit_cli, [*args, "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["feedback"] == {
        "capture": "requested-only",
        "coverage": "repo-and-upstream",
        "detail": "detailed",
        "reminder": "off",
    }
    assert payload["stages_off"] == ["collect-feedback"]
