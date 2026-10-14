"""``RULE-spec-progress``, loaded from this folder as devkit loads the deployed copy."""

from __future__ import annotations

from pathlib import Path

from devkit.rules import Severity
from devkit.rules.testing import check, load_rule, write_files

RULE = load_rule(__file__)


def _bundle(root: Path, slug: str, spec_status: str, tasks: str = "", reconcile_status: str = "") -> str:
    """Write a bundle under ``specs/2026-10/20261006-<slug>/`` and return its ``spec.md`` path."""
    base = f"specs/2026-10/20261006-{slug}"
    files = {f"{base}/spec.md": f"---\nid: SPEC-{slug}\ntitle: T\nstatus: {spec_status}\n---\n\n# [SPEC-{slug}] T\n"}
    if tasks:
        files[f"{base}/tasks.md"] = f"---\nid: TASKS-{slug}\n---\n{tasks}"
    if reconcile_status:
        files[f"{base}/reconcile.md"] = (
            f"---\nreconcile_id: REC-{slug}\nfeature: SPEC-{slug}\nstatus: {reconcile_status}\ntargets: []\n---\n"
        )
    write_files(root, files)
    return f"{base}/spec.md"


def test_started_draft_or_planned_specs_are_reported(tmp_path: Path) -> None:
    started = _bundle(tmp_path, "started", "planned", "- [x] A\n- [ ] B\n")
    drafted = _bundle(tmp_path, "drafted", " Draft ", "- [x] A\n")
    _bundle(tmp_path, "unstarted", "planned", "- [ ] A\n- [ ] B\n")
    _bundle(tmp_path, "underway", "in-progress", "- [x] A\n- [ ] B\n")
    _bundle(tmp_path, "finished", "planned", "- [x] A\n", "resolved")  # RULE-spec-lifecycle's: due completed
    _bundle(tmp_path, "fenced", "planned", "```md\n- [x] example\n```\n- [ ] A\n")
    violations = {v.file: v for v in check(RULE, tmp_path)}
    assert set(violations) == {started, drafted}
    assert all(v.line == 1 and v.fixable and v.severity is Severity.WARNING for v in violations.values())
    assert violations[started].message == (f"Spec status 'planned' of {started} is behind its tasks: 1 of 2 checked")


def test_fix_sets_in_progress_in_place(tmp_path: Path) -> None:
    spec = _bundle(tmp_path, "started", "planned", "- [x] A\n- [ ] B\n")
    path = tmp_path / spec
    before = path.read_text()
    assert [(v.file, v.fixed) for v in check(RULE, tmp_path, fix=True)] == [(spec, True)]
    assert path.read_text() == before.replace("status: planned", "status: in-progress")
    assert check(RULE, tmp_path, fix=True) == []
    assert path.read_text() == before.replace("status: planned", "status: in-progress")


def test_fix_keeps_a_trailing_comment(tmp_path: Path) -> None:
    spec = _bundle(tmp_path, "started", "planned", "- [x] A\n- [ ] B\n")
    path = tmp_path / spec
    before = path.read_text().replace("status: planned", "status: planned   # draft | planned | in-progress")
    path.write_text(before)
    assert [v.fixed for v in check(RULE, tmp_path, fix=True)] == [True]
    assert path.read_text() == before.replace("status: planned", "status: in-progress")


def test_targeting_follows_spec_lifecycle(tmp_path: Path) -> None:
    spec = _bundle(tmp_path, "started", "planned", "- [x] A\n- [ ] B\n")
    tasks = "specs/2026-10/20261006-started/tasks.md"
    by_tasks = check(RULE, tmp_path, targets=[tasks], fix=True)
    assert [(v.file, v.fixable, v.fixed) for v in by_tasks] == [(tasks, False, False)]
    assert "status: planned" in (tmp_path / spec).read_text()
    write_files(tmp_path, {"docs/unrelated.md": "# unrelated\n"})
    assert check(RULE, tmp_path, targets=["docs/unrelated.md"]) == []


def test_a_spec_without_a_status_is_not_reported(tmp_path: Path) -> None:
    spec = _bundle(tmp_path, "started", "planned", "- [x] A\n")
    write_files(tmp_path, {spec: "---\nid: SPEC-started\n---\n"})
    assert check(RULE, tmp_path) == []
