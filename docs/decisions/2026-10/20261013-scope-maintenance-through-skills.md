---
id: ADR-scope-maintenance-through-skills
title: Maintain the work-scope registry through the skills
summary: Because devkit's workflow next and worktree finish cannot call devkit-spec, the spec skills keep the scope registry current (register, update, sweep and prune), and cleanup runs scope sweep --apply after a successful worktree finish instead of releasing before it.
status: superseded
created_at: 2026-10-13
---

# [ADR-scope-maintenance-through-skills] Maintain the work-scope registry through the skills

- **Status**: Superseded by `ADR-cleanup-after-worktree-finish`
- **Date**: 2026-10-13
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `CAP-COLL-work-scope-registry`, `CAP-HARN-agent-guidance`, `ARCH-06-runtime-view`

---

## 1. Context & Problem Statement

In specrig, the registry was kept current by its own commands: `workflow next --scope-ack` updated a task's scope,
`worktree finish` released the record after its merge check and swept after removing the worktree, and proposal
cleanup ran on finish. In devkit, `devkit workflow next` and `devkit worktree finish` know nothing about devkit-spec
and offer no extension point to call it. The registry still has to follow each task from registration to cleanup.

---

## 2. Decision Drivers

- devkit stays SDD-agnostic: no devkit-spec calls inside devkit commands.
- A refused finish never leaves a live task unregistered.
- Every step is a deterministic command an agent can run and check.

---

## 3. Considered Options

### Option 1: The skills call the scope commands; sweep after a successful finish (Selected)
- **Overview**: `devkit spec proposal handoff` registers itself in a linked worktree under `[tool.spec] worktree = true`;
  after `devkit spec new` in a task worktree the `spec` skill runs `devkit spec scope register --spec <dir>`;
  `spec-tasks` and `spec-sync` run `devkit spec scope update --spec <dir>`; after `devkit worktree finish` succeeds
  the base runs `devkit spec scope sweep --apply` and `devkit spec proposal prune <slug>`.
- **Pros**: no devkit change; the removed worktree's record becomes stale and the sweep removes it; a refused finish
  leaves the task registered.
- **Cons**: the registry is only as current as the skills' compliance.

### Option 2: The skills release before finish
- **Overview**: `devkit spec scope release` first, then `devkit worktree finish`.
- **Pros**: the record is gone at once.
- **Cons**: a refused finish (`WORKTREE_UNMERGED`, `WORKTREE_DIRTY`, `WORKTREE_BASE_BEHIND`, ...) leaves a task that is
  still running invisible to the other worktrees.

### Option 3: Hooks in devkit for devkit-spec
- **Overview**: let `workflow next` and `worktree finish` call registered callbacks.
- **Pros**: automatic maintenance.
- **Cons**: an extension mechanism in devkit for one plugin's registry; devkit's commands would depend on a plugin's
  success.

---

## 4. Decision Outcome

We decided to adopt **Option 1**.

**Rationale**: it keeps devkit unchanged and orders cleanup so that the only state a failure can leave is a task that
is still registered, which is the safe side for overlap detection.

---

## 5. Consequences

- **Positive**: `release` without a token is a successful no-op, so a cleanup step needs no condition;
  `SPEC_SCOPE_TOKEN_MISSING` on update means the worktree takes no part and the step is skipped; an abandoned task is
  withdrawn with `devkit spec scope release -w <worktree>`.
- **Negative / Risks**: a skipped skill step leaves a record stale until the next sweep; worktree guard refusals are
  not journaled, so the journal has no `guard` events and no `worktree-start`, `worktree-finish` or `workflow-next`
  sources.
- **Follow-ups**: a handoff registration failure is a `SPEC_SCOPE_REGISTER_FAILED` warning whose `[FIX]` the agent runs.
