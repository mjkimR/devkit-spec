---
id: TASKS-orchestration-mode
spec: SPEC-orchestration-mode
plan: PLAN-orchestration-mode
---

# Task Breakdown: `SPEC-orchestration-mode` Orchestration mode for delegated implementation

- [x] **Task 1**: Worker role contract, its bundle declaration and projection tests.
  - **_Boundary**: src/devkit_spec/bundle/subagents/worker.md, src/devkit_spec/bundle/bundle.toml,
    tests/test_role_contracts.py, tests/test_workflows.py
  - _Requirements: AC-02, AC-05_
- [x] **Task 2**: spec-delegate worker support with the payload table moved to a reference.
  - **_Boundary**: src/devkit_spec/bundle/skills/spec-delegate/, tests/test_role_contracts.py
  - _Requirements: AC-03, AC-05_
- [x] **Task 3**: spec-orchestrate mode skill, its declaration and the constitution pointer.
  - **_Boundary**: src/devkit_spec/bundle/skills/spec-orchestrate/, src/devkit_spec/bundle/bundle.toml,
    src/devkit_spec/bundle/AGENTS.md
  - _Requirements: AC-01, AC-04, AC-05_
