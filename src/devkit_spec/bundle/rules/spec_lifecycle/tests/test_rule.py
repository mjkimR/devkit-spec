"""``RULE-spec-lifecycle``, loaded from this folder as devkit loads the deployed copy."""

from __future__ import annotations

from pathlib import Path

import pytest
from devkit.rules import Autofixable, RuleContext, Violation
from devkit.rules.testing import check, load_rule, write_files

RULE = load_rule(__file__)


def _found(violations: list[Violation]) -> list[tuple[str, int, str]]:
    """``(file, line, message)`` of the violations that remain (not fixed)."""
    return [(v.file, v.line, v.message) for v in violations if not v.fixed]


def _bundle(root: Path, slug: str, spec_status: str, reconcile_status: str = "", tasks: str = "") -> str:
    """Write a bundle under ``specs/2026-10/20261006-<slug>/`` and return its ``spec.md`` path."""
    base = f"specs/2026-10/20261006-{slug}"
    files = {f"{base}/spec.md": f"---\nid: SPEC-{slug}\ntitle: T\nstatus: {spec_status}\n---\n\n# [SPEC-{slug}] T\n"}
    if reconcile_status:
        files[f"{base}/reconcile.md"] = (
            f"---\nreconcile_id: REC-{slug}\nfeature: 2026-10/20261006-{slug}\nstatus: {reconcile_status}\n"
            "targets: []\n---\n"
        )
    if tasks:
        files[f"{base}/tasks.md"] = f"---\nid: TASKS-{slug}\n---\n{tasks}"
    write_files(root, files)
    return f"{base}/spec.md"


def test_lifecycle_violations(tmp_path: Path) -> None:
    _bundle(tmp_path, "ok", "completed", "resolved", "- [x] A\n- [x] B\n")
    _bundle(tmp_path, "in-progress", "in-progress", "resolved", "- [x] A\n- [ ] B\n")
    _bundle(tmp_path, "no-tasks", "planned", "resolved")
    _bundle(tmp_path, "fenced", "planned", "resolved", "```md\n- [x] example\n```\n")
    no_reconcile = _bundle(tmp_path, "no-rec", "completed", tasks="- [x] A\n")
    pending = _bundle(tmp_path, "pending", "completed", "pending", "- [x] A\n")
    stale = _bundle(tmp_path, "stale", "planned", "resolved", "- [x] A\n  - [X] nested\n")
    violations = {v.file: v for v in check(RULE, tmp_path)}
    assert set(violations) == {no_reconcile, pending, stale}
    assert all(v.line == 1 and v.remediation for v in violations.values())
    assert "has no reconcile.md" in violations[no_reconcile].message and not violations[no_reconcile].fixable
    assert "status 'pending'" in violations[pending].message and not violations[pending].fixable
    assert "is stale" in violations[stale].message and violations[stale].fixable


def test_statuses_are_compared_case_insensitively(tmp_path: Path) -> None:
    _bundle(tmp_path, "upper", " Completed ", "Resolved", "- [x] A\n")
    assert check(RULE, tmp_path) == []


def test_fix_sets_stale_status_in_place(tmp_path: Path) -> None:
    _bundle(tmp_path, "no-rec", "completed", tasks="- [x] A\n")
    spec = _bundle(tmp_path, "stale", "planned", "resolved", "- [x] A\n")
    path = tmp_path / spec
    path.write_bytes(b"---\r\nid: SPEC-stale\r\nstatus: planned  \r\n---\r\nstatus: planned\r\n")

    ctx = RuleContext(workspace_root=tmp_path, fix=True, dry_run=True)
    assert isinstance(RULE, Autofixable)
    assert RULE.fix(ctx) == [spec]
    assert b"status: planned  \r\n---" in path.read_bytes()

    fixed = check(RULE, tmp_path, fix=True)
    assert sorted((v.file, v.fixed) for v in fixed) == [
        ("specs/2026-10/20261006-no-rec/spec.md", False),
        (spec, True),
    ]
    expected = b"---\r\nid: SPEC-stale\r\nstatus: completed\r\n---\r\nstatus: planned\r\n"
    assert path.read_bytes() == expected
    assert _found(check(RULE, tmp_path, fix=True)) == [
        (
            "specs/2026-10/20261006-no-rec/spec.md",
            1,
            "Completed spec specs/2026-10/20261006-no-rec/spec.md has no reconcile.md",
        )
    ]
    assert path.read_bytes() == expected


