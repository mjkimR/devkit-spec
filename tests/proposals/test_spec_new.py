from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner, Result
from conftest import Write
from devkit.cli import cli as devkit_cli
from devkit.core import FrontmatterError
from devkit.core.frontmatter import parse
from proposals.support import MONTH, STAMP, TODAY, WORKFLOW, spec_dir, write_workflow

from devkit_spec.errors import SpecExistsError, SpecSlugError, SpecWorkflowError, SpecWriteError
from devkit_spec.proposals import SKELETON_MARKER, create_proposal, create_spec


def _spec_new(workspace: Path, *args: str) -> Result:
    return CliRunner().invoke(devkit_cli, ["spec", "new", *args, "-w", str(workspace)])


def _meta(path: Path) -> dict[str, object]:
    data = parse(path.read_text(encoding="utf-8")).data
    assert data is not None
    return data


def test_creates_a_bound_bundle(workspace: Path) -> None:
    write_workflow(workspace, "direct-delivery")
    created = create_spec(workspace, "SPEC-Login Flow", title="Login: Flow", day=TODAY)
    target = spec_dir(workspace, "login-flow")
    assert created.to_dict() == {
        "id": "SPEC-login-flow",
        "dir": f"specs/{MONTH}/{STAMP}-login-flow",
        "workflow": "direct-delivery",
        "namespace": None,
        "next_command": f"devkit workflow next --unit specs/{MONTH}/{STAMP}-login-flow",
        "notices": [],
    }
    spec = _meta(target / "spec.md")
    assert spec["id"] == "SPEC-login-flow" and spec["title"] == "Login: Flow" and spec["status"] == "planned"
    assert spec["workflow"] == "direct-delivery" and str(spec["workflow_hash"]).startswith("sha256:")
    assert "kind" not in spec
    assert _meta(target / "plan.md") == {"id": "PLAN-login-flow", "spec": "SPEC-login-flow"}
    assert _meta(target / "tasks.md") == {
        "id": "TASKS-login-flow",
        "spec": "SPEC-login-flow",
        "plan": "PLAN-login-flow",
    }
    for name in ("spec.md", "plan.md", "tasks.md"):
        lines = (target / name).read_text(encoding="utf-8").split("\n")
        assert lines[lines.index("---", 1) + 1] == SKELETON_MARKER, name
    text = (target / "spec.md").read_text(encoding="utf-8")
    assert "Handed off" not in text and "Carried Proposal Notes" not in text
    assert "### [AC-01] <scenario>" in text
    assert "_Requirements: AC-01_" in (target / "tasks.md").read_text(encoding="utf-8")


def test_bugfix_carries_its_kind(workspace: Path) -> None:
    write_workflow(workspace, "bugfix")
    created = create_spec(workspace, "crash", workflow="bugfix", day=TODAY)
    target = spec_dir(workspace, "crash")
    spec = _meta(target / "spec.md")
    assert created.workflow == "bugfix" and spec["kind"] == "bugfix" and spec["workflow"] == "bugfix"
    # The bugfix workflow writes plan.md and tasks.md in its plan-tasks stage.
    assert sorted(path.name for path in target.iterdir()) == ["spec.md"]


@pytest.mark.parametrize("definition", [None, WORKFLOW.format(id="bugfix").replace("schema_version: 1", "")])
def test_an_unbindable_workflow_writes_nothing(workspace: Path, definition: str | None) -> None:
    if definition is not None:
        write_workflow(workspace, "bugfix", definition)
    with pytest.raises(SpecWorkflowError) as raised:
        create_spec(workspace, "crash", workflow="bugfix", day=TODAY)
    assert raised.value.code == "SPEC_WORKFLOW_INVALID"
    assert not (workspace / "specs").exists()


def test_without_the_default_workflow_the_spec_stays_unbound(workspace: Path) -> None:
    created = create_spec(workspace, "loose", day=TODAY)
    assert created.workflow is None and created.next_command is None
    assert [notice.code for notice in created.notices] == ["SPEC_UNBOUND"]
    assert "workflow" not in _meta(spec_dir(workspace, "loose") / "spec.md")


@pytest.mark.parametrize(
    ("error", "raised_type"), [(FrontmatterError("bad"), FrontmatterError), (RuntimeError("bug"), SpecWriteError)]
)
def test_any_failure_while_writing_is_rolled_back(
    workspace: Path, monkeypatch: pytest.MonkeyPatch, error: Exception, raised_type: type[Exception]
) -> None:
    write_workflow(workspace, "direct-delivery")

    def write_binding(*_: object) -> None:
        raise error

    monkeypatch.setattr("devkit_spec.proposals.specs.write_binding", write_binding)
    with pytest.raises(raised_type):
        create_spec(workspace, "broken", day=TODAY)
    assert not (workspace / "specs").exists()


