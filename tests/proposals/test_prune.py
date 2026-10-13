from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from conftest import Write
from devkit.cli import cli as devkit_cli

from devkit_spec.proposals import prune_proposals


def test_only_empty_trees_are_removed(workspace: Path, write: Write) -> None:
    (workspace / "docs/proposals/PROP-done/decisions").mkdir(parents=True)
    (workspace / "docs/proposals/PROP-done/materials").mkdir()
    write("docs/proposals/PROP-live/proposal.md", "x\n")
    write("docs/proposals/PROP-notes/materials/note.txt", "kept\n")
    assert prune_proposals(workspace) == ["docs/proposals/PROP-done"]
    assert not (workspace / "docs/proposals/PROP-done").exists()
    assert (workspace / "docs/proposals/PROP-live/proposal.md").is_file()
    assert (workspace / "docs/proposals/PROP-notes/materials/note.txt").is_file()
    assert prune_proposals(workspace) == []


def test_a_slug_prunes_one_proposal(workspace: Path) -> None:
    (workspace / "docs/proposals/PROP-a").mkdir(parents=True)
    (workspace / "docs/proposals/PROP-b").mkdir()
    assert prune_proposals(workspace, "a") == ["docs/proposals/PROP-a"]
    assert (workspace / "docs/proposals/PROP-b").is_dir()


def test_cli(workspace: Path) -> None:
    (workspace / "docs/proposals/PROP-a/materials").mkdir(parents=True)

    def run(*args: str) -> str:
        return CliRunner().invoke(devkit_cli, ["spec", "proposal", "prune", *args, "-w", str(workspace)]).stdout

    assert run("--format", "json") == json.dumps({"pruned": ["docs/proposals/PROP-a"]}, indent=2) + "\n"
    assert run() == "[OK: nothing to prune]\n"
