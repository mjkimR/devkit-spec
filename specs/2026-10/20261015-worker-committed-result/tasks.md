---
id: TASKS-worker-committed-result
spec: SPEC-worker-committed-result
plan: PLAN-worker-committed-result
---

# Task Breakdown: `SPEC-worker-committed-result` Workers deliver committed, self-contained results

- [x] **Task 1**: Record the decision
  - **_Boundary**: `docs/decisions/2026-10/20261015-worker-delivers-committed-result.md`
  - _Requirements: AC-06_
- [ ] **Task 2**: Worker contract: committed, self-contained result, with role contract tests
  - **_Boundary**: `src/devkit_spec/bundle/subagents/worker.md`, `tests/test_role_contracts.py`
  - _Requirements: AC-01, AC-02, AC-03_
- [ ] **Task 3**: Host side: range validation and block in `spec-delegate`, the loop in `spec-orchestrate`, worker
  boundaries in `spec-tasks`, with tests
  - **_Boundary**: `src/devkit_spec/bundle/skills/spec-delegate/SKILL.md`,
    `src/devkit_spec/bundle/skills/spec-delegate/references/payload.md`,
    `src/devkit_spec/bundle/skills/spec-orchestrate/SKILL.md`, `src/devkit_spec/bundle/skills/spec-tasks/SKILL.md`,
    `tests/test_role_contracts.py`
  - _Requirements: AC-02, AC-04, AC-05_
  - **Verification**: `just ci`
