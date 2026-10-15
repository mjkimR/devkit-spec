---
id: PLAN-search-blank-query
spec: SPEC-search-blank-query
---

# Technical Plan: `SPEC-search-blank-query` Reject a blank search query

## 1. Constitution & Invariant Review

None. The check follows the existing `--limit` validation in the same command (devkit's `ArgumentError`).

## 2. Architecture Overview & Impact

- **Impacted Components**:
  - `src/devkit_spec/cli/search.py`: after joining `words`, raise `ArgumentError` when `query.strip()` is empty,
    with `target_files=["QUERY"]` and a `[FIX]` asking for at least one non-blank word. The check runs before the
    index is loaded.
  - `tests/test_search.py`: CLI tests for AC-01 to AC-03.
- **New Dependencies**: None.

## 3. Error Handling & Edge Cases

- `words` is `required=True`, so click already rejects no argument at all; the new check covers arguments that are
  all blank.
- Pinning, glossary expansion and ranking are not reached for a blank query.

## 4. Verification & Test Plan

- `just test` (new tests in `tests/test_search.py`), `just lint`, `just check`, `devkit rules check`.
