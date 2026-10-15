---
id: FB-worker-checkbox-leaves-spec-status-to-host
title: A worker's checked task leaves spec.md status behind, and only the host may fix it
scope: repo
kind: friction
category: instruction-conflict
target: src/devkit_spec/bundle/skills/spec-orchestrate/SKILL.md
skill: spec-orchestrate
agent: claude-code
origin: agent
severity: workaround
recurring: true
status: open
created_at: 2026-10-15
---

# [FB-worker-checkbox-leaves-spec-status-to-host] A worker's checked task leaves spec.md status behind, and only the host may fix it

## 1. Friction / Question (friction, question)

- **Context**: Validating and committing a worker's build (`spec-orchestrate` §3 step 4, `spec-delegate` Steps 4 to 6).
- **Expectation**: the worker contract has the worker check off its tasks in `tasks.md`, and the procedure for the
  host then stages the write-scope paths, runs `devkit rules check --staged` and commits.
- **Actual**: the checked box makes `RULE-spec-progress` warn that `spec.md` is still `planned`. The worker contract
  denies `spec.md`, and neither `spec-orchestrate` nor `spec-delegate` Step 6 (Worker) says the host sets the status,
  so the step is discovered from the warning. It happened in both units of the session.
- **Workaround (or Interpretation Chosen)**: the host ran `devkit rules fix <dir>/spec.md` (status `in-progress`) and
  staged `spec.md` with the worker's paths, recording it as an assumption in the worker envelope.
- **Suggestion**: add the status step to `spec-delegate` Step 6 (Worker) or `spec-orchestrate` §3 step 4: after
  validating, run `devkit rules fix <dir>/spec.md` and stage it with the build.

## Diagnostic Details

- **Reproduction**: worker checks a task in `tasks.md`; host stages it and runs `devkit rules check --staged`.
- **Expected / Actual**: expected a clean staged check; actual one `RULE-spec-progress` warning.
- **Versions**: devkit 0.1.1; devkit-spec base `ed2dd0d`.
- **Conditions**: orchestration mode, Route 2 `direct-delivery`, worker role `native` on Claude Code.
- **Workarounds Attempted**: `devkit rules fix` on `spec.md`; staged check then clean.
- **Related Assets**: `spec-orchestrate` §3, `spec-delegate` Step 6, `subagents/worker.md` (write boundaries).

## Evidence

```text
worker.md: Denied: anything outside the worktree, the unit's `spec.md`, `plan.md`, `reconcile.md` and envelopes, ...
[VIOLATION: RULE-spec-progress severity=warning file=specs/2026-10/20261015-search-blank-query/tasks.md line=1 status=open message="Spec status 'planned' of specs/2026-10/20261015-search-blank-query/spec.md is behind its tasks: 1 of 1 checked" remediation="Run `devkit rules fix specs/2026-10/20261015-search-blank-query/spec.md` to set status: in-progress in spec.md"]
```
