"""``RULE-task-coverage``, loaded from this folder as devkit loads the deployed copy."""

from __future__ import annotations

from pathlib import Path

import pytest
from devkit.rules import RuleContext, Violation, evaluate_rules
from devkit.rules.testing import check, load_rule, write_files

RULE = load_rule(__file__)
BUNDLE = "specs/2026-10/20261001-feature"
SPEC = f"{BUNDLE}/spec.md"
TASKS = f"{BUNDLE}/tasks.md"
SPEC_ONE = "## 4. Acceptance Criteria & Behavioral Contracts\n### Scenario 1 [AC-01]: First\n"
SPEC_TWO = SPEC_ONE + "### Scenario 2 [AC-02]: Second\n"
TEMPLATE_TASKS = (
    "- [ ] **Task 1**: Domain types and validation, with unit tests\n"
    "  - **_Boundary**: `src/domain/types.go`, `src/domain/types_test.go`\n"
    "  - _Requirements: AC-01_\n"
    "- [ ] **Task 2**: CLI command wiring and its error output\n"
    "  - **_Boundary**: `src/cli/commands/run.go`, `src/cli/commands/run_test.go`\n"
    "  - _Requirements: AC-01, AC-02_\n"
    "  - **Verification**: `just build && ./bin/cli run --help`\n"
)
MISSING_01 = "acceptance criteria without a task: AC-01"


def _found(violations: list[Violation]) -> list[tuple[str, int, str]]:
    """``(file, line, message)`` of the violations that remain (not fixed)."""
    return [(v.file, v.line, v.message) for v in violations if not v.fixed]


def _messages(root: Path, spec: str, tasks: str) -> list[str]:
    violations = check(RULE, root, {SPEC: spec, TASKS: tasks})
    assert all(v.rule_id == "RULE-task-coverage" and v.remediation and v.line >= 1 for v in violations)
    return [message for _, _, message in _found(violations)]


@pytest.mark.parametrize(
    ("spec", "tasks"),
    [
        pytest.param(SPEC_TWO, "- [ ] Parent\n  - [ ] Child [AC-02]\n  - _Requirements: AC-01_", id="nested"),
        pytest.param(SPEC_TWO, "- [ ] First [AC-01]\n- [x] Second [AC-02]", id="inline"),
        pytest.param(SPEC_TWO, "- [ ] Both\n  - _Boundary: src/_\n  - _Requirements: AC-01, AC-02_", id="metadata"),
        pytest.param(SPEC_TWO, "- [ ] Both [AC-01] [AC-02]\n- [X] Again [AC-01]", id="many-to-many"),
        pytest.param(SPEC_TWO, "* [ ] Star [AC-01]\n+ [ ] Plus\n  - _Requirements: AC-02_", id="markers"),
        pytest.param(SPEC_TWO, "- [ ] A\n  - [ ] B\n    - [ ] C [AC-01]\n      - _Requirements: AC-02_", id="deep"),
        pytest.param(SPEC_ONE + "## 5. Notes\n### Other [AC-99]", "- [ ] Task [AC-01]", id="other-sections"),
        pytest.param(SPEC_ONE.replace("\n", "\r\n"), "- [ ] Task\r\n  - _Requirements: AC-01_\r\n", id="crlf"),
        pytest.param(SPEC_TWO, TEMPLATE_TASKS, id="tasks-template"),
    ],
)
def test_covered_pairs_pass(tmp_path: Path, spec: str, tasks: str) -> None:
    assert _messages(tmp_path, spec, tasks) == []


@pytest.mark.parametrize(
    ("spec", "tasks", "expected"),
    [
        pytest.param(SPEC_TWO, "- [ ] First [AC-01]", "acceptance criteria without a task: AC-02", id="missing"),
        pytest.param(SPEC_ONE, "- [ ] First [AC-01] [AC-99]", "undefined acceptance criteria: AC-99", id="phantom"),
        pytest.param(
            SPEC_ONE + "### Other [AC-01]: Again",
            "- [ ] First [AC-01]",
            "duplicate acceptance criterion ID AC-01",
            id="duplicate",
        ),
        pytest.param(
            SPEC_ONE + "### Other: No ID", "- [ ] First [AC-01]", "exactly one [AC-NN] ID, found 0", id="no-id"
        ),
        pytest.param(
            "## Acceptance Criteria\n### Other [AC-1]: Bad", "", "exactly one [AC-NN] ID, found 0", id="short"
        ),
        pytest.param(SPEC_ONE + "### Other [AC-02] [AC-03]", "", "exactly one [AC-NN] ID, found 2", id="two-ids"),
        pytest.param("## Acceptance Criteria\n", "", "no acceptance criteria defined", id="empty"),
        pytest.param("## Introduction\n### X [AC-01]", "- [ ] First [AC-01]", "no acceptance criteria", id="outside"),
        pytest.param("# Spec [AC-01]\n### X [AC-01]", "- [ ] First [AC-01]", "no acceptance criteria", id="no-section"),
        pytest.param("```\n" + SPEC_ONE + "```", "- [ ] Task [AC-01]", "no acceptance criteria", id="fenced-spec"),
        pytest.param("<!--\n" + SPEC_ONE + "-->", "- [ ] Task [AC-01]", "no acceptance criteria", id="commented-spec"),
        pytest.param(
            SPEC_ONE, "- [ ] Task [AC-01]\n  - _Requirements: AC-1_", "invalid requirement ID 'AC-1'", id="bad"
        ),
        pytest.param(SPEC_ONE, "- [ ] Task [AC-01]\n  - _Requirements: _", "invalid requirement ID ''", id="blank"),
        pytest.param(SPEC_ONE, "- [ ] Task\n\n    - [ ] Code [AC-01]", MISSING_01, id="indented-code-after-task"),
        pytest.param(SPEC_ONE, "| Task | [AC-01] |", MISSING_01, id="table"),
        pytest.param(SPEC_ONE, "Mention [AC-01]\n_Requirements: AC-01_", MISSING_01, id="prose"),
        pytest.param(SPEC_ONE, "> - [ ] Example [AC-01]", MISSING_01, id="quote"),
        pytest.param(SPEC_ONE, "```md\n- [ ] Example [AC-01]\n```", MISSING_01, id="fence"),
        pytest.param(SPEC_ONE, "~~~~md\n- [ ] Example [AC-01]\n~~~\n~~~~", MISSING_01, id="tilde-fence"),
        pytest.param(SPEC_ONE, "<!--\n- [ ] Example [AC-01]\n-->", MISSING_01, id="comment"),
        pytest.param(SPEC_ONE, "<!-- - [ ] Example [AC-01] -->", MISSING_01, id="inline-comment"),
        pytest.param(SPEC_ONE, "---\nexample: '[AC-01]'\n---", MISSING_01, id="frontmatter"),
        pytest.param(SPEC_ONE, "    - [ ] Example [AC-01]", MISSING_01, id="indented-code"),
        pytest.param(SPEC_ONE, "- [ ] Task\n  - Details\n    - _Requirements: AC-01_", MISSING_01, id="indirect"),
        pytest.param(SPEC_ONE, "- [ ] Task\n## Next\n  - _Requirements: AC-01_", MISSING_01, id="detached"),
        pytest.param(SPEC_ONE, "- [ ] Task\n- _Requirements: AC-01_", MISSING_01, id="unindented"),
    ],
)
def test_coverage_problems(tmp_path: Path, spec: str, tasks: str, expected: str) -> None:
    assert any(expected in message for message in _messages(tmp_path, spec, tasks))


