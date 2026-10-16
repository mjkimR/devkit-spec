"""The ``devkit.hygiene`` extension: rejected proposals waiting for their cleanup."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner
from devkit.cli import cli as devkit_cli
from scope.support import write

from devkit_spec.hygiene import rejected_proposals


def _proposal(root: Path, slug: str, status: str) -> None:
    write(root, f"docs/proposals/PROP-{slug}/proposal.md", f"---\nid: PROP-{slug}\nstatus: {status}\n---\n# x\n")


def test_rejected_proposals_are_reported_until_they_are_cleaned_up(tmp_path: Path) -> None:
    assert rejected_proposals(tmp_path) is None  # no spec bundle: left alone
    (tmp_path / ".devkit/managed/spec").mkdir(parents=True)
    _proposal(tmp_path, "kept", "draft")
    assert rejected_proposals(tmp_path) is None
    _proposal(tmp_path, "gone", "rejected")
    write(tmp_path, "docs/proposals/PROP-single.md", "---\nid: PROP-single\nstatus: rejected\n---\n# x\n")
    found = rejected_proposals(tmp_path)
    assert found is not None
    assert [(w.code, w.message) for w in found] == [
        ("SPEC_PROPOSAL_REJECTED_PENDING", "docs/proposals/PROP-gone is rejected and waits for its cleanup"),
        ("SPEC_PROPOSAL_REJECTED_PENDING", "docs/proposals/PROP-single.md is rejected and waits for its cleanup"),
    ]
    assert found[0].fix is not None and "rejection ADR" in found[0].fix


def test_the_hygiene_run_shows_them_through_the_installed_entry_point(tmp_path: Path) -> None:
    (tmp_path / ".devkit/managed/spec").mkdir(parents=True)
    _proposal(tmp_path, "gone", "rejected")
    result = CliRunner().invoke(devkit_cli, ["rules", "check", "-p", "hygiene", "-w", str(tmp_path)])
    assert "(SPEC_PROPOSAL_REJECTED_PENDING) docs/proposals/PROP-gone is rejected" in result.stderr
