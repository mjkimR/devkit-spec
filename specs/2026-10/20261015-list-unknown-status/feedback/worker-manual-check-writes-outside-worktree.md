---
id: FB-worker-manual-check-writes-outside-worktree
title: A worker's manual CLI check created a scratch workspace outside its worktree
scope: repo
kind: friction
category: instruction-conflict
target: src/devkit_spec/bundle/subagents/worker.md
skill: spec-delegate
agent: claude-code
origin: agent
severity: noise
recurring: false
status: open
created_at: 2026-10-15
---

# [FB-worker-manual-check-writes-outside-worktree] A worker's manual CLI check created a scratch workspace outside its worktree

## 1. Friction / Question (friction, question)

- **Context**: The `worker` of `SPEC-list-unknown-status` checked the notice output by hand before returning.
- **Expectation**: the contract says to work only in the worktree and never touch anything outside it; the caller's
  diff check covers the worktree and the base checkout.
- **Actual**: the worker created a scratch workspace in the session's scratch directory (outside both checkouts),
  could not remove it afterwards, and reported it under `unverified_areas`. The caller's diff check cannot see such
  writes; here they were harmless.
- **Workaround (or Interpretation Chosen)**: accepted the result, since no repository path changed; noted the leftover.
- **Suggestion**: give the worker a sanctioned place for throwaway fixtures (pytest `tmp_path` in a test, or an
  ignored path inside the worktree) and say so in the contract's procedure, so manual checks stay inside the checked
  boundary.

## Diagnostic Details

- **Reproduction**: unknown beyond this run; a worker verifying CLI output against a fixture workspace.
- **Expected / Actual**: expected no write outside the worktree; actual one scratch directory outside it.
- **Versions**: devkit 0.1.1; devkit-spec base `ed2dd0d`.
- **Conditions**: Claude Code worker sharing the session directory.
- **Workarounds Attempted**: not applicable.
- **Related Assets**: `subagents/worker.md` (Procedure step 1, Write boundaries), `spec-delegate` Step 5.

## Evidence

```text
worker.md: 1. Work only in the worktree. ... Never touch the caller's checkout.
worker return, unverified_areas: "A scratch workspace I used for a manual output check is still at <session scratch>/ws (outside the worktree; my attempt to remove it was not allowed)."
```
