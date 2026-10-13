---
id: TASKS-boundary-continuation-lines
spec: SPEC-boundary-continuation-lines
plan: PLAN-boundary-continuation-lines
---

# Task Breakdown: `SPEC-boundary-continuation-lines` Boundary continuation lines

## Phase 1: Parser

- [x] **Task 1.1**: Join indented continuation lines in `parse_boundaries`
  - **_Boundary**: `src/devkit_spec/entrypoints/bundle.py`, `tests/entrypoints/test_derive.py`, `tests/scope/test_inputs.py`
  - _Requirements: AC-01, AC-02, AC-03_
  - **Verification**: `just test tests/entrypoints tests/scope`

## Phase 2: Guidance

- [x] **Task 2.1**: State the wrapped form in `spec-tasks`
  - **_Boundary**: `src/devkit_spec/bundle/skills/spec-tasks/SKILL.md`
  - _Requirements: AC-04_
  - **Verification**: `just test tests/test_bundle_budgets.py`
