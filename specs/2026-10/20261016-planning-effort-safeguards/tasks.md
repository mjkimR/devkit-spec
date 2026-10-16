---
id: TASKS-planning-effort-safeguards
spec: SPEC-planning-effort-safeguards
plan: PLAN-planning-effort-safeguards
---

# Task Breakdown: `SPEC-planning-effort-safeguards` Planning effort safeguards

- [x] **Task 1**: Update the strategy layer's effort table, plan-intent row, acceptance request, decisions and change
  list (workbench, written first)
  - **_Boundary**: workbench `docs/strategy-layer/01-master-flow.md`
  - _Requirements: AC-01_
  - **Verification**: read against AC-01; `git -C <workbench> diff --check`
- [x] **Task 2**: Make `challenger` the `medium` default of proposal Planning and state the effort proposal and the
  `high` criteria in the bundle
  - **_Boundary**: `src/devkit_spec/bundle/skills/spec/references/effort.md`,
    `src/devkit_spec/bundle/skills/spec/references/classification.md`, `src/devkit_spec/bundle/skills/spec/SKILL.md`,
    `src/devkit_spec/bundle/skills/spec-delegate/SKILL.md`, `src/devkit_spec/bundle/subagents/planning-worker.md`,
    `src/devkit_spec/bundle/workflows/sdd-proposal.md`
  - _Requirements: AC-02, AC-03, AC-04_
  - **Verification**: the `rg` checks of the plan; `devkit workflow show sdd-proposal`
- [x] **Task 3**: Sync the projected copies and rebind the bound proposals when the workflow hash changed
  - **_Boundary**: `.devkit/`, `.claude/`, `.agents/`, `docs/proposals/*/proposal.md`
  - _Requirements: AC-05_
  - **Verification**: `devkit sync`; `devkit workflow next --unit docs/proposals/PROP-<slug>` for each proposal (the hash covers the stage schema only, so the body change needed no rebind)
- [x] **Task 4**: Reflect the Planning effort rule in the Living Spec and run the checks
  - **_Boundary**: `docs/capabilities/delivery/CAP-DLV-delivery-workflows.md`
  - _Requirements: AC-06_
  - **Verification**: `just ci`
