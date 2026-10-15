---
id: FB-worker-scope-excludes-code-documentation
title: A worker cannot finish a change that adds an advisory code, because the code must be documented under docs/
scope: repo
kind: friction
category: instruction-conflict
target: src/devkit_spec/bundle/subagents/worker.md
skill: spec-orchestrate
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: open
created_at: 2026-10-15
---

# [FB-worker-scope-excludes-code-documentation] A worker cannot finish a change that adds an advisory code, because the code must be documented under docs/

## 1. Friction / Question (friction, question)

- **Context**: Planning and delegating `SPEC-list-unknown-status`, whose task adds the `SPEC_LIST_STATUS_UNKNOWN`
  notice, to a `worker` in orchestration mode.
- **Expectation**: the task's `_Boundary:` paths become the worker's write scope (`spec-orchestrate` §3 step 3), and
  the worker returns a build whose checks pass.
- **Actual**: `tests/test_documented_codes.py` requires every code under `src/` to appear in a `docs/` document, while
  the worker contract denies `docs/`. The first `tasks.md` put the capability document in the boundary; it had to be
  removed, the worker was told to expect one failing test, and the host added the code-table row before committing.
- **Workaround (or Interpretation Chosen)**: host edit of the code-table row after validating the worker diff, in
  the same commit as the build; the remaining Living Spec wording followed in `living-spec-draft`.
- **Suggestion**: either let the caller grant the worker a named `docs/` path for a code table (an explicit
  exception in the contract), or state in `spec-orchestrate` §3 step 4 that the host adds documentation a check
  requires before the build commit, and in `spec-tasks` that a worker task's boundary excludes `docs/`.

## Diagnostic Details

- **Reproduction**: a worker task that adds a new `code = "SPEC_..."` class; run `just test` in the worktree.
- **Expected / Actual**: expected all tests pass; actual `test_every_code_is_documented` fails for the new code.
- **Versions**: devkit 0.1.1; devkit-spec base `ed2dd0d`.
- **Conditions**: orchestration mode, worker `native` on Claude Code.
- **Workarounds Attempted**: host-added code-table row; `just test` 721 passed.
- **Related Assets**: `subagents/worker.md`, `spec-orchestrate` §3, `tests/test_documented_codes.py`,
  `CAP-DOCS-document-lookup`.

## Evidence

```text
worker.md: Denied: anything outside the worktree, the unit's `spec.md`, `plan.md`, `reconcile.md` and envelopes, `docs/`, ...
tests/test_documented_codes.py: """Every advisory code devkit-spec defines is documented under ``docs/``"""
worker run: test_every_code_is_documented: AssertionError: assert ['SPEC_LIST_STATUS_UNKNOWN'] == []; 1 failed, 720 passed
```
