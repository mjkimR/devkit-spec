---
id: TASKS-proposal-effort-hints
spec: SPEC-proposal-effort-hints
plan: PLAN-proposal-effort-hints
---

# Task Breakdown: `SPEC-proposal-effort-hints` Separate Planning and Development effort hints on proposals

## Phase 1: Proposal Scaffolding, Validation, Handoff & Listing
- [ ] **Task 1.1**: Add `EFFORTS`, `DEFAULT_EFFORT`, `PLANNING_EFFORT`, `DEV_EFFORT` and `--planning-effort` / `--dev-effort` scaffolding to `binding.py`, `scaffold.py`, and `cli/proposals.py`
  - **_Boundary**: `src/devkit_spec/proposals/binding.py`, `src/devkit_spec/proposals/scaffold.py`, `src/devkit_spec/cli/proposals.py`
  - _Requirements: AC-01_
  - **Verification**: `uv run pytest tests/test_proposals.py`
- [ ] **Task 1.2**: Validate `planning_effort` and `dev_effort` on proposal anchors in `RULE-spec-format`
  - **_Boundary**: `src/devkit_spec/rules/spec_format.py`, `src/devkit_spec/rules/guides/RULE-spec-format/guide.md`
  - _Requirements: AC-02_
  - **Verification**: `uv run pytest tests/test_spec_format_rule.py`
- [ ] **Task 1.3**: Validate effort hints on `handoff`, expose `dev_effort` on `HandoffResult` without copying to `spec.md`, and expose `task_kind` / `planning_effort` / `dev_effort` in `devkit spec list`
  - **_Boundary**: `src/devkit_spec/proposals/handoff.py`, `src/devkit_spec/cli/proposals.py`, `src/devkit_spec/cli/documents.py`
  - _Requirements: AC-03, AC-04_
  - **Verification**: `uv run pytest tests/test_proposals.py tests/test_documents.py`

## Phase 2: Bundle Guidance, Sync & Living Spec Reconciliation
- [ ] **Task 2.1**: Update bundle workflow, subagent and skill guidance (`sdd-proposal.md`, `planning-worker.md`, `spec`, `spec-orchestrate`), rebind existing proposals, and run `devkit sync`
  - **_Boundary**: `src/devkit_spec/bundle/`, `docs/proposals/`, `.devkit/`
  - _Requirements: AC-05_
  - **Verification**: `uv run pytest tests/test_bundle.py && uv run devkit rules check`
- [ ] **Task 2.2**: Reconcile Living Spec capabilities and `docs/proposals/README.md`
  - **_Boundary**: `docs/capabilities/`, `docs/proposals/README.md`
  - _Requirements: AC-01, AC-02, AC-03, AC-04, AC-05_
  - **Verification**: `just ci`