def test_violation_locations(tmp_path: Path) -> None:
    files = {
        SPEC: SPEC_TWO + "### Again [AC-02]\n",
        TASKS: "- [ ] Unknown [AC-99] [AC-98]\n  - _Requirements: AC-01, x_\n",
    }
    assert _found(check(RULE, tmp_path, files)) == [
        (SPEC, 4, "duplicate acceptance criterion ID AC-02"),
        (TASKS, 2, "invalid requirement ID 'x'"),
        (TASKS, 1, "acceptance criteria without a task: AC-02"),
        (TASKS, 1, "tasks reference undefined acceptance criteria: AC-98, AC-99"),
    ]


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        pytest.param("---\nstatus: planned\n---\n" + SPEC_ONE, "without a task: AC-01", id="active"),
        pytest.param("---\nstatus: completed\n---\n", None, id="completed"),
        pytest.param("---\nstatus: 'completed'\n---\n", None, id="quoted-status"),
        pytest.param("---\nstatus: Completed\n---\n", None, id="status-case"),
        pytest.param(SPEC_ONE + "status: completed\n", "without a task: AC-01", id="body-status"),
        pytest.param("---\nstatus: [\n---\n", "invalid spec frontmatter", id="invalid-yaml"),
        pytest.param("---\nstatus: planned\n", "invalid spec frontmatter", id="unclosed-yaml"),
    ],
)
def test_spec_status(tmp_path: Path, spec: str, expected: str | None) -> None:
    messages = _messages(tmp_path, spec, "")
    if expected is None:
        assert messages == []
    else:
        assert any(expected in message for message in messages)


def test_missing_spec_and_specs_before_tasks(tmp_path: Path) -> None:
    assert check(RULE, tmp_path, {"specs/2026-10/20261002-planned/spec.md": SPEC_ONE}) == []
    assert _found(check(RULE, tmp_path, {TASKS: "- [ ] Task [AC-01]\n"})) == [
        (SPEC, 1, "the paired spec.md cannot be read: it does not exist")
    ]


def test_no_specs_directory(tmp_path: Path) -> None:
    assert check(RULE, tmp_path) == []


def test_pair_is_checked_when_either_file_is_targeted(tmp_path: Path) -> None:
    write_files(tmp_path, {SPEC: SPEC_TWO, TASKS: "- [ ] First [AC-01]\n", "docs/unrelated.md": "# unrelated\n"})
    expected = [(TASKS, 1, "acceptance criteria without a task: AC-02")]
    assert _found(check(RULE, tmp_path, targets=[SPEC])) == expected
    assert _found(check(RULE, tmp_path, targets=[TASKS])) == expected
    assert check(RULE, tmp_path, targets=["docs/unrelated.md"]) == []


def test_completed_pairs_are_checked_only_when_explicitly_targeted(tmp_path: Path) -> None:
    assert check(RULE, tmp_path, {SPEC: "---\nstatus: completed\n---\n" + SPEC_ONE, TASKS: ""}) == []
    assert _found(check(RULE, tmp_path, targets=[TASKS])) == [(TASKS, 1, MISSING_01)]
    assert _found(check(RULE, tmp_path, targets=[SPEC])) == [(TASKS, 1, MISSING_01)]


def test_excluded_files_are_not_reported(tmp_path: Path) -> None:
    write_files(tmp_path, {SPEC: SPEC_TWO + "### Again [AC-02]\n", TASKS: "- [ ] First [AC-01]\n"})
    ctx = RuleContext(workspace_root=tmp_path, changed_files=[SPEC], exclude=("specs/**/tasks.md",))
    result = evaluate_rules(ctx, [RULE])
    assert _found(result.violations) == [(SPEC, 4, "duplicate acceptance criterion ID AC-02")]
