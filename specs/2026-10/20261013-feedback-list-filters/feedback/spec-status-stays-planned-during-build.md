---
id: FB-spec-status-stays-planned-during-build
title: "A spec stays planned until it is completed"
scope: bundle
kind: question
category: spec-ambiguity
target: "spec-tasks skill"
skill: spec-tasks
agent: claude-code
origin: agent
severity: noise
recurring: false
status: open
created_at: 2026-10-13
---

# [FB-spec-status-stays-planned-during-build] A spec stays planned until it is completed

## 1. Friction / Question (friction, question)

- **Context**: Building a Route 2 spec through every stage
- **Expectation**: The spec template offers draft, planned, in-progress and completed
- **Actual**: No skill or workflow stage sets `in-progress`; the spec read `planned` through build, review and reconcile until `devkit rules fix` set `completed`
- **Workaround (or Interpretation Chosen)**: Left it `planned`
- **Suggestion**: Name the step that sets `in-progress` (build-verify entry), or drop the value

## Evidence

```text
[WORKFLOW: direct-delivery unit=specs/2026-10/20261013-feedback-list-filters status=planned bound=yes]
[DONE: intent direction specify build-verify review-refine]
```
