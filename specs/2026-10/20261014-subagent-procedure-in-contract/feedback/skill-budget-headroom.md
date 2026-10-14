---
id: FB-skill-budget-headroom
title: spec-delegate and spec skills sit at the 8192-byte budget
scope: bundle
kind: friction
category: context-overflow
target: src/devkit_spec/bundle/skills/spec-delegate/SKILL.md
skill: spec-delegate
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: promoted
created_at: 2026-10-14
---

# [FB-skill-budget-headroom] spec-delegate and spec skills sit at the 8192-byte budget

## 1. Friction / Question (friction, question)

- **Context**: Adding a per-role payload table to `spec-delegate` while removing caller-only sections from the role contracts.
- **Expectation**: A small, well-placed addition fits the skill document budget (`tests/test_bundle_budgets.py`, 8192 bytes).
- **Actual**: The edit came to 9004 bytes; four trimming passes of unrelated sentences were needed to reach 8176. `spec/SKILL.md` is at 8144.
- **Workaround (or Interpretation Chosen)**: Shortened wording across Steps 1 to 6 without dropping a rule.
- **Suggestion**: Move a stable block (the per-host invocation list or the envelope command block) into a reference under `spec-delegate/references/`, and do the same for the `spec` routing table, so the next edit to either skill has headroom.

## Evidence

```text
first edit: 9004 bytes; after trims: 8493, 8325, 8270, 8202, 8176
spec/SKILL.md: 8144 bytes (was 8183 before this change)
```

- **Disposition**: `SPEC-subagent-procedure-in-contract` (AC-08): `spec-delegate` and `spec` restructured with the skill-authoring playbook to 7418 and 7677 bytes, guarded by `tests/test_bundle_budgets.py`.
