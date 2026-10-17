---
id: TASKS-hook-driven-integration-cleanup
spec: SPEC-hook-driven-integration-cleanup
plan: PLAN-hook-driven-integration-cleanup
---

# Task Breakdown: `SPEC-hook-driven-integration-cleanup` Approval-driven integration and worktree cleanup

- [ ] **Task 1**: Update `devkit` lockfile dependency, register the `devkit.integration.readiness` entry point, and configure `[integration] provider = "spec"`
  - **_Boundary**: `pyproject.toml`, `uv.lock`, `.devkit/config.toml`, `tests/test_package.py`
  - _Requirements: AC-01, AC-06, AC-07_
  - **Verification**: `uv run pytest tests/test_package.py`
- [ ] **Task 2**: Implement scoped local-only post-finish cleanup (`ScopedCleanup`) in `src/devkit_spec/cleanup.py` with unit and resume tests
  - **_Boundary**: `src/devkit_spec/cleanup.py`, `tests/test_cleanup.py`
  - _Requirements: AC-04, AC-05_
  - **Verification**: `uv run pytest tests/test_cleanup.py`
- [ ] **Task 3**: Implement the SDD readiness provider in `src/devkit_spec/integration.py` and end-to-end `IntegrationService` tests for Unit and session tasks
  - **_Boundary**: `src/devkit_spec/integration.py`, `tests/test_integration.py`
  - _Requirements: AC-01, AC-02, AC-03, AC-06_
  - **Verification**: `uv run pytest tests/test_integration.py`
- [ ] **Task 4**: Update `spec-integrate` and `spec` worktree/completion guidance for approval-bound local integration and `--local-only` recovery, and track deferred follow-ups
  - **_Boundary**: `src/devkit_spec/bundle/skills/spec-integrate/SKILL.md`, `src/devkit_spec/bundle/skills/spec/references/worktree.md`, `src/devkit_spec/bundle/skills/spec/references/completion.md`, `tests/test_bundle_budgets.py`
  - _Requirements: AC-07_
  - **Verification**: `uv run pytest tests/test_bundle_budgets.py`