def test_refuses_a_taken_slug(workspace: Path, write: Write) -> None:
    write("specs/2026-09/20260901-old/spec.md", "---\nid: SPEC-old\nstatus: completed\n---\n")
    with pytest.raises(SpecExistsError) as raised:
        create_spec(workspace, "old", day=TODAY)
    assert raised.value.target_files == ("specs/2026-09/20260901-old/spec.md",)
    create_proposal(workspace, "idea")
    with pytest.raises(SpecExistsError):
        create_spec(workspace, "idea", day=TODAY)
    write(f"specs/{MONTH}/{STAMP}-dir/notes.md", "x\n")
    with pytest.raises(SpecExistsError):
        create_spec(workspace, "dir", day=TODAY)
    with pytest.raises(SpecSlugError):
        create_spec(workspace, "!!", day=TODAY)
    assert not spec_dir(workspace, "old").exists() and not spec_dir(workspace, "idea").exists()


def test_cli(workspace: Path) -> None:
    write_workflow(workspace, "direct-delivery")
    result = _spec_new(workspace, "demo", "--date", "2026-09-02")
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines() == [
        "[SPEC: SPEC-demo path=specs/2026-09/20260902-demo workflow=direct-delivery]",
        "[NEXT_CMD: devkit workflow next --unit specs/2026-09/20260902-demo]",
    ]
    assert _meta(workspace / "specs/2026-09/20260902-demo/spec.md")["created"].isoformat() == "2026-09-02"  # type: ignore[union-attr]
    result = CliRunner().invoke(
        devkit_cli,
        ["workflow", "next", "--unit", "specs/2026-09/20260902-demo", "-w", str(workspace), "--format", "json"],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["stage"]["id"] == "specify"
    result = _spec_new(workspace, "demo", "--date", "2026-09-02", "--format", "json")
    assert result.exit_code == 2 and json.loads(result.stdout)["error"]["code"] == "SPEC_EXISTS"
    result = _spec_new(workspace, "other", "--workflow", "missing")
    assert result.exit_code == 2 and "(SPEC_WORKFLOW_INVALID)" in result.stderr


def _devkit(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("DEVKIT_")}
    return subprocess.run(
        [sys.executable, "-m", "devkit", *args, "-w", str(root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )


def test_a_new_bundle_passes_the_rules_and_starts_its_workflow(tmp_path: Path) -> None:
    """With the spec bundle synced: RULE-id-convention and the other rules accept it, and its workflow begins."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    assert _devkit(tmp_path, "sync").returncode == 0
    for args in (("demo",), ("crash", "--workflow", "bugfix")):
        result = _devkit(tmp_path, "spec", "new", *args, "--format", "json")
        assert result.returncode == 0, result.stdout + result.stderr
        unit = json.loads(result.stdout)["dir"]
        result = _devkit(tmp_path, "workflow", "next", "--unit", unit, "--format", "json")
        assert result.returncode == 0, result.stdout + result.stderr
        payload = json.loads(result.stdout)
        assert payload["workflow"] == ("bugfix" if "bugfix" in args else "direct-delivery")
        assert payload["stage"]["id"] == "intent"
    result = _devkit(tmp_path, "rules", "check")
    assert result.returncode == 0, result.stdout + result.stderr


def test_a_characterized_bugfix_bundle_passes_the_rules(tmp_path: Path) -> None:
    """A bugfix bundle has no tasks.md until plan-tasks, so its characterized spec.md alone is lint-clean."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    assert _devkit(tmp_path, "sync").returncode == 0
    result = _devkit(
        tmp_path,
        "spec",
        "new",
        "x",
        "--workflow",
        "bugfix",
        "--summary",
        "Saving an empty file works.",
        "--format",
        "json",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    unit = tmp_path / json.loads(result.stdout)["dir"]
    assert sorted(path.name for path in unit.iterdir()) == ["spec.md"]
    spec = unit / "spec.md"
    text = spec.read_text(encoding="utf-8").replace(SKELETON_MARKER + "\n", "")
    text = text.replace("### [AC-01] <scenario>", "### [AC-01] Saving an empty file no longer crashes")
    spec.write_text(text, encoding="utf-8")
    result = _devkit(tmp_path, "rules", "check", str(unit))
    assert result.returncode == 0, result.stdout + result.stderr
