---
id: TASKS-commit-gate-rules-default
spec: SPEC-commit-gate-rules-default
plan: PLAN-commit-gate-rules-default
---

# Task Breakdown: `SPEC-commit-gate-rules-default` Commit gate runs the spec rules by default

- [x] **Task 1**: Pin devkit at the commit with the `rules-check` gate and resync
  - **_Boundary**: `uv.lock`, `.devkit/installation.json`, `AGENTS.md`
  - _Requirements: AC-01, AC-02_
  - **Verification**: `uv run devkit gate status`; refused scratch commit with an over-long summary
- [ ] **Task 2**: Rewrite the bundle guidance: constitution, brownfield playbook commit gate step, seed CI/CD page
  - **_Boundary**: `src/devkit_spec/bundle/AGENTS.md`, `src/devkit_spec/bundle/playbooks/brownfield-adoption/SKILL.md`,
    `src/devkit_spec/bundle/seed/docs/development/ci-cd.md`, `AGENTS.md`, `.devkit/installation.json`
  - _Requirements: AC-03, AC-04_
  - **Verification**: `just ci`
- [ ] **Task 3**: Rewrite this repository's development docs that describe its commit gate
  - **_Boundary**: `docs/development/workflow.md`, `docs/development/specrig-port-map.md`
  - _Requirements: AC-03_
