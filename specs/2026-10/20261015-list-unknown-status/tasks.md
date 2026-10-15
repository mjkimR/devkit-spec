---
id: TASKS-list-unknown-status
spec: SPEC-list-unknown-status
plan: PLAN-list-unknown-status
---

# Task Breakdown: `SPEC-list-unknown-status` Flag an unknown status filter in devkit spec list

- [ ] **Task 1**: `SPEC_LIST_STATUS_UNKNOWN` notice in `devkit spec list`, with CLI tests for text, JSON,
  mixed values, history and namespace, and kind selection
  - **_Boundary**: `src/devkit_spec/errors.py`, `src/devkit_spec/cli/documents.py`, `tests/test_cli_documents.py`
  - _Requirements: AC-01, AC-02, AC-03, AC-04, AC-05_
  - **Verification**: `just test`
