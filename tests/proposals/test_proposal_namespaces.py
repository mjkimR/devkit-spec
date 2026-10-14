from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from conftest import Write
from devkit.cli import cli as devkit_cli
from devkit.core.errors import ArgumentError
from devkit.core.frontmatter import parse
from proposals.support import TODAY, accept, spec_dir

from devkit_spec.errors import ProposalInvalidError, SpecConfigError
from devkit_spec.proposals import create_proposal, create_spec, handoff_proposal

CONFIG = '[[tool.spec.namespaces]]\nname = "api"\npath = "services/api"\n'


def _meta(path: Path) -> dict[str, object]:
    data = parse(path.read_text(encoding="utf-8")).data
    assert data is not None
    return data


def test_proposal_and_spec_record_the_namespace(workspace: Path, write: Write) -> None:
    write(".devkit/config.toml", CONFIG)
    proposal = workspace / create_proposal(workspace, "a", namespace="api", today=TODAY).path
    assert "target_area: capabilities/<area>/\nnamespace: api\npriority: high" in proposal.read_text()
    assert _meta(workspace / create_proposal(workspace, "b", namespace="global", today=TODAY).path)["namespace"] == (
        "global"
    )
    assert "namespace" not in _meta(workspace / create_proposal(workspace, "c", today=TODAY).path)

    spec = spec_dir(workspace, "d") / "spec.md"
    create_spec(workspace, "d", namespace="api", day=TODAY)
    assert _meta(spec)["namespace"] == "api"
    assert f"created: {TODAY.isoformat()}\nnamespace: api\n" in spec.read_text()
    create_spec(workspace, "e", day=TODAY)
    assert "namespace" not in _meta(spec_dir(workspace, "e") / "spec.md")


def test_unknown_namespace_is_an_argument_error(workspace: Path, write: Write) -> None:
    with pytest.raises(ArgumentError) as raised:
        create_proposal(workspace, "a", namespace="api", today=TODAY)
    assert str(raised.value.advisory.fix).startswith("Pass one of global (registered in")
    write(".devkit/config.toml", CONFIG)
    with pytest.raises(ArgumentError) as raised:
        create_spec(workspace, "b", namespace="web", day=TODAY)
    assert raised.value.target_files == ("--namespace",) and "global, api" in str(raised.value.advisory.fix)
    assert not (workspace / "docs/proposals").exists() and not (workspace / "specs").exists()


def test_global_needs_no_registry(workspace: Path, write: Write) -> None:
    write(".devkit/config.toml", "[tool.spec]\nnamespaces = 3\n")
    create_spec(workspace, "a", namespace="global", day=TODAY)
    with pytest.raises(SpecConfigError):
        create_spec(workspace, "b", namespace="api", day=TODAY)


def test_cli_namespace_option(workspace: Path, write: Write) -> None:
    write(".devkit/config.toml", CONFIG)
    runner = CliRunner()
    result = runner.invoke(devkit_cli, ["spec", "proposal", "new", "a", "--namespace", "api", "-w", str(workspace)])
    assert result.exit_code == 0, result.output
    assert _meta(workspace / "docs/proposals/PROP-a/proposal.md")["namespace"] == "api"
    result = runner.invoke(
        devkit_cli, ["spec", "new", "b", "--namespace", "web", "--format", "json", "-w", str(workspace)]
    )
    assert result.exit_code == 2
    assert json.loads(result.stdout)["error"]["code"] == "ARGUMENT_INVALID"
    result = runner.invoke(devkit_cli, ["spec", "new", "b", "--namespace", "api", "-w", str(workspace)])
    assert result.exit_code == 0, result.output


def test_handoff_carries_the_namespace(workspace: Path, write: Write) -> None:
    write(".devkit/config.toml", CONFIG)
    proposal = workspace / create_proposal(workspace, "a", namespace="api", today=TODAY).path
    accept(proposal)
    handoff_proposal(workspace, "a", today=TODAY)
    assert _meta(spec_dir(workspace, "a") / "spec.md")["namespace"] == "api"

    plain = workspace / create_proposal(workspace, "b", today=TODAY).path
    accept(plain)
    handoff_proposal(workspace, "b", today=TODAY)
    assert "namespace" not in _meta(spec_dir(workspace, "b") / "spec.md")


