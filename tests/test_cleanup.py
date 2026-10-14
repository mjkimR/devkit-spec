"""The ``devkit.post_finish`` extension: proposal pruning and the finished worktree's scope record."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner
from devkit.cli import cli as devkit_cli
from scope.support import SPEC, git, make_repo, write

from devkit_spec.cleanup import after_finish
from devkit_spec.errors import SpecConfigError


def _scope(root: Path, *args: str) -> str:
    return CliRunner().invoke(devkit_cli, ["spec", "scope", *args, "-w", str(root)]).stdout


def test_a_project_without_the_spec_bundle_is_left_alone(tmp_path: Path) -> None:
    write(tmp_path, "docs/proposals/PROP-x/decisions/.keep-dir/x", "")
    assert after_finish(tmp_path, {"slug": "x", "path": str(tmp_path / "wt")}) is None


def test_finish_prunes_the_proposal_and_removes_only_the_finished_worktree_record(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "repo")
    (repo / ".devkit/managed/spec").mkdir(parents=True)
    (repo / "docs/proposals/PROP-s/decisions").mkdir(parents=True)  # what a merged handoff leaves
    (repo / "docs/proposals/PROP-kept/materials").mkdir(parents=True)
    write(repo, "docs/proposals/PROP-kept/materials/note.md", "kept\n")
    finished, other = tmp_path / "wt-s", tmp_path / "wt-b"
    git(repo, "worktree", "add", "-q", "-b", "s", str(finished))
    git(repo, "worktree", "add", "-q", "-b", "b", str(other))
    write(other, "specs/2026-10/20261002-b/spec.md", "---\nid: SPEC-b\n---\n")
    write(other, "specs/2026-10/20261002-b/tasks.md", "- [ ] t\n  - _Boundary: src/a/\n")
    assert "[SCOPE: SPEC-s " in _scope(finished, "register", "--spec", SPEC)
    assert "[SCOPE: SPEC-b " in _scope(other, "register", "--spec", "specs/2026-10/20261002-b")
    git(repo, "worktree", "remove", "--force", str(finished))
    git(repo, "worktree", "remove", "--force", str(other))

    lines = after_finish(repo, {"slug": "s", "path": str(finished)})
    assert lines == ["removed empty proposal directory docs/proposals/PROP-s", "removed the scope record of SPEC-s"]
    assert not (repo / "docs/proposals/PROP-s").exists() and (repo / "docs/proposals/PROP-kept").is_dir()
    # The other stale record waits for an explicit sweep.
    assert "[SWEEP: SPEC-b verdict=stale" in _scope(repo, "sweep")
    assert after_finish(repo, {"slug": "s", "path": str(finished)}) is None  # nothing left: idempotent


def test_a_failed_record_removal_keeps_the_prune_notices(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "repo")
    (repo / ".devkit/managed/spec").mkdir(parents=True)
    (repo / "docs/proposals/PROP-s/decisions").mkdir(parents=True)
    write(repo, ".devkit/config.toml", "[tool.spec.scope]\ntimeout = 0\n")
    lines = after_finish(repo, {"slug": "s", "path": str(tmp_path / "wt-s")})
    assert lines is not None and lines[0] == "removed empty proposal directory docs/proposals/PROP-s"
    assert len(lines) == 2 and isinstance(lines[1], SpecConfigError)
    assert str(lines[1].fix).endswith(
        "then run devkit spec scope sweep --apply to remove the finished worktree's scope record"
    )
