---
id: FB-commit-intent-before-planning-worktree
title: "Make the proposal intent commit explicit before branching"
scope: repo
kind: change-request
category: instruction-conflict
target: "src/devkit_spec/bundle/skills/spec/references/classification.md"
skill: spec
agent: codex
origin: agent
severity: workaround
recurring: false
status: open
created_at: 2026-10-16
---

# [FB-commit-intent-before-planning-worktree] Make the proposal intent commit explicit before branching

## 2. Suggestion / Change Request

- **Current Procedure**: Backlog records proposal plan-intent; the Planning worktree starts from the base HEAD.
  The proposal Backlog instruction does not explicitly commit the gate before starting that branch.
- **Proposed Procedure**: State that the recorded proposal intent is committed before starting plan-<slug>, just as
  inline spec Planning explicitly commits its input. Preserve unrelated base changes.
- **Expected Benefit**: A fresh Planning worktree contains its approval rather than stopping at an already-decided gate.
- **Cost & Risk**: Instruction-only follow-up; keep base commit scope restricted to the approved Backlog record.
- **Attempted**: Used a separate intent-record commit before worktree start in this feature; the record was present.

## Diagnostic Details

- **Reproduction**: Compare the proposal Backlog recording instruction with worktree start's base-HEAD semantics.
- **Expected / Actual**: Explicit committed input; actual proposal procedure names record/start without the commit.
- **Versions**: devkit-spec 4e17ead.
- **Conditions**: Proposal-depth work with a separate Planning worktree.
- **Workarounds Attempted**: Commit the intent record first, then start the worktree.
- **Related Assets**: spec/references/classification.md, spec/references/worktree.md, devkit worktree start.

## Evidence

classification.md Backlog records plan-intent but its proposal bullet has no commit step. The inline-spec bullet
explicitly says record and commit. worktree.md states that a new worktree is created from the base HEAD.
`SPEC-planning-feedback-capture` used a separate intent commit before its Planning branch.