@pytest.mark.parametrize("value", ["web", "3", "[api]"])
def test_handoff_refuses_an_unknown_namespace(workspace: Path, write: Write, value: str) -> None:
    write(".devkit/config.toml", CONFIG)
    proposal = workspace / create_proposal(workspace, "a", today=TODAY).path
    accept(proposal, f"\nnamespace: {value}")
    with pytest.raises(ProposalInvalidError) as raised:
        handoff_proposal(workspace, "a", today=TODAY)
    assert raised.value.target_files == ("docs/proposals/PROP-a/proposal.md",)
    assert "global, api" in str(raised.value.advisory.fix)
    assert proposal.is_file() and not (workspace / "specs").exists()


def _new(workspace: Path, *args: str) -> list[str]:
    result = CliRunner().invoke(devkit_cli, ["spec", *args, "-w", str(workspace)])
    assert result.exit_code == 0, result.output
    return result.stdout.splitlines()


def test_new_bundles_take_the_namespace_of_the_current_directory(
    workspace: Path, write: Write, monkeypatch: pytest.MonkeyPatch
) -> None:
    write(".devkit/config.toml", CONFIG)
    (workspace / "services/api/src").mkdir(parents=True)
    monkeypatch.chdir(workspace / "services/api/src")
    lines = _new(workspace, "new", "--date", TODAY.isoformat(), "rate-limits")
    assert lines[0].startswith("[SPEC: SPEC-rate-limits path=") and lines[0].endswith(" namespace=api]")
    assert _meta(spec_dir(workspace, "rate-limits") / "spec.md")["namespace"] == "api"
    assert (
        json.loads("\n".join(_new(workspace, "new", "--date", TODAY.isoformat(), "quotas", "--format", "json")))[
            "namespace"
        ]
        == "api"
    )

    (workspace / "docs/packages/api").mkdir(parents=True)
    monkeypatch.chdir(workspace / "docs/packages/api")
    lines = _new(workspace, "proposal", "new", "throttle")
    assert lines[0].startswith("[PROPOSAL: PROP-throttle ") and lines[0].endswith(" namespace=api]")
    proposal = workspace / "docs/proposals/PROP-throttle/proposal.md"
    assert _meta(proposal)["namespace"] == "api"
    accept(proposal)
    handoff_proposal(workspace, "throttle", today=TODAY)
    assert _meta(spec_dir(workspace, "throttle") / "spec.md")["namespace"] == "api"


@pytest.mark.parametrize("where", ["root", "outside"])
def test_outside_every_package_the_bundle_stays_global(
    workspace: Path, write: Write, monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory, where: str
) -> None:
    write(".devkit/config.toml", CONFIG)
    monkeypatch.chdir(workspace if where == "root" else tmp_path_factory.mktemp("elsewhere"))
    lines = _new(workspace, "new", "--date", TODAY.isoformat(), "a")
    assert lines[0].endswith(" workflow=- namespace=global]")
    assert "namespace" not in _meta(spec_dir(workspace, "a") / "spec.md")
    created = json.loads("\n".join(_new(workspace, "proposal", "new", "b", "--format", "json")))
    assert created["namespace"] == "global"
    assert "namespace" not in _meta(workspace / "docs/proposals/PROP-b/proposal.md")


def test_without_registered_namespaces_nothing_is_reported(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(workspace)
    assert "namespace=" not in _new(workspace, "new", "--date", TODAY.isoformat(), "a")[0]
    assert json.loads("\n".join(_new(workspace, "proposal", "new", "b", "--format", "json")))["namespace"] is None


def test_an_explicit_namespace_wins_over_the_current_directory(
    workspace: Path, write: Write, monkeypatch: pytest.MonkeyPatch
) -> None:
    write(".devkit/config.toml", CONFIG)
    (workspace / "services/api").mkdir(parents=True)
    monkeypatch.chdir(workspace / "services/api")
    assert _new(workspace, "new", "--date", TODAY.isoformat(), "a", "--namespace", "global")[0].endswith(
        " namespace=global]"
    )
    assert _meta(spec_dir(workspace, "a") / "spec.md")["namespace"] == "global"
    assert _new(workspace, "proposal", "new", "b", "--namespace", "global")[0].endswith(" namespace=global]")
    assert _meta(workspace / "docs/proposals/PROP-b/proposal.md")["namespace"] == "global"
    result = CliRunner().invoke(
        devkit_cli, ["spec", "new", "c", "--namespace", "web", "--date", TODAY.isoformat(), "-w", str(workspace)]
    )
    assert result.exit_code == 2 and "ARGUMENT_INVALID" in result.output
