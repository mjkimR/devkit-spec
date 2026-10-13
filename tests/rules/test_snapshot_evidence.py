"""Diff evidence in snapshot runs (``check --staged``/``--ci``): rules read ``ctx.snapshot``."""

from __future__ import annotations

import subprocess
from pathlib import Path

from conftest import Write
from devkit.rules import RuleContext, evaluate_rules, git_snapshot

from devkit_spec.rules.code_entrypoints import CodeEntrypointsRule
from devkit_spec.rules.reconcile_contract import ReconcileContractRule

BUNDLE = "specs/2026-10/20261001-x"


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def _repo(workspace: Path) -> None:
    _git(workspace, "init", "-q", "-b", "main")
    _git(workspace, "config", "user.email", "t@example.com")
    _git(workspace, "config", "user.name", "t")


def _staged(workspace: Path, rule: object) -> list[tuple[str, str]]:
    _git(workspace, "add", "-A")
    snapshot = git_snapshot(workspace, staged=True)
    ctx = RuleContext(workspace_root=workspace, changed_files=list(snapshot.changed), snapshot=snapshot)
    result = evaluate_rules(ctx, [rule])  # type: ignore[list-item]
    assert result.errors == []
    return [(v.file, v.message) for v in result.violations]


def _record(targets: str, status: str = "resolved") -> str:
    return f"---\nreconcile_id: REC-x\nstatus: {status}\ntargets:\n{targets}---\n"


def test_a_resolved_record_needs_its_modified_targets_in_the_diff(workspace: Path, write: Write) -> None:
    _repo(workspace)
    write("docs/a.md", "a\n")
    write("docs/b.md", "b\n")
    _git(workspace, "add", "-A")
    _git(workspace, "commit", "-q", "-m", "base")
    write("docs/a.md", "a changed\n")
    write(f"{BUNDLE}/spec.md", "---\nid: SPEC-x\nstatus: in-progress\n---\n")
    write(
        f"{BUNDLE}/reconcile.md",
        _record("  - {file: docs/a.md, resolution: modified}\n  - {file: docs/b.md, resolution: modified}\n"),
    )
    assert _staged(workspace, ReconcileContractRule()) == [
        (f"{BUNDLE}/reconcile.md", "target docs/b.md is resolved as modified but absent from the staged diff")
    ]


def test_a_pending_record_and_a_body_only_edit_need_no_evidence(workspace: Path, write: Write) -> None:
    _repo(workspace)
    write(f"{BUNDLE}/spec.md", "---\nid: SPEC-x\nstatus: in-progress\n---\n")
    write(f"{BUNDLE}/reconcile.md", _record("  - {file: docs/b.md, resolution: modified}\n", status="pending"))
    assert _staged(workspace, ReconcileContractRule()) == []
    write(f"{BUNDLE}/reconcile.md", _record("  - {file: docs/b.md, resolution: modified}\n"))
    write("docs/b.md", "b\n")
    _git(workspace, "add", "-A")
    _git(workspace, "commit", "-q", "-m", "resolved")
    write(f"{BUNDLE}/reconcile.md", _record("  - {file: docs/b.md, resolution: modified}\n") + "Body note.\n")
    assert _staged(workspace, ReconcileContractRule()) == []


def test_deleting_declared_code_is_caught_without_touching_the_document(workspace: Path, write: Write) -> None:
    _repo(workspace)
    write("src/app/run.py", "x = 1\n")
    write("src/keep.py", "y = 1\n")
    write("docs/capabilities/core/CAP-CORE-a.md", "---\nid: CAP-CORE-a\nstatus: active\nentrypoints: [src/app/]\n---\n")
    write(
        "docs/capabilities/core/CAP-CORE-b.md", "---\nid: CAP-CORE-b\nstatus: active\nentrypoints: [src/keep.py]\n---\n"
    )
    _git(workspace, "add", "-A")
    _git(workspace, "commit", "-q", "-m", "base")
    _git(workspace, "rm", "-q", "-r", "src/app")
    found = _staged(workspace, CodeEntrypointsRule())
    assert [file for file, _ in found] == ["docs/capabilities/core/CAP-CORE-a.md"]
    assert "Dead code entrypoint" in found[0][1]
