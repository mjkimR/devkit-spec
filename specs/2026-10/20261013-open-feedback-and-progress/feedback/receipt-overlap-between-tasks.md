---
id: FB-receipt-overlap-between-tasks
title: "Parallel tasks overlap on the installation receipt"
scope: bundle
kind: question
category: missing-capability
target: "devkit spec scope query"
skill: spec-tasks
agent: claude-code
origin: agent
severity: noise
recurring: false
status: promoted
created_at: 2026-10-13
---

# [FB-receipt-overlap-between-tasks] Parallel tasks overlap on the installation receipt

## 1. Friction / Question (friction, question)

- **Context**: two tasks in parallel worktrees both changed bundle assets and ran `devkit sync`.
- **Expectation**: the registry flags overlaps that need coordination.
- **Actual**: it reports `.devkit/installation.json` as an observed code overlap; the receipt is regenerated, so the
  second integration resolves it by rerunning `devkit sync` after the rebase, which no skill says.
- **Workaround (or Interpretation Chosen)**: planned the resync after rebasing the later task.
- **Suggestion**: mark generated files (the receipt) as `regenerate` overlaps, or say in `spec-integrate` Step 1 that
  a conflict in `.devkit/installation.json` is resolved by `devkit sync`.

## Evidence

```text
[EVIDENCE: .devkit/installation.json a=SPEC-boundary-continuation-lines b=SPEC-open-feedback-and-progress kind=code granularity=file ...]
```

- **Disposition**: src/devkit_spec/bundle/skills/spec/references/worktree.md: S-Lane; a receipt conflict when integrating the base is resolved by `devkit sync`; the registry still reports the overlap, which is real
