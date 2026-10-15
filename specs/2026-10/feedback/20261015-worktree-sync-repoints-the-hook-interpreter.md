---
id: FB-worktree-sync-repoints-the-hook-interpreter
title: devkit sync in a task worktree points the shared hooks' fallback interpreter at that worktree
scope: upstream
kind: friction
category: tool-error
target: devkit sync (post-sync gate-hooks extension)
skill: spec-integrate
agent: claude-code
origin: agent
severity: workaround
recurring: true
status: open
created_at: 2026-10-15
---

# [FB-worktree-sync-repoints-the-hook-interpreter] devkit sync in a task worktree points the shared hooks' fallback interpreter at that worktree

## 1. Friction / Question (friction, question)

- **Context**: Finishing task worktrees (`devkit worktree finish <slug> --merge`) after running `devkit sync` inside
  them, then checking `devkit gate status` in the base checkout.
- **Expectation**: the hooks live in the common Git directory and serve every worktree, so their fallback interpreter
  stays valid when one worktree is removed.
- **Actual**: the post-sync `gate-hooks` extension reinstalls the shared dispatchers with the interpreter running the
  sync, the task worktree's `.venv/bin/python3`. After `finish` removes the worktree, `gate status` in the base
  reports `python_ok=false` for `pre-commit` and `commit-msg`. Commits in the base still work, because the entry
  prefers the committing worktree's own `.venv`, but any checkout without one would hit
  `GATE_INTERPRETER_UNAVAILABLE`.
- **Workaround (or Interpretation Chosen)**: `uv run devkit gate install` in the base after each finish.
- **Suggestion**: keep an existing valid fallback when a linked worktree syncs (or record the main worktree's
  interpreter), or have `devkit worktree finish` repair a fallback that pointed into the removed worktree.

## Diagnostic Details

- **Reproduction**: `devkit worktree start <slug>`; `uv run devkit sync` inside it; `devkit worktree finish <slug>
  --merge` from the base; `devkit gate status` in the base.
- **Expected / Actual**: expected `python_ok=true`; actual `python=<removed worktree>/.venv/bin/python3 python_ok=false`.
- **Versions**: devkit `bc14046`.
- **Conditions**: hooks shared through the common Git directory; seen after two finishes in one session.
- **Workarounds Attempted**: `devkit gate install` in the base; `python_ok=true` again.
- **Related Assets**: devkit `gate-hooks` post-sync extension, `devkit gate install`, `devkit worktree finish`.

## Evidence

```text
[WORKTREE_FINISHED: commit-gate-rules-default ... merged=yes push=pushed removed=yes branch_deleted=yes]
[HOOK: pre-commit state=managed python=<task-worktree>/.venv/bin/python3 python_ok=false scripts=10-cgate,20-devkit]
$ uv run devkit gate install   (base)
[HOOK: pre-commit state=managed python=<base>/.venv/bin/python3 python_ok=true scripts=10-cgate,20-devkit]
```

