---
id: FB-return-keeps-later-disk-stages-done
title: "workflow return does not reopen stages whose disk checks still pass"
scope: bundle
kind: question
category: tool-error
target: "devkit workflow return"
skill: spec-review
agent: claude-code
origin: agent
severity: noise
recurring: false
status: open
created_at: 2026-10-13
---

# [FB-return-keeps-later-disk-stages-done] workflow return does not reopen stages whose disk checks still pass

## 1. Friction / Question (friction, question)

- **Context**: a defect found after review; the unit was returned to `build-verify` as the workflow's `RETURNS`
  directs.
- **Expectation**: the unit sits in `build-verify` until a new review round passes.
- **Actual**: `return` recorded a decision, and `next` placed the unit straight back in `collect-feedback`: the
  earlier `reverify-01.yaml` still satisfies `envelope-review-passed`.
- **Workaround (or Interpretation Chosen)**: recorded a second review round (`review-02`, `reverify-02`) by hand.
- **Suggestion**: decide whether a return voids envelopes recorded before it, or say in `spec-review` that a
  post-review defect needs a new review round, which `return` does not enforce.

## Evidence

```text
[RETURNED: decisions/03-return-build-verify.yaml to=build-verify]
[DONE: intent direction specify build-verify review-refine living-spec-draft]
[STAGE: collect-feedback human_gate=- role=developer isolation=none]
```
