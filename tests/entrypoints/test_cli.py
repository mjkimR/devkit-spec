from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner, Result
from conftest import Write
from devkit.cli import cli as devkit_cli

CAP = "docs/capabilities/x/CAP-X-one.md"
STORY = "docs/stories/x/US-two.md"


def _derive(workspace: Path, *args: str) -> Result:
    return CliRunner().invoke(devkit_cli, ["spec", "entrypoints", "derive", *args, "-w", str(workspace)])


def _code(result: Result) -> str:
    return json.loads(result.stdout)["error"]["code"]


@pytest.fixture
def bundles(workspace: Path, write: Write) -> Path:
    write(CAP, "---\nid: CAP-X-one\nstatus: active\n---\n")
    write(STORY, "---\nid: US-two\nstatus: active\n---\n")
    write("src/pkg/b.go", "package b\n")
    write("src/other/c.go", "package c\n")

    def bundle(directory: str, spec_id: str, status: str, boundary: str, target: str) -> None:
        write(f"{directory}/spec.md", f"---\nid: {spec_id}\nstatus: {status}\n---\n")
        write(
            f"{directory}/tasks.md", f"- [x] **Task 1**: t\n  - **_Boundary**: {boundary}\n  - _Requirements: AC-01_\n"
        )
        write(
            f"{directory}/reconcile.md",
            f"---\nreconcile_id: REC-x\nstatus: resolved\ntargets:\n  - file: {target}\n    resolution: modified\n---\n",
        )

    bundle("specs/2026-10/20261001-one", "SPEC-one", "completed", "`src/pkg/`, N/A", CAP)
    bundle("specs/2026-10/20261002-two", "SPEC-two", "completed", "`src/pkg/`, `src/other/`", CAP)
    bundle("specs/2026-10/20261003-three", "SPEC-three", "draft", "`src/other/`", STORY)
    write("specs/2026-10/20261004-four/spec.md", "---\nid: SPEC-four\nstatus: completed\n---\n")
    return workspace


def test_single_bundle(bundles: Path) -> None:
    result = _derive(bundles, "--spec", "specs/2026-10/20261001-one")
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines() == [
        "[PAIR: CAP-X-one code=src/pkg spec=SPEC-one task=1 state=new exists=yes]",
        "[SKIPPED: N/A kind=boundary spec=SPEC-one task=1 reason=not-a-path]",
        "[SUMMARY: pairs=1 new=1 declared=0 skipped=1 applied=0]",
    ]
    assert "entrypoints" not in (bundles / CAP).read_text()
    absolute = _derive(bundles, "--spec", str(bundles / "specs/2026-10/20261001-one"))
    assert absolute.stdout == result.stdout


def test_input_and_option_errors(bundles: Path, write: Write) -> None:
    result = _derive(bundles, "--spec", "specs/2026-10/20261004-four", "--format", "json")
    assert result.exit_code == 2
    error = json.loads(result.stdout)["error"]
    assert error["code"] == "SPEC_ENTRYPOINTS_INPUT_MISSING"
    assert error["advisory"]["target_files"] == ["specs/2026-10/20261004-four/tasks.md"]
    for args in (
        [],
        ["--spec", "x", "--all"],
        ["--spec", "x", "--min-count", "2"],
        ["--spec", "x", "--status", "draft"],
        ["--all", "--min-count", "0"],
        ["--all", "--target", "CAP-X-one"],
        ["--spec", "../outside"],
    ):
        assert _code(_derive(bundles, *args, "--format", "json")) == "ARGUMENT_INVALID", args
    write("specs/2026-10/20261005-five/tasks.md", "- [ ] t\n")
    write("specs/2026-10/20261005-five/reconcile.md", "not yaml\n")
    result = _derive(bundles, "--spec", "specs/2026-10/20261005-five")
    assert result.exit_code == 2 and "(SPEC_ENTRYPOINTS_INPUT_INVALID)" in result.stderr


