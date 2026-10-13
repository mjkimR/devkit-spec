---
id: FB-integrate-assumes-a-remote-base
title: "spec-integrate merges origin/main even when the base is ahead of it"
scope: bundle
kind: friction
category: instruction-conflict
target: "spec-integrate skill"
skill: spec-integrate
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: open
created_at: 2026-10-13
---

# [FB-integrate-assumes-a-remote-base] spec-integrate merges origin/main even when the base is ahead of it

## 1. Friction / Question (friction, question)

- **Context**: Step 1 of `spec-integrate` under `pull_request=no`, with a local commit on the base not yet pushed.
- **Expectation**: integrating the base makes `devkit worktree finish --merge` a fast-forward.
- **Actual**: Step 1 says `git fetch origin` and `git merge origin/main`; the local base `main` was one commit ahead
  of `origin/main`, so that merge would integrate nothing and `finish --merge` would stop with
  `WORKTREE_MERGE_NOT_FF`.
- **Workaround (or Interpretation Chosen)**: integrated the local base branch (`git rebase main`).
- **Suggestion**: name the base checkout's branch (the one `finish` fast-forwards), after `git pull --ff-only` in
  the base, instead of `origin/main`.

## Evidence

```text
$ git -C <base> status -sb
## main...origin/main [ahead 1]
```
