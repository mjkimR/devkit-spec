---
id: TASKS-namespace-default-and-handoff-branch
spec: SPEC-namespace-default-and-handoff-branch
plan: PLAN-namespace-default-and-handoff-branch
---

# Task Breakdown: `SPEC-namespace-default-and-handoff-branch` Namespace default from the current directory and the handoff branch guard

## Phase 1: Namespace default

- [x] **Task 1.1**: `spec new` and `proposal new` default the namespace to the current directory and report it
  - **_Boundary**: `src/devkit_spec/proposals/scaffold.py`, `src/devkit_spec/proposals/specs.py`, `src/devkit_spec/cli/specs.py`, `src/devkit_spec/cli/proposals.py`, `tests/proposals/`
  - _Requirements: AC-01, AC-02, AC-03, AC-04_
  - **Verification**: `just test tests/proposals`

## Phase 2: Handoff guard

- [x] **Task 2.1**: Refuse a handoff in a linked worktree whose branch is not the slug
  - **_Boundary**: `src/devkit_spec/proposals/handoff.py`, `src/devkit_spec/errors.py`, `tests/proposals/`
  - _Requirements: AC-05, AC-06_
  - **Verification**: `just test tests/proposals`

## Phase 3: Bundle guidance

- [x] **Task 3.1**: Package glossary in `living-spec-writing`, namespace default in `spec-specify`
  - **_Boundary**: `src/devkit_spec/bundle/instructions/living-spec-writing.md`, `src/devkit_spec/bundle/skills/spec-specify/SKILL.md`
  - _Requirements: AC-07_
  - **Verification**: `just test tests/test_bundle_budgets.py`; `uv run --no-active devkit sync`