def test_all_aggregates_and_skips_bundles(bundles: Path) -> None:
    result = _derive(bundles, "--all")
    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    assert "[PAIR: CAP-X-one code=src/pkg count=2 specs=SPEC-one,SPEC-two state=new exists=yes]" in lines
    assert "[PAIR: CAP-X-one code=src/other count=1 specs=SPEC-two state=new exists=yes]" in lines
    assert "US-two" not in result.stdout
    assert "[SKIPPED: specs/2026-10/20261004-four kind=bundle spec=SPEC-four reason=input-missing]" in lines

    payload = json.loads(_derive(bundles, "--all", "--min-count", "2", "--format", "json").stdout)
    assert [pair["code"] for pair in payload["pairs"]] == ["src/pkg"]
    assert payload["summary"]["pairs"] == 1
    assert payload["errors"] == [] and payload["notices"] == []

    result = _derive(bundles, "--all", "--status", "Draft")
    assert "[PAIR: US-two code=src/other count=1 specs=SPEC-three state=new exists=yes]" in result.stdout.splitlines()


def test_apply_with_targets(bundles: Path) -> None:
    assert _code(_derive(bundles, "--all", "--apply", "--target", "US-nope", "--format", "json")) == (
        "SPEC_ENTRYPOINTS_TARGET_UNKNOWN"
    )
    assert _code(_derive(bundles, "--all", "--apply", "--target", STORY, "--format", "json")) == (
        "SPEC_ENTRYPOINTS_TARGET_UNKNOWN"
    )
    result = _derive(bundles, "--all", "--apply", "--target", "CAP-X-one")
    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    assert f"[APPLIED: CAP-X-one path={CAP} added=src/other/,src/pkg/]" in lines
    assert lines[-1] == "[SUMMARY: pairs=2 new=2 declared=0 skipped=2 applied=1]"
    assert (bundles / CAP).read_text() == (
        "---\nid: CAP-X-one\nstatus: active\nentrypoints:\n  - src/other/\n  - src/pkg/\n---\n"
    )
    result = _derive(bundles, "--all", "--apply", "--target", f"./{CAP}")
    assert "state=declared" in result.stdout and result.stdout.endswith("applied=0]\n")


def test_code_and_exclude_filters(bundles: Path) -> None:
    result = _derive(bundles, "--all", "--code", "src/other")
    assert "code=src/pkg " not in result.stdout and "code=src/other " in result.stdout
    result = _derive(bundles, "--all", "--exclude", "src/other/")
    assert "[SKIPPED: src/other kind=boundary reason=excluded]" in result.stdout.splitlines()
    assert "code=src/pkg " in result.stdout
    assert _code(_derive(bundles, "--all", "--code", "../x", "--format", "json")) == "SPEC_ENTRYPOINTS_PATH_INVALID"


def test_target_without_selected_candidates_applies_nothing(bundles: Path) -> None:
    result = _derive(bundles, "--all", "--apply", "--target", "CAP-X-one", "--code", "src/nowhere")
    assert result.exit_code == 0
    assert result.stdout.splitlines()[-1] == "[SUMMARY: pairs=0 new=0 declared=0 skipped=2 applied=0]"
    assert "[APPLIED:" not in result.stdout and "entrypoints" not in (bundles / CAP).read_text()


def test_apply_failure_is_reported_after_the_result(bundles: Path, write: Write) -> None:
    (bundles / CAP).chmod(0o444)
    (bundles / CAP).parent.chmod(0o555)
    try:
        result = _derive(bundles, "--all", "--apply", "--format", "json")
    finally:
        (bundles / CAP).parent.chmod(0o755)
        (bundles / CAP).chmod(0o644)
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert [error["code"] for error in payload["errors"]] == ["SPEC_ENTRYPOINTS_APPLY_FAILED"]
    assert payload["errors"][0]["advisory"]["target_files"] == [CAP]
    assert payload["summary"]["applied"] == 0


def test_invalid_documents_are_warnings(bundles: Path, write: Write) -> None:
    write("docs/stories/x/US-broken.md", "---\nid: [\n---\n")
    result = _derive(bundles, "--spec", "specs/2026-10/20261001-one")
    assert result.exit_code == 0
    assert "(SPEC_DOCUMENT_INVALID)" in result.stderr
