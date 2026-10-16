---
id: FB-bundle-budget-forces-waivers
title: Bundle size budgets left no room for a review fix in spec-delegate
scope: repo
kind: friction
category: other
target: tests/test_bundle_budgets.py
skill: spec-review
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: promoted
created_at: 2026-10-16
---

# [FB-bundle-budget-forces-waivers] Bundle size budgets left no room for a review fix in spec-delegate

Size budget, not a rule conflict: the byte limits on skill files decided the wording of a contract change.

## 1. Friction / Question (friction, question)

- **Context**: `SPEC-planning-effort-safeguards` changed one sentence in `spec-delegate/SKILL.md` and one in
  `spec/references/classification.md`.
- **Expectation**: A review finding asking for the full Planning effort row in `spec-delegate` could be fixed.
- **Actual**: Both files were within a few dozen bytes of their limits (`HEADROOM["spec-delegate"] = 7680`,
  `BUDGET = 8192`). The first edit failed `just ci`; the sentences were shortened twice, a neighbouring sentence in
  `classification.md` was trimmed to make room, and review finding 5 was waived for size.
- **Workaround (or Interpretation Chosen)**: Kept only the delegation decision in `spec-delegate` and pointed to
  `effort.md` for the full row; waived the finding with that reason.
- **Suggestion**: Restore headroom in `classification.md` and `spec-delegate/SKILL.md` (move detail to references),
  or have the budget test report the remaining bytes so authors see the margin before editing.

## Diagnostic Details

- **Reproduction**: Add about 100 bytes to either file and run `just test`.
- **Expected / Actual**: Expected room for a one-sentence clarification; actual failures
  `test_within_budget[skills/spec/references/classification.md]` (8256 > 8192) and
  `test_restructured_skills_keep_headroom[spec-delegate]` (7730 > 7680).
- **Versions**: devkit-spec at branch `dev-planning-effort-safeguards`, base `66b6f6d`.
- **Conditions**: Guidance-only change; no Python touched.
- **Workarounds Attempted**: Shortened the sentences (succeeded), trimmed an unrelated sentence (succeeded).
- **Related Assets**: `tests/test_bundle_budgets.py`, `src/devkit_spec/bundle/skills/spec-delegate/SKILL.md`,
  `src/devkit_spec/bundle/skills/spec/references/classification.md`, `review-01.yaml` finding 5.

## Evidence

```text
FAILED tests/test_bundle_budgets.py::test_within_budget[skills/spec/references/classification.md]
FAILED tests/test_bundle_budgets.py::test_restructured_skills_keep_headroom[spec-delegate]  (assert 7730 <= 7680)
after trimming: classification.md 8181 bytes, spec-delegate/SKILL.md 7679 bytes
```

- **Disposition**: `tests/test_bundle_budgets.py`: the budget follows devkit's raised `RULE-skill-document-size` default (12288 bytes, devkit 94085f4), the headroom is the budget minus 512, and a failure reports the size, the limit and the excess.
