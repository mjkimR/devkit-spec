---
id: FB-skill-byte-budgets-leave-no-headroom
title: Spec skill references sit at the byte budget, so policy wording changes need trimming elsewhere
scope: repo
kind: suggestion
category: other
target: src/devkit_spec/bundle/skills/spec/references/completion.md
skill: spec
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: promoted
created_at: 2026-10-15
---

# [FB-skill-byte-budgets-leave-no-headroom] Spec skill references sit at the byte budget, so policy wording changes need trimming elsewhere

Nature: document size budget pressure on frequently edited guidance.

## 2. Suggestion / Change Request (suggestion, change-request)

- **Current Procedure**: `tests/test_bundle_budgets.py` caps every skill document at 8192 bytes (`spec` and
  `spec-delegate` at 7680). Adding the policy-level semantics to `completion.md` pushed it to 8210 bytes; it passed
  only after shortening unrelated phrases.
- **Proposed Procedure**: Move the Git policy section of `completion.md` (and the PR/merge paragraph of
  `spec-integrate`) into a dedicated `references/git-policy.md` that both link, as `spec` and `spec-delegate` were
  restructured for headroom.
- **Expected Benefit**: The next policy change (the gate-answer wording fix touches the same files) edits one
  reference with room, instead of trimming wording to fit.
- **Cost & Risk**: One more reference to read for Git decisions; links must stay resolvable (checked by the test).
- **Attempted**: Hypothesis; this change trimmed wording instead.

## Diagnostic Details

- **Reproduction**: Edit the `GIT_POLICY` bullet of `completion.md`; `wc -c` exceeds 8192.
- **Expected / Actual**: Expected room for a paragraph; actual 18 bytes over, now 7 bytes under.
- **Versions**: devkit-spec base `79b3cb1` plus this change.
- **Conditions**: not applicable.
- **Workarounds Attempted**: shortened two phrases in the same bullet.
- **Related Assets**: `tests/test_bundle_budgets.py`, `skills/spec/references/completion.md`,
  `skills/spec-integrate/SKILL.md`, `skills/spec/SKILL.md`.

## Evidence

```text
$ wc -c skills/spec/references/completion.md   -> 8210 (before trimming), 8185 (after)
$ wc -c skills/spec-integrate/SKILL.md        -> 8152 before, 8118 after
$ wc -c skills/spec/SKILL.md                  -> 7653 before (HEADROOM 7680), 7622 after
```

- **Disposition**: S-Lane: the Git policy levels moved from `spec/references/completion.md` to `spec/references/git-policy.md`, and the payload field table from `spec/references/envelope.md` to `spec-delegate/references/payload.md` (completion 6.7 KB, envelope 7.7 KB).
