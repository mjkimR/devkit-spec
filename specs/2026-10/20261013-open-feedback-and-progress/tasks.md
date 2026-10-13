---
id: TASKS-open-feedback-and-progress
spec: SPEC-open-feedback-and-progress
plan: PLAN-open-feedback-and-progress
---

# Task Breakdown: `SPEC-open-feedback-and-progress` Open feedback outside history and in-progress specs

## Phase 1: Feedback outside history

- [x] **Task 1.1**: Leave feedback documents out of `historical`
  - **_Boundary**: `src/devkit_spec/documents/index.py`, `src/devkit_spec/documents/__init__.py`, `src/devkit_spec/rules/id_convention.py`, `src/devkit_spec/proposals/rewrite.py`, `tests/proposals/test_proposal_handoff.py`, `src/devkit_spec/bundle/rules/id_convention/tests/test_rule.py`, `tests/test_cli_documents.py`, `tests/test_search.py`, `tests/documents/test_index.py`
  - _Requirements: AC-01, AC-02, AC-03_
  - **Verification**: `just test tests/test_cli_documents.py tests/test_search.py tests/documents`
- [x] **Task 1.2**: Drop `--history` from the feedback commands of the bundle assets
  - **_Boundary**: `src/devkit_spec/bundle/skills/spec-next/SKILL.md`, `src/devkit_spec/bundle/skills/spec/references/envelope.md`, `src/devkit_spec/bundle/skills/spec-feedback/SKILL.md`, `src/devkit_spec/bundle/skills/spec-feedback/references/sweep.md`, `src/devkit_spec/bundle/playbooks/feedback-hygiene/SKILL.md`
  - _Requirements: AC-07_
  - **Verification**: `just test tests/test_bundle_budgets.py`

## Phase 2: RULE-spec-progress

- [x] **Task 2.1**: Shared bundle helpers and `SpecProgressRule`
  - **_Boundary**: `src/devkit_spec/rules/spec_lifecycle.py`, `src/devkit_spec/rules/spec_progress.py`
  - _Requirements: AC-04, AC-05, AC-06_
  - **Verification**: `devkit rules test RULE-spec-progress RULE-spec-lifecycle`
- [x] **Task 2.2**: Bundle asset: wrapper, guide, tests, `bundle.toml`
  - **_Boundary**: `src/devkit_spec/bundle/rules/spec_progress/rule.py`, `src/devkit_spec/bundle/rules/spec_progress/guide.md`, `src/devkit_spec/bundle/rules/spec_progress/tests/test_rule.py`, `src/devkit_spec/bundle/bundle.toml`
  - _Requirements: AC-04, AC-05, AC-06_
  - **Verification**: `just test src/devkit_spec/bundle/rules/spec_progress`; `devkit sync`
