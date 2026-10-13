---
id: FB-intent-stage-lists-a-proposal-artifact
title: "The direct-delivery intent stage lists a proposal artifact"
scope: bundle
kind: question
category: docs-mismatch
target: "src/devkit_spec/bundle/workflows/direct-delivery.md"
skill: spec
agent: claude-code
origin: agent
severity: noise
recurring: false
status: open
created_at: 2026-10-13
---

# [FB-intent-stage-lists-a-proposal-artifact] The direct-delivery intent stage lists a proposal artifact

## 1. Friction / Question (friction, question)

- **Context**: Reading `devkit workflow show direct-delivery` before G1 of a Route 2 task
- **Expectation**: Route 2 has no proposal; the intent stage's artifacts are the spec bundle
- **Actual**: The stage lists `docs/proposals/PROP-<slug>/proposal.md` as an artifact
- **Workaround (or Interpretation Chosen)**: Ignored it: Route 2 creates no proposal
- **Suggestion**: Drop the proposal path from direct-delivery's intent stage, or say when it applies

## Evidence

```text
[STAGE: intent name="G1 intent" human_gate=intent ...]
[ARTIFACTS: docs/proposals/PROP-<slug>/proposal.md specs/<YYYY-MM>/<YYYYMMDD>-<slug>/]
```
