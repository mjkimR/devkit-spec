from __future__ import annotations

from pathlib import Path

import pytest
from conftest import Write
from rules.support import found, run

from devkit_spec.rules.reconcile_contract import ReconcileContractRule

RULE = ReconcileContractRule()
BUNDLE = "specs/2026-10/20261001-x"
WAIVER = "rationale: The acceptance criteria of this story are unchanged.\n"


def _record(body: str) -> str:
    return f"---\nreconcile_id: REC-x\n{body}---\n# Reconcile\n"


def _spec(write: Write, status: str = "in-progress") -> None:
    write(f"{BUNDLE}/spec.md", f"---\nid: SPEC-x\nstatus: {status}\n---\n")


def test_a_well_formed_record_passes(workspace: Path, write: Write) -> None:
    _spec(write)
    write(
        f"{BUNDLE}/reconcile.md",
        _record(
            "status: resolved\ntargets:\n  - file: docs/a.md\n    resolution: modified\n"
            f"  - file: docs/b.md\n    resolution: waived\n    {WAIVER}"
        ),
    )
    assert run(RULE, workspace) == []
    write(f"{BUNDLE}/reconcile.md", _record("status: pending\ntargets: []\n"))
    assert run(RULE, workspace) == []


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("status: done\ntargets: []\n", "status must be pending or resolved, got 'done'"),
        ("status: resolved\n", "targets must be a list (empty when nothing in the Living Spec is affected)"),
        ("status: resolved\ntargets: [x]\n", "targets[1] must be a mapping of file, resolution and rationale"),
        (
            "status: resolved\ntargets:\n  - {file: ../a.md, resolution: modified}\n",
            "targets[1].file '../a.md' must be a unique workspace-relative path",
        ),
        (
            "status: resolved\ntargets:\n  - {file: a.md, resolution: modified}\n  - {file: a.md, resolution: modified}\n",
            "targets[2].file 'a.md' must be a unique workspace-relative path",
        ),
        (
            "status: resolved\ntargets:\n  - {file: a.md, resolution: kept}\n",
            "targets[1].resolution must be modified or waived, got 'kept'",
        ),
        (
            "status: resolved\ntargets:\n  - {file: a.md, resolution: waived, rationale: not needed}\n",
            "targets[1] waiver of a.md needs a rationale of at least 20 non-whitespace characters, has 9",
        ),
    ],
)
def test_malformed_records(workspace: Path, write: Write, body: str, message: str) -> None:
    _spec(write)
    write(f"{BUNDLE}/reconcile.md", _record(body))
    assert found(run(RULE, workspace)) == [(f"{BUNDLE}/reconcile.md", 1, message)]


def test_missing_id_and_frontmatter(workspace: Path, write: Write) -> None:
    _spec(write)
    write(f"{BUNDLE}/reconcile.md", "---\nstatus: pending\ntargets: []\n---\n")
    assert [m for _, _, m in found(run(RULE, workspace))] == ["reconcile_id is missing"]
    write(f"{BUNDLE}/reconcile.md", "# no frontmatter\n")
    assert [m for _, _, m in found(run(RULE, workspace))] == ["reconcile.md has no frontmatter"]
    write(f"{BUNDLE}/reconcile.md", "---\nstatus: [\n---\n")
    assert found(run(RULE, workspace))[0][2].startswith("frontmatter is malformed")


def test_completed_bundles_only_when_targeted(workspace: Path, write: Write) -> None:
    _spec(write, "completed")
    write(f"{BUNDLE}/reconcile.md", _record("status: done\n"))
    assert run(RULE, workspace) == []
    assert len(found(run(RULE, workspace, f"{BUNDLE}/reconcile.md"))) == 2


def test_only_targets_are_reported(workspace: Path, write: Write) -> None:
    _spec(write)
    write(f"{BUNDLE}/reconcile.md", _record("status: done\ntargets: []\n"))
    assert run(RULE, workspace, f"{BUNDLE}/spec.md") == []
