---
id: FB-integrate-merge-message-fails-commit-msg-gate
title: spec-integrate's base merge uses Git's default message, which a Conventional Commits gate refuses
scope: repo
kind: friction
category: instruction-conflict
target: src/devkit_spec/bundle/skills/spec-integrate/SKILL.md
skill: spec-integrate
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: open
created_at: 2026-10-15
---

# [FB-integrate-merge-message-fails-commit-msg-gate] spec-integrate's base merge uses Git's default message, which a Conventional Commits gate refuses

## 1. Friction / Question (friction, question)

- **Context**: Integrating the base into the second orchestration unit (`SPEC-list-unknown-status`), `spec-integrate`
  Step 1.
- **Expectation**: Step 1 shows `git merge <base-branch>` and nothing more is needed for a conflict-free merge.
- **Actual**: the commit-msg hook (`10-cgate`) refused Git's default `Merge branch 'main' into ...` message as not
  Conventional Commits, leaving the merge uncommitted (`MERGE_HEAD` set).
- **Workaround (or Interpretation Chosen)**: committed the merge with `git commit -m "chore(merge): integrate main into
  <slug>"`.
- **Suggestion**: in Step 1, merge with `git merge --no-edit -m "<conventional subject>" <base-branch>` (or say to
  commit the merge with a message the repository's commit conventions accept), so the step does not stop half-done.

## Diagnostic Details

- **Reproduction**: `git merge main` in a task worktree of a repository whose commit-msg hook enforces Conventional
  Commits.
- **Expected / Actual**: expected a merge commit; actual the hook's refusal and an unfinished merge.
- **Versions**: cgate version unknown; devkit-spec `ed2dd0d`.
- **Conditions**: devkit commit gate plus `10-cgate` in `commit-msg.d`.
- **Workarounds Attempted**: explicit conventional message; merge committed as `f7b8b9c`.
- **Related Assets**: `spec-integrate` Step 1, the `git-commits` instruction.

## Evidence

```text
spec-integrate Step 1: git merge <base-branch>   # the base checkout's branch (it may be ahead of origin); or rebase
$ git merge --no-edit -m "Merge branch 'main' into list-unknown-status ..." main
Expected format: <type>(<scope>): <subject> (e.g., 'feat: add user login', 'fix(auth): handle timeout')
Rewrite your commit message following Conventional Commits format.
```
