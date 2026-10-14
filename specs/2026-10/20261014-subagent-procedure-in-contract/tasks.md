---
id: TASKS-subagent-procedure-in-contract
spec: SPEC-subagent-procedure-in-contract
plan: PLAN-subagent-procedure-in-contract
---

# Task Breakdown: `SPEC-subagent-procedure-in-contract` Subagent procedures in role contracts

- [x] **Task 1**: Fold the Scout and Challenger procedures into their contracts, give Scout a shell, remove the two
  skills and their references in the bundle
  - **_Boundary**: `src/devkit_spec/bundle/subagents/scout.md`, `src/devkit_spec/bundle/subagents/challenger.md`,
    `src/devkit_spec/bundle/skills/spec-scout/`, `src/devkit_spec/bundle/skills/spec-challenge/`,
    `src/devkit_spec/bundle/bundle.toml`, `src/devkit_spec/bundle/workflows/incubated-delivery.md`,
    `src/devkit_spec/bundle/skills/spec/SKILL.md`, `.devkit/installation.json`
  - _Requirements: AC-01, AC-02, AC-05, AC-07_
  - **Verification**: `rg -n "spec-scout|spec-challenge" src README.md` returns nothing
- [x] **Task 2**: Remove caller-only sections from all four contracts and move the caller guidance into
  `spec-delegate`
  - **_Boundary**: `src/devkit_spec/bundle/subagents/`, `src/devkit_spec/bundle/skills/spec-delegate/SKILL.md`
  - _Requirements: AC-03, AC-04, AC-06_
- [x] **Task 3**: Tests for the contracts, `spec-delegate` and the projected skill set
  - **_Boundary**: `tests/test_role_contracts.py`, `tests/test_workflows.py`
  - _Requirements: AC-01, AC-02, AC-03, AC-04, AC-05, AC-06_
  - **Verification**: `just test tests/test_role_contracts.py tests/test_workflows.py tests/test_bundle_budgets.py`
- [x] **Task 4**: Restructure `spec-delegate` and `spec` with the `skill-authoring` playbook (conditional content into
  references), with a link test
  - **_Boundary**: `src/devkit_spec/bundle/skills/spec-delegate/`, `src/devkit_spec/bundle/skills/spec/`,
    `tests/test_bundle_budgets.py`
  - _Requirements: AC-08_
  - **Verification**: `just test tests/test_bundle_budgets.py`
