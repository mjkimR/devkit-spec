"""Q20 (01 §5.1): a draft proposal whose plan-<slug> exists is listed as reviewing, and Backlog may not change it."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from devkit.cli import cli as devkit_cli
from proposals.support import TODAY, accept
from scope.support import git, write

from devkit_spec.proposals import create_proposal


def _repo(tmp_path: Path) -> Path:
    root = (tmp_path / "repo").resolve()
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    write(root, ".devkit/config.toml", "")
    for slug in ("local", "remote", "idle", "taken"):
        create_proposal(root, slug, today=TODAY)
    accept(root / create_proposal(root, "done", today=TODAY).path)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "proposals")
    git(root, "branch", "plan-local")
    git(root, "update-ref", "refs/remotes/origin/plan-remote", "HEAD")  # fetched from a remote
    return root


def _spec(root: Path, *args: str) -> object:
    return CliRunner().invoke(devkit_cli, ["spec", *args, "-w", str(root)])


def test_list_shows_a_draft_in_planning_as_reviewing_without_writing(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    result = CliRunner().invoke(devkit_cli, ["spec", "list", "proposal", "-w", str(root), "--format", "json"])
    shown = {d["id"]: d for d in json.loads(result.stdout)["documents"]}
    assert (shown["PROP-local"]["status"], shown["PROP-local"]["planning_branch"]) == ("reviewing", "plan-local")
    assert (shown["PROP-remote"]["status"], shown["PROP-remote"]["planning_branch"]) == (
        "reviewing",
        "origin/plan-remote",
    )
    assert shown["PROP-idle"]["status"] == "draft" and "planning_branch" not in shown["PROP-idle"]
    assert "status: draft" in (root / "docs/proposals/PROP-local/proposal.md").read_text()  # the base is unchanged
    text = CliRunner().invoke(devkit_cli, ["spec", "list", "proposal", "--status", "reviewing", "-w", str(root)])
    assert (
        "PROP-local" in text.stdout and "planning_branch=plan-local" in text.stdout and "PROP-idle" not in text.stdout
    )


def test_backlog_changes_only_a_draft_without_a_planning_branch(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    ok = CliRunner().invoke(devkit_cli, ["spec", "proposal", "check", "idle", "-w", str(root)])
    assert ok.exit_code == 0 and ok.stdout.startswith("[PROPOSAL: PROP-idle ") and "editable=yes" in ok.stdout
    for slug, reason in (
        ("local", "in Planning on plan-local"),
        ("remote", "on origin/plan-remote"),
        ("done", "accepted"),
    ):
        refused = CliRunner().invoke(
            devkit_cli, ["spec", "proposal", "check", slug, "-w", str(root), "--format", "json"]
        )
        error = json.loads(refused.stdout)["error"]
        assert refused.exit_code == 2 and error["code"] == "SPEC_PROPOSAL_IN_PLANNING" and reason in error["message"]
    missing = CliRunner().invoke(devkit_cli, ["spec", "proposal", "check", "nothing", "-w", str(root)])
    assert missing.exit_code == 2 and "SPEC_PROPOSAL_NOT_FOUND" in missing.stderr


def test_a_padr_of_a_proposal_in_planning_is_written_on_its_branch_only(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    for slug, branch in (("local", "plan-local"), ("remote", "origin/plan-remote")):
        refused = CliRunner().invoke(
            devkit_cli, ["spec", "proposal", "padr", slug, "Pick", "-w", str(root), "--format", "json"]
        )
        error = json.loads(refused.stdout)["error"]
        assert refused.exit_code == 2 and error["code"] == "SPEC_PROPOSAL_IN_PLANNING" and branch in error["message"]
        assert not (root / f"docs/proposals/PROP-{slug}/decisions/PADR-pick.md").exists()
    idle = CliRunner().invoke(devkit_cli, ["spec", "proposal", "padr", "idle", "Keep", "-w", str(root)])
    assert idle.exit_code == 0 and idle.stdout.startswith("[PADR: PADR-keep ")  # no Planning branch: Backlog may
    git(root, "switch", "-q", "plan-local")
    on_branch = CliRunner().invoke(devkit_cli, ["spec", "proposal", "padr", "local", "Pick", "-w", str(root)])
    assert on_branch.exit_code == 0 and on_branch.stdout.startswith("[PADR: PADR-pick "), on_branch.output
