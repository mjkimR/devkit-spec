---
id: FB-feedback-hidden-in-completed-bundles
title: "Open feedback in a completed bundle is hidden without --history"
scope: bundle
kind: suggestion
category: spec-ambiguity
target: "devkit spec list feedback"
skill: spec-feedback
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: open
created_at: 2026-10-13
---

# [FB-feedback-hidden-in-completed-bundles] Open feedback in a completed bundle is hidden without --history

## 2. Suggestion / Change Request (suggestion, change-request)

- **Current Procedure**: every file of a completed spec bundle is historical, its `feedback/` included, so
  `devkit spec list feedback --status open` omits feedback the `collect-feedback` stage records, which always runs
  after `living-spec-draft` completed the spec. Every caller must remember `--history`; `spec-next` and
  `envelope.md` did not until `SPEC-feedback-list-filters` added it.
- **Proposed Procedure**: treat feedback as never historical (specrig scanned every bundle's feedback), so open
  feedback is listed until a hygiene session changes its status.
- **Expected Benefit**: the G3 critical check and `/spec-next` see feedback recorded in the current task without a
  flag that is easy to forget.
- **Cost & Risk**: a contract change in `CAP-DOCS-document-model` (what is historical); `list --history` then no
  longer changes feedback results.
- **Attempted**: observed in this session; the flag was added to the assets as the fix within scope.

## Evidence

```text
$ devkit spec list feedback --status open -n 0
[PAGE: total=0 offset=0 limit=0 count=0 next=-]
$ devkit spec list feedback --status open --history -n 0
... [PAGE: total=9 offset=0 limit=0 count=9 next=-]
```
