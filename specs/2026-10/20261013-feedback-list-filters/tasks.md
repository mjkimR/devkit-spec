---
id: TASKS-feedback-list-filters
spec: SPEC-feedback-list-filters
plan: PLAN-feedback-list-filters
---

# Task Breakdown: `SPEC-feedback-list-filters` Feedback list filters

## Phase 1: List command

- [x] **Task 1.1**: `--where` option: parsing, malformed-item errors and the frontmatter match
  - **_Boundary**: `src/devkit_spec/cli/documents.py`, `tests/test_cli_documents.py`
  - _Requirements: AC-01, AC-02, AC-03, AC-04_
  - **Verification**: `just test tests/test_cli_documents.py`
- [x] **Task 1.2**: Severity order and the feedback fields on text lines and JSON records
  - **_Boundary**: `src/devkit_spec/cli/documents.py`, `tests/test_cli_documents.py`
  - _Requirements: AC-05, AC-06_
  - **Verification**: `just test tests/test_cli_documents.py`
- [x] **Task 1.3**: `[NEXT_CMD]` repeats every `--where`
  - **_Boundary**: `src/devkit_spec/cli/documents.py`, `tests/test_cli_documents.py`
  - _Requirements: AC-07_
  - **Verification**: `just test tests/test_cli_documents.py`

## Phase 2: Bundle assets

- [x] **Task 2.1**: `spec-next`, `envelope.md`, `sweep.md` and `feedback-hygiene` select feedback with `--where`
  - **_Boundary**: `src/devkit_spec/bundle/skills/spec-next/SKILL.md`, `src/devkit_spec/bundle/skills/spec/references/envelope.md`, `src/devkit_spec/bundle/skills/spec-feedback/references/sweep.md`, `src/devkit_spec/bundle/playbooks/feedback-hygiene/SKILL.md`
  - _Requirements: AC-08_
  - **Verification**: `just test tests/test_bundle_budgets.py`; `uv run --no-active devkit sync`
