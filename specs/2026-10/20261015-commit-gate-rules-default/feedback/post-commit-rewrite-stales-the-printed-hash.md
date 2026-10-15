---
id: FB-post-commit-rewrite-stales-the-printed-hash
title: A post-commit hook rewrites the commit, so the hash git commit prints is stale
scope: upstream
kind: friction
category: other
target: cgate post-commit hook (10-cgate)
skill: spec
agent: claude-code
origin: agent
severity: noise
recurring: false
status: forwarded
created_at: 2026-10-15
---

# [FB-post-commit-rewrite-stales-the-printed-hash] A post-commit hook rewrites the commit, so the hash git commit prints is stale

Nature: an external hook changes `HEAD` after `git commit` reports it.

## 1. Friction / Question (friction, question)

- **Context**: Committing in a devkit-spec task worktree, then recording the commit in an envelope (`--head`).
- **Expectation**: the `[<branch> <hash>]` line `git commit` prints names the commit that `HEAD` then points to.
- **Actual**: the post-commit dispatcher's `10-cgate` script rewrote the commit: same tree and message, a different
  author and committer date, and no `Co-Authored-By` trailer; `HEAD` moved to a new hash. An envelope or report that
  took the printed hash would name a commit no branch contains (and `envelope new --head` accepts it,
  `FB-envelope-head-accepts-unknown-commit`).
- **Workaround (or Interpretation Chosen)**: always read `git rev-parse HEAD` after the commit; every envelope in this
  bundle uses it.
- **Suggestion**: state in the `spec` skill's envelope reference that `--head` comes from `git rev-parse HEAD` after the
  commit, never from `git commit` output, since hooks may rewrite it.

## Diagnostic Details

- **Reproduction**: `git commit -m ...` in a clone whose `post-commit.d` holds `10-cgate`; compare the printed hash with
  `git rev-parse HEAD`.
- **Expected / Actual**: expected equal; actual printed `e09d961`, `HEAD` `23a9b82`, `git diff e09d961 23a9b82` empty.
- **Versions**: cgate version unknown; devkit `bc14046`.
- **Conditions**: hooks dispatched from the base repository's `.git/hooks`, shared by the worktree.
- **Workarounds Attempted**: `git rev-parse HEAD`; works.
- **Related Assets**: `.git/hooks/post-commit.d/10-cgate`, `spec/references/envelope.md`.

## Evidence

```text
[commit-gate-rules-default e09d961] docs: rely on devkit's default rules-check commit gate
$ git log --oneline -1   -> 23a9b82 docs: rely on devkit's default rules-check commit gate
$ git diff --stat e09d961 23a9b82   -> (empty)
e09d961 author date Thu Oct 15 11:06:48 2026 +0900; 23a9b82 author date Thu Oct 15 18:06:22 2026 +0900
```

- **Disposition**: cgate (owner's change, 2026-10-15): the post-commit hook now prints `[cgate] Commit rewritten: <old> -> <new> (use <new>)`.