def test_fix_keeps_a_trailing_comment(tmp_path: Path) -> None:
    spec = _bundle(tmp_path, "stale", "planned", "resolved", "- [x] A\n")
    path = tmp_path / spec
    path.write_text(
        "---\nid: SPEC-stale\nstatus: draft # draft | planned | in-progress | completed\n---\n", encoding="utf-8"
    )
    assert [v.fixed for v in check(RULE, tmp_path, fix=True)] == [True]
    assert path.read_text(encoding="utf-8") == (
        "---\nid: SPEC-stale\nstatus: completed # draft | planned | in-progress | completed\n---\n"
    )
    assert check(RULE, tmp_path) == []


@pytest.mark.parametrize(
    ("status", "fixed"),
    [
        ('"draft #2"', "completed"),
        ('"draft #2" # note', "completed # note"),
        ("'it''s #1' # c", "completed # c"),
        ('"a \\" #b" #c', "completed #c"),
        ("draft#2", "completed"),
        ('"open #1', "completed"),
    ],
)
def test_fix_reads_a_hash_inside_quotes_as_the_value(tmp_path: Path, status: str, fixed: str) -> None:
    spec = _bundle(tmp_path, "stale", "planned", "resolved", "- [x] A\n")
    path = tmp_path / spec
    path.write_text(f"---\nid: SPEC-stale\nstatus: {status}\n---\n", encoding="utf-8")
    check(RULE, tmp_path, fix=True)
    assert path.read_text(encoding="utf-8") == f"---\nid: SPEC-stale\nstatus: {fixed}\n---\n"


def test_stale_spec_without_status_line_is_not_fixable(tmp_path: Path) -> None:
    spec = _bundle(tmp_path, "stale", "planned", "resolved", "- [x] A\n")
    violations = check(RULE, tmp_path, {spec: "---\nid: SPEC-stale\n---\n"}, fix=True)
    assert [(v.file, v.fixable, v.fixed) for v in violations] == [(spec, False, False)]
    assert "status ''" in violations[0].message


def test_completed_bundles_are_checked(tmp_path: Path) -> None:
    spec = _bundle(tmp_path, "done", "completed", "pending")
    assert [file for file, _, _ in _found(check(RULE, tmp_path))] == [spec]


def test_targets_select_bundles(tmp_path: Path) -> None:
    pending = _bundle(tmp_path, "pending", "completed", "pending")
    stale = _bundle(tmp_path, "stale", "planned", "resolved", "- [x] A\n")
    other_tasks = "specs/2026-10/20261006-stale/tasks.md"

    assert [file for file, _, _ in _found(check(RULE, tmp_path, targets=[pending]))] == [pending]
    # A target must exist; an unrelated file selects no bundle.
    assert check(RULE, tmp_path, {"docs/unrelated.md": "# unrelated\n"}, targets=["docs/unrelated.md"]) == []

    by_tasks = check(RULE, tmp_path, targets=[other_tasks], fix=True)
    assert [(v.file, v.fixable, v.fixed) for v in by_tasks] == [(other_tasks, False, False)]
    assert "planned" in (tmp_path / stale).read_text()

    by_reconcile = check(RULE, tmp_path, targets=["specs/2026-10/20261006-pending/reconcile.md"])
    assert [v.file for v in by_reconcile] == ["specs/2026-10/20261006-pending/reconcile.md"]

    fixed = check(RULE, tmp_path, targets=[stale, other_tasks], fix=True)
    assert [(v.file, v.fixed) for v in fixed] == [(stale, True)]


def test_no_specs_directory(tmp_path: Path) -> None:
    assert check(RULE, tmp_path) == []
