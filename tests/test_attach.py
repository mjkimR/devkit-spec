"""The ``devkit.attach_check`` extension: the unit of an activity branch, read at the branch tip."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from devkit.cli import cli as devkit_cli
from scope.support import git, write

from devkit_spec.attach import attach_check

PROPOSAL = "docs/proposals/PROP-login"
SPEC = "specs/2026-10/20261016-login"


def _repo(tmp_path: Path) -> Path:
    root = (tmp_path / "repo").resolve()
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    write(root, "README.md", "x\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    return root


def _commit(root: Path, branch: str, files: dict[str, str]) -> str:
    git(root, "switch", "-q", "-c", branch)
    for rel, text in files.items():
        write(root, rel, text)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", branch)
    tip = git(root, "rev-parse", "HEAD")
    git(root, "switch", "-q", "main")
    return tip


def _anchor(workflow: str, status: str = "draft") -> str:
    return f"---\nid: X\nstatus: {status}\nworkflow: {workflow}\n---\n# x\n"


def test_a_plan_branch_carries_its_proposal_bound_to_sdd_proposal(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    tip = _commit(root, "plan-login", {f"{PROPOSAL}/proposal.md": _anchor("sdd-proposal")})
    assert attach_check(root, "plan-login", PROPOSAL, tip) == []
    assert attach_check(root, "plan-other", PROPOSAL, tip) == [
        f"{PROPOSAL} is the unit of slug login, not of plan-other"
    ]
    assert "not a proposal bundle" in attach_check(root, "plan-login", SPEC, tip)[0]


def test_a_plan_branch_refuses_a_rejected_or_undecomposed_proposal(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    rejected = _commit(root, "plan-login", {f"{PROPOSAL}/proposal.md": _anchor("sdd-proposal", "rejected")})
    assert any("is rejected" in reason for reason in attach_check(root, "plan-login", PROPOSAL, rejected))
    split = _anchor("sdd-proposal").replace("status: draft\n", "status: draft\nneeds_decompose: true\n")
    marked = _commit(root, "plan-split", {"docs/proposals/PROP-split/proposal.md": split})
    reasons = attach_check(root, "plan-split", "docs/proposals/PROP-split", marked)
    assert any("needs_decompose" in reason for reason in reasons)


def test_a_dev_branch_carries_its_spec_or_the_accepted_proposal_before_the_handoff(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    tip = _commit(
        root,
        "dev-login",
        {
            f"{SPEC}/spec.md": _anchor("sdd-spec-bugfix"),
            f"{PROPOSAL}/proposal.md": _anchor("sdd-proposal", "accepted"),
            "docs/proposals/PROP-draft/proposal.md": _anchor("sdd-proposal"),
            "specs/2026-10/20261016-old/spec.md": _anchor("direct-delivery"),
        },
    )
    assert attach_check(root, "dev-login", SPEC, tip) == []
    assert attach_check(root, "dev-login", PROPOSAL, tip) == []
    assert attach_check(root, "dev-draft", "docs/proposals/PROP-draft", tip) == [
        "docs/proposals/PROP-draft/proposal.md at "
        f"{tip[:7]} is not accepted and bound to sdd-proposal (workflow: sdd-proposal)"
    ]
    assert attach_check(root, "dev-old", "specs/2026-10/20261016-old", tip) == [
        f"specs/2026-10/20261016-old/spec.md at {tip[:7]} is not bound to an sdd-spec-* workflow"
        " (workflow: direct-delivery)"
    ]
    assert "neither a spec bundle" in attach_check(root, "dev-login", "src/login", tip)[0]


@pytest.mark.parametrize(
    ("files", "reason"),
    [
        ({f"{PROPOSAL}/notes.md": "x\n"}, "has no proposal.md"),
        ({f"{PROPOSAL}/proposal.md": "---\nid: [\n---\n"}, "unreadable frontmatter"),
        ({f"{PROPOSAL}/proposal.md": "---\nid: X\n---\n"}, "(workflow: -)"),
    ],
)
def test_an_unreadable_or_unbound_anchor_refuses(tmp_path: Path, files: dict[str, str], reason: str) -> None:
    root = _repo(tmp_path)
    tip = _commit(root, "plan-login", files)
    reasons = attach_check(root, "plan-login", PROPOSAL, tip)
    assert len(reasons) == 1 and reason in reasons[0]


def test_devkit_refuses_attaching_a_branch_to_another_unit_through_the_installed_extension(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _commit(
        root,
        "plan-login",
        {
            f"{PROPOSAL}/proposal.md": _anchor("sdd-proposal"),
            "docs/proposals/PROP-other/proposal.md": _anchor("sdd-proposal"),
        },
    )
    start = ["worktree", "start", "plan-login", "--existing-branch", "plan-login", "-w", str(root), "--format", "json"]
    refused = CliRunner().invoke(devkit_cli, [*start, "--unit", "docs/proposals/PROP-other"])
    assert refused.exit_code == 2
    assert json.loads(refused.stdout)["error"]["code"] == "WORKTREE_ATTACH_REFUSED"
    attached = CliRunner().invoke(devkit_cli, [*start, "--unit", PROPOSAL])
    assert attached.exit_code == 0, attached.output
    assert json.loads(attached.stdout)["unit"] == PROPOSAL
