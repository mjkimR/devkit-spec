---
id: TASKS-handoff-unit-records
spec: SPEC-handoff-unit-records
plan: PLAN-handoff-unit-records
---

# Task Breakdown: `SPEC-handoff-unit-records` Proposal handoff and the workflow records of the proposal unit

- [x] **Task 1**: Drop the proposal unit's records and record the spec's gates in the handoff, with the warning, the
  CLI lines and tests.
  - **_Boundary**: src/devkit_spec/proposals/handoff.py, src/devkit_spec/errors.py, src/devkit_spec/cli/proposals.py,
    tests/proposals/
  - _Requirements: AC-01, AC-02, AC-03, AC-04_
  - **Verification**: `just test`
- [x] **Task 2**: Living Spec, workflow gate rules and skill references.
  - **_Boundary**: docs/capabilities/delivery/CAP-DLV-proposal-incubation.md,
    docs/architecture/ARCH-06-runtime-view.md, src/devkit_spec/bundle/workflows/,
    src/devkit_spec/bundle/skills/spec/references/worktree.md,
    src/devkit_spec/bundle/skills/spec-next/references/post-handoff.md
  - _Requirements: AC-05_
  - **Verification**: `just ci`
