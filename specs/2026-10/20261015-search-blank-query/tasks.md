---
id: TASKS-search-blank-query
spec: SPEC-search-blank-query
plan: PLAN-search-blank-query
---

# Task Breakdown: `SPEC-search-blank-query` Reject a blank search query

- [x] **Task 1**: Refuse a blank query in `devkit spec search`, with CLI tests for text, JSON and an unchanged
  non-blank query
  - **_Boundary**: `src/devkit_spec/cli/search.py`, `tests/test_search.py`
  - _Requirements: AC-01, AC-02, AC-03_
  - **Verification**: `just test`
