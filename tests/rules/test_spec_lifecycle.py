from __future__ import annotations

from pathlib import Path

from conftest import Write
from devkit.rules import RuleContext
from rules.support import found, run

from devkit_spec.rules.spec_lifecycle import SpecLifecycleRule

RULE = SpecLifecycleRule()


def _bundle(write: Write, slug: str, spec_status: str, reconcile_status: str = "", tasks: str = "") -> str:
    """Write a bundle under ``specs/2026-10/20261006-<slug>/`` and return its ``spec.md`` path."""
    base = f"specs/2026-10/20261006-{slug}"
    write(f"{base}/spec.md", f"---\nid: SPEC-{slug}\ntitle: T\nstatus: {spec_status}\n---\n\n# [SPEC-{slug}] T\n")
    if reconcile_status:
        write(
            f"{base}/reconcile.md",
            f"---\nreconcile_id: REC-{slug}\nfeature: 2026-10/20261006-{slug}\nstatus: {reconcile_status}\n"
            "targets: []\n---\n",
        )
    if tasks:
        write(f"{base}/tasks.md", f"---\nid: TASKS-{slug}\n---\n{tasks}")
    return f"{base}/spec.md"


def test_lifecycle_violations(workspace: Path, write: Write) -> None:
    _bundle(write, "ok", "completed", "resolved", "- [x] A\n- [x] B\n")
    _bundle(write, "in-progress", "in-progress", "resolved", "- [x] A\n- [ ] B\n")
    _bundle(write, "no-tasks", "planned", "resolved")
    _bundle(write, "fenced", "planned", "resolved", "```md\n- [x] example\n```\n")
    no_reconcile = _bundle(write, "no-rec", "completed", tasks="- [x] A\n")
    pending = _bundle(write, "pending", "completed", "pending", "- [x] A\n")
    stale = _bundle(write, "stale", "planned", "resolved", "- [x] A\n  - [X] nested\n")
    violations = {v.file: v for v in run(RULE, workspace)}
    assert set(violations) == {no_reconcile, pending, stale}
    assert all(v.line == 1 and v.remediation for v in violations.values())
    assert "has no reconcile.md" in violations[no_reconcile].message and not violations[no_reconcile].fixable
    assert "status 'pending'" in violations[pending].message and not violations[pending].fixable
    assert "is stale" in violations[stale].message and violations[stale].fixable


def test_statuses_are_compared_case_insensitively(workspace: Path, write: Write) -> None:
    _bundle(write, "upper", " Completed ", "Resolved", "- [x] A\n")
    assert run(RULE, workspace) == []


def test_fix_sets_stale_status_in_place(workspace: Path, write: Write) -> None:
    _bundle(write, "no-rec", "completed", tasks="- [x] A\n")
    spec = _bundle(write, "stale", "planned", "resolved", "- [x] A\n")
    path = workspace / spec
    path.write_bytes(b"---\r\nid: SPEC-stale\r\nstatus: planned  \r\n---\r\nstatus: planned\r\n")

    ctx = RuleContext(workspace_root=workspace, fix=True, dry_run=True)
    assert RULE.fix(ctx) == [spec]
    assert b"status: planned  \r\n---" in path.read_bytes()

    fixed = run(RULE, workspace, fix=True)
    assert sorted((v.file, v.fixed) for v in fixed) == [
        ("specs/2026-10/20261006-no-rec/spec.md", False),
        (spec, True),
    ]
    expected = b"---\r\nid: SPEC-stale\r\nstatus: completed\r\n---\r\nstatus: planned\r\n"
    assert path.read_bytes() == expected
    assert found(run(RULE, workspace, fix=True)) == [
        (
            "specs/2026-10/20261006-no-rec/spec.md",
            1,
            "Completed spec specs/2026-10/20261006-no-rec/spec.md has no reconcile.md",
        )
    ]
    assert path.read_bytes() == expected


def test_stale_spec_without_status_line_is_not_fixable(workspace: Path, write: Write) -> None:
    spec = _bundle(write, "stale", "planned", "resolved", "- [x] A\n")
    write(spec, "---\nid: SPEC-stale\n---\n")
    violations = run(RULE, workspace, fix=True)
    assert [(v.file, v.fixable, v.fixed) for v in violations] == [(spec, False, False)]
    assert "status ''" in violations[0].message


def test_completed_bundles_are_checked(workspace: Path, write: Write) -> None:
    spec = _bundle(write, "done", "completed", "pending")
    assert [file for file, _, _ in found(run(RULE, workspace))] == [spec]


def test_targets_select_bundles(workspace: Path, write: Write) -> None:
    pending = _bundle(write, "pending", "completed", "pending")
    stale = _bundle(write, "stale", "planned", "resolved", "- [x] A\n")
    other_tasks = "specs/2026-10/20261006-stale/tasks.md"

    assert [file for file, _, _ in found(run(RULE, workspace, pending))] == [pending]
    assert run(RULE, workspace, "docs/unrelated.md") == []

    by_tasks = run(RULE, workspace, other_tasks, fix=True)
    assert [(v.file, v.fixable, v.fixed) for v in by_tasks] == [(other_tasks, False, False)]
    assert "planned" in (workspace / stale).read_text()

    by_reconcile = run(RULE, workspace, "specs/2026-10/20261006-pending/reconcile.md")
    assert [v.file for v in by_reconcile] == ["specs/2026-10/20261006-pending/reconcile.md"]

    fixed = run(RULE, workspace, stale, other_tasks, fix=True)
    assert [(v.file, v.fixed) for v in fixed] == [(stale, True)]


def test_no_specs_directory(workspace: Path) -> None:
    assert run(RULE, workspace) == []
