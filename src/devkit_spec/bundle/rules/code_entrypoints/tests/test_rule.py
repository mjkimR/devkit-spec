"""``RULE-code-entrypoints``, loaded from this folder as devkit loads the deployed copy."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from devkit.rules import RuleContext, Violation, evaluate_rules, git_snapshot
from devkit.rules.testing import check, load_rule, write_files

RULE = load_rule(__file__)
VALID = "docs/capabilities/test/CAP-TEST-valid.md"
STORY = "docs/stories/test/US-invalid.md"


def _found(violations: list[Violation]) -> list[tuple[str, int, str]]:
    """``(file, line, message)`` of the violations that remain (not fixed)."""
    return [(v.file, v.line, v.message) for v in violations if not v.fixed]


def test_existing_paths_pass(tmp_path: Path) -> None:
    files = {
        "src/main.go": "package main",
        VALID: "---\nid: CAP-TEST-valid\nentrypoints: [src/, ./src/main.go, .]\n---\n",
        "docs/stories/test/US-absent.md": "---\nid: US-absent\n---\n",
        "docs/stories/test/US-empty.md": "---\nid: US-empty\nentrypoints: []\n---\n",
        "docs/packages/api/capabilities/core/CAP-CORE-a.md": "---\nid: CAP-CORE-a\nentrypoints: [src/main.go]\n---\n",
    }
    assert check(RULE, tmp_path, files) == []


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("'[missing]'", "entrypoints must be an array of path strings"),
        ("null", "entrypoints must be an array of path strings"),
        ("{file: src}", "entrypoints must be an array of path strings"),
        ("[42]", "entrypoints must contain only path strings"),
        ("['']", "invalid entrypoint '': use a literal workspace-relative path"),
        ("['../src']", "invalid entrypoint '../src': parent traversal is forbidden"),
        ("['/src']", "invalid entrypoint '/src': use a literal workspace-relative path"),
        ("['src/*']", "invalid entrypoint 'src/*': use a literal workspace-relative path"),
        ("['missing']", "Dead code entrypoint: 'missing' (missing or outside workspace)"),
    ],
)
def test_invalid_declarations(tmp_path: Path, value: str, message: str) -> None:
    files = {STORY: f"---\nid: US-invalid\nentrypoints: {value}\n---\n"}
    assert _found(check(RULE, tmp_path, files)) == [(STORY, 3, message)]


def test_lines_point_at_items(tmp_path: Path) -> None:
    files = {
        "src/a.py": "",
        STORY: "---\nid: US-invalid\ntitle: x\nentrypoints:\n  - src/a.py\n  - src/gone.py\n---\n",
    }
    assert [(line, message) for _, line, message in _found(check(RULE, tmp_path, files))] == [
        (6, "Dead code entrypoint: 'src/gone.py' (missing or outside workspace)")
    ]


def test_symlink_outside_workspace_is_dead(tmp_path: Path, tmp_path_factory: pytest.TempPathFactory) -> None:
    outside = tmp_path_factory.mktemp("outside")
    os.symlink(outside, tmp_path / "escape")
    files = {STORY: "---\nid: US-invalid\nentrypoints: [escape]\n---\n"}
    assert len(_found(check(RULE, tmp_path, files))) == 1


def test_only_targets_and_bearing_documents(tmp_path: Path) -> None:
    files = {
        STORY: "---\nid: US-invalid\nentrypoints: [missing]\n---\n",
        "docs/decisions/2026-10/20261001-x.md": "---\nid: ADR-x\nentrypoints: [missing]\n---\n",
        "docs/materials/MAT-x.md": "---\nid: MAT-x\nentrypoints: [missing]\n---\n",
        VALID: "---\nid: CAP-TEST-valid\n---\n",
    }
    assert [file for file, _, _ in _found(check(RULE, tmp_path, files))] == [STORY]
    assert check(RULE, tmp_path, targets=[VALID]) == []
    assert len(_found(check(RULE, tmp_path, targets=[STORY]))) == 1


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def test_deleting_declared_code_is_caught_without_touching_the_document(tmp_path: Path) -> None:
    """A snapshot run (``check --staged``/``--ci``) reads the deletion from ``ctx.snapshot``."""
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    write_files(
        tmp_path,
        {
            "src/app/run.py": "x = 1\n",
            "src/keep.py": "y = 1\n",
            "docs/capabilities/core/CAP-CORE-a.md": "---\nid: CAP-CORE-a\nstatus: active\nentrypoints: [src/app/]\n---\n",
            "docs/capabilities/core/CAP-CORE-b.md": (
                "---\nid: CAP-CORE-b\nstatus: active\nentrypoints: [src/keep.py]\n---\n"
            ),
        },
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    _git(tmp_path, "rm", "-q", "-r", "src/app")
    _git(tmp_path, "add", "-A")
    snapshot = git_snapshot(tmp_path, staged=True)
    ctx = RuleContext(workspace_root=tmp_path, changed_files=list(snapshot.changed), snapshot=snapshot)
    result = evaluate_rules(ctx, [RULE])
    assert result.errors == []
    found = [(v.file, v.message) for v in result.violations]
    assert [file for file, _ in found] == ["docs/capabilities/core/CAP-CORE-a.md"]
    assert "Dead code entrypoint" in found[0][1]
