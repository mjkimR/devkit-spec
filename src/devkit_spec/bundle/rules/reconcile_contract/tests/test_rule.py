"""``RULE-reconcile-contract``, loaded from this folder as devkit loads the deployed copy."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from devkit.rules import RuleContext, Violation, evaluate_rules, git_snapshot
from devkit.rules.testing import check, load_rule, write_files

RULE = load_rule(__file__)
BUNDLE = "specs/2026-10/20261001-x"
SPEC = f"{BUNDLE}/spec.md"
RECORD = f"{BUNDLE}/reconcile.md"
WAIVER = "rationale: The acceptance criteria of this story are unchanged.\n"


def _found(violations: list[Violation]) -> list[tuple[str, int, str]]:
    """``(file, line, message)`` of the violations that remain (not fixed)."""
    return [(v.file, v.line, v.message) for v in violations if not v.fixed]


def _record(body: str) -> str:
    return f"---\nreconcile_id: REC-x\n{body}---\n# Reconcile\n"


def _spec(status: str = "in-progress") -> str:
    return f"---\nid: SPEC-x\nstatus: {status}\n---\n"


def test_a_well_formed_record_passes(tmp_path: Path) -> None:
    files = {
        SPEC: _spec(),
        RECORD: _record(
            "status: resolved\ntargets:\n  - file: docs/a.md\n    resolution: modified\n"
            f"  - file: docs/b.md\n    resolution: waived\n    {WAIVER}"
        ),
    }
    assert check(RULE, tmp_path, files) == []
    assert check(RULE, tmp_path, {RECORD: _record("status: pending\ntargets: []\n")}) == []


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
def test_malformed_records(tmp_path: Path, body: str, message: str) -> None:
    assert _found(check(RULE, tmp_path, {SPEC: _spec(), RECORD: _record(body)})) == [(RECORD, 1, message)]


def test_missing_id_and_frontmatter(tmp_path: Path) -> None:
    files = {SPEC: _spec(), RECORD: "---\nstatus: pending\ntargets: []\n---\n"}
    assert [m for _, _, m in _found(check(RULE, tmp_path, files))] == ["reconcile_id is missing"]
    files = {RECORD: "# no frontmatter\n"}
    assert [m for _, _, m in _found(check(RULE, tmp_path, files))] == ["reconcile.md has no frontmatter"]
    files = {RECORD: "---\nstatus: [\n---\n"}
    assert _found(check(RULE, tmp_path, files))[0][2].startswith("frontmatter is malformed")


def test_completed_bundles_only_when_targeted(tmp_path: Path) -> None:
    files = {SPEC: _spec("completed"), RECORD: _record("status: done\n")}
    assert check(RULE, tmp_path, files) == []
    assert len(_found(check(RULE, tmp_path, targets=[RECORD]))) == 2


def test_only_targets_are_reported(tmp_path: Path) -> None:
    files = {SPEC: _spec(), RECORD: _record("status: done\ntargets: []\n")}
    assert check(RULE, tmp_path, files, targets=[SPEC]) == []


# Diff evidence in snapshot runs (``check --staged``/``--ci``): the rule reads ``ctx.snapshot``.


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def _repo(root: Path) -> None:
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")


def _staged(root: Path) -> list[tuple[str, str]]:
    _git(root, "add", "-A")
    snapshot = git_snapshot(root, staged=True)
    ctx = RuleContext(workspace_root=root, changed_files=list(snapshot.changed), snapshot=snapshot)
    result = evaluate_rules(ctx, [RULE])
    assert result.errors == []
    return [(v.file, v.message) for v in result.violations]


def _targets_record(targets: str, status: str = "resolved") -> str:
    return f"---\nreconcile_id: REC-x\nstatus: {status}\ntargets:\n{targets}---\n"


def test_a_resolved_record_needs_its_modified_targets_in_the_diff(tmp_path: Path) -> None:
    _repo(tmp_path)
    write_files(tmp_path, {"docs/a.md": "a\n", "docs/b.md": "b\n"})
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    write_files(
        tmp_path,
        {
            "docs/a.md": "a changed\n",
            SPEC: _spec(),
            RECORD: _targets_record(
                "  - {file: docs/a.md, resolution: modified}\n  - {file: docs/b.md, resolution: modified}\n"
            ),
        },
    )
    assert _staged(tmp_path) == [(RECORD, "target docs/b.md is resolved as modified but absent from the staged diff")]


def test_a_pending_record_and_a_body_only_edit_need_no_evidence(tmp_path: Path) -> None:
    _repo(tmp_path)
    targets = "  - {file: docs/b.md, resolution: modified}\n"
    write_files(tmp_path, {SPEC: _spec(), RECORD: _targets_record(targets, status="pending")})
    assert _staged(tmp_path) == []
    write_files(tmp_path, {RECORD: _targets_record(targets), "docs/b.md": "b\n"})
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "resolved")
    write_files(tmp_path, {RECORD: _targets_record(targets) + "Body note.\n"})
    assert _staged(tmp_path) == []
