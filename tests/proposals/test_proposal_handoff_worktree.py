"""The handoff branch guard: the checkout must be on ``dev-<slug>``, linked or base, at either worktree level."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from devkit.cli import cli as devkit_cli
from proposals.support import TODAY, accept, spec_dir
from scope.support import git, write

from devkit_spec.errors import ProposalWrongWorktreeError
from devkit_spec.proposals import create_proposal, handoff_proposal

SLUG = "rate-limits"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A committed repository holding an accepted proposal of ``SLUG``."""
    root = (tmp_path / "repo").resolve()
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    write(root, ".devkit/config.toml", "")
    accept(root / create_proposal(root, SLUG, today=TODAY).path)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "proposal")
    return root


def _worktree(repo: Path, name: str, *args: str) -> Path:
    path = repo.parent / f"wt-{name}"
    git(repo, "worktree", "add", "-q", *args, str(path))
    return path


@pytest.mark.parametrize("detached", [False, True])
def test_a_handoff_in_another_tasks_worktree_is_refused_before_writing(repo: Path, detached: bool) -> None:
    linked = _worktree(repo, "other", "--detach") if detached else _worktree(repo, "other", "-b", "other-task")
    result = CliRunner().invoke(devkit_cli, ["spec", "proposal", "handoff", SLUG, "-w", str(linked)])
    assert result.exit_code == 2 and result.stdout == ""
    assert "SPEC_PROPOSAL_WRONG_WORKTREE" in result.stderr
    branch = "- (detached HEAD)" if detached else "other-task"
    assert f"in the worktree of branch {branch}; it runs on branch dev-{SLUG}" in result.stderr
    assert f"devkit worktree start dev-{SLUG}" in result.stderr
    assert (linked / f"docs/proposals/PROP-{SLUG}/proposal.md").is_file() and not (linked / "specs").exists()

    result = CliRunner().invoke(
        devkit_cli, ["spec", "proposal", "handoff", SLUG, "--format", "json", "-w", str(linked)]
    )
    assert json.loads(result.stdout)["error"]["code"] == "SPEC_PROPOSAL_WRONG_WORKTREE"


def test_the_development_branch_of_the_slug_hands_off(repo: Path) -> None:
    plain = _worktree(repo, SLUG, "-b", SLUG)  # the bare slug is not an activity branch
    with pytest.raises(ProposalWrongWorktreeError):
        handoff_proposal(plain, SLUG, today=TODAY)
    linked = _worktree(repo, f"dev-{SLUG}", "-b", f"dev-{SLUG}")
    result = CliRunner().invoke(devkit_cli, ["spec", "proposal", "handoff", SLUG, "-w", str(linked)])
    assert result.exit_code == 0, result.output
    assert result.stdout.startswith(f"[HANDOFF: PROP-{SLUG} spec=SPEC-{SLUG} ")


def test_the_base_checkout_is_guarded_too(repo: Path) -> None:
    with pytest.raises(ProposalWrongWorktreeError, match="in the checkout of branch main"):
        handoff_proposal(repo, SLUG, today=TODAY)  # the accepted proposal would be deleted from the base itself
    assert not (repo / "specs").exists()
    git(repo, "checkout", "-q", "-b", f"dev-{SLUG}")  # devkit worktree start dev-<slug> --no-worktree
    handoff_proposal(repo, SLUG, today=TODAY)
    assert (spec_dir(repo, SLUG) / "spec.md").is_file()


@pytest.mark.parametrize("level", ["auto", "required"])
def test_both_worktree_levels_guard_a_linked_worktree(repo: Path, level: str) -> None:
    linked = _worktree(repo, "other", "-b", "feature/rate-limits")
    write(linked, ".devkit/config.toml", f'[tool.spec]\nworktree = "{level}"\n')
    with pytest.raises(ProposalWrongWorktreeError):
        handoff_proposal(linked, SLUG, today=TODAY)
    assert not (linked / "specs").exists()


def test_outside_git_nothing_is_checked(workspace: Path) -> None:
    accept(workspace / create_proposal(workspace, SLUG, today=TODAY).path)
    handoff_proposal(workspace, SLUG, today=TODAY)
    assert (spec_dir(workspace, SLUG) / "spec.md").is_file()


def test_the_library_raises_the_same_refusal(repo: Path) -> None:
    linked = _worktree(repo, "other", "-b", "other-task")
    with pytest.raises(ProposalWrongWorktreeError) as raised:
        handoff_proposal(linked, SLUG, today=TODAY)
    assert raised.value.target_files == (str(linked),)
