---
id: PLAN-boundary-continuation-lines
spec: SPEC-boundary-continuation-lines
---

# Technical Plan: `SPEC-boundary-continuation-lines` Boundary continuation lines

## 1. Constitution & Invariant Review

None. The parse rule of `CAP-TRACE-code-entrypoints` (section on the code side) widens; the registry
(`CAP-COLL-work-scope-registry`) already defers to it.

## 2. Architecture Overview & Impact

- **Impacted Components**:
  - `src/devkit_spec/entrypoints/bundle.py`: `parse_boundaries` keeps the open boundary's indentation and appends each
    following line indented deeper that is not blank and not a list item; anything else closes it.
  - `src/devkit_spec/bundle/skills/spec-tasks/SKILL.md`: the boundary form.
  - Tests: `tests/entrypoints/test_derive.py`, `tests/scope/` (registry input).
- **New Dependencies**: None.

## 5. Error Handling & Edge Cases

- Fenced code blocks still end and hide everything, continuation included.
- The lines are joined with a space and split on commas exactly as a one-line value is.

## 6. Verification & Test Plan

- `tests/entrypoints/test_derive.py`: AC-01, AC-02.
- A registry test with a wrapped boundary: AC-03.
- `rg` the skill for the stated form: AC-04; `tests/test_bundle_budgets.py`.
- `just ci`.
