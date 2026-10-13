from __future__ import annotations

import os
from pathlib import Path

import pytest
from conftest import Write
from rules.support import found, run

from devkit_spec.rules.code_entrypoints import CodeEntrypointsRule

RULE = CodeEntrypointsRule()
VALID = "docs/capabilities/test/CAP-TEST-valid.md"
STORY = "docs/stories/test/US-invalid.md"


def test_existing_paths_pass(workspace: Path, write: Write) -> None:
    write("src/main.go", "package main")
    write(VALID, "---\nid: CAP-TEST-valid\nentrypoints: [src/, ./src/main.go, .]\n---\n")
    write("docs/stories/test/US-absent.md", "---\nid: US-absent\n---\n")
    write("docs/stories/test/US-empty.md", "---\nid: US-empty\nentrypoints: []\n---\n")
    write("docs/packages/api/capabilities/core/CAP-CORE-a.md", "---\nid: CAP-CORE-a\nentrypoints: [src/main.go]\n---\n")
    assert run(RULE, workspace) == []


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
def test_invalid_declarations(workspace: Path, write: Write, value: str, message: str) -> None:
    write(STORY, f"---\nid: US-invalid\nentrypoints: {value}\n---\n")
    assert found(run(RULE, workspace)) == [(STORY, 3, message)]


def test_lines_point_at_items(workspace: Path, write: Write) -> None:
    write("src/a.py", "")
    write(STORY, "---\nid: US-invalid\ntitle: x\nentrypoints:\n  - src/a.py\n  - src/gone.py\n---\n")
    assert [(line, message) for _, line, message in found(run(RULE, workspace))] == [
        (6, "Dead code entrypoint: 'src/gone.py' (missing or outside workspace)")
    ]


def test_symlink_outside_workspace_is_dead(
    workspace: Path, write: Write, tmp_path_factory: pytest.TempPathFactory
) -> None:
    outside = tmp_path_factory.mktemp("outside")
    os.symlink(outside, workspace / "escape")
    write(STORY, "---\nid: US-invalid\nentrypoints: [escape]\n---\n")
    assert len(found(run(RULE, workspace))) == 1


def test_only_targets_and_bearing_documents(workspace: Path, write: Write) -> None:
    write(STORY, "---\nid: US-invalid\nentrypoints: [missing]\n---\n")
    write("docs/decisions/2026-10/20261001-x.md", "---\nid: ADR-x\nentrypoints: [missing]\n---\n")
    write("docs/materials/MAT-x.md", "---\nid: MAT-x\nentrypoints: [missing]\n---\n")
    write(VALID, "---\nid: CAP-TEST-valid\n---\n")
    assert [file for file, _, _ in found(run(RULE, workspace))] == [STORY]
    assert run(RULE, workspace, VALID) == []
    assert len(found(run(RULE, workspace, STORY))) == 1
