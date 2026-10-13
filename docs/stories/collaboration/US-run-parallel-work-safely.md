---
id: US-run-parallel-work-safely
title: Run Parallel Work Safely
summary: An orchestrating agent or developer runs several spec bundles in parallel task worktrees and sees, before and during the work, which documents and code paths the tasks share, so it can schedule them and order their integration.
area: collaboration
actor: AI coding agent (orchestrator) or developer
status: active
created_at: 2026-10-13
capabilities:
  - CAP-COLL-work-scope-registry
  - CAP-TRACE-code-entrypoints
  - CAP-DLV-project-policy
---

# [US-run-parallel-work-safely] Run Parallel Work Safely

## 1. User Story Narrative

- **As a**: AI coding agent orchestrating several tasks, or a developer running them side by side
- **I want to**: see which Living Spec documents and code paths planned and running tasks share, and how much of
  their scope is still unknown
- **So that**: I decide what runs in parallel and in which order work is integrated before conflicts appear, without
  any task being blocked by a lock

---

## 2. Background & Context

With `[tool.spec] worktree = true` (`devkit spec policy` prints `worktree=yes`) every formal task runs in its own
devkit task worktree. Each task's scope comes from its declarations (`target-docs.md` and `reconcile.md` targets,
`tasks.md` `_Boundary` entries, the targets' `entrypoints`) and from what Git observes in its worktree. The work-scope
registry lives in the Git common directory, so every worktree of the repository shares it without configuration.

---

## 3. Acceptance Criteria (Given / When / Then)

### Scenario 1: Two proposals are compared before work starts
- **Given**: two proposals whose `target-docs.md` both list the same capability file
- **When**: the orchestrator runs `devkit spec scope compare --proposal <a> --proposal <b>`
- **Then**: the output has one `[PAIR: ... docs=1 ...]` line with an `[EVIDENCE: <path> ... kind=doc ...]` line and a
  `[SUMMARY: sets=2 pairs=1 overlapping=1]` line, and nothing is written

### Scenario 2: A running task sees its overlaps after writing its tasks
- **Given**: two task worktrees, each registered with `devkit spec scope register --spec <dir>`, whose `tasks.md`
  boundaries share a source directory
- **When**: one of them runs `devkit spec scope update --spec <dir>`
- **Then**: it prints the pair with `kind=code` evidence and `[SCOPE_ACK: status=applied ... overlaps=1 ...]`, and
  the overlap does not prevent either task from writing

### Scenario 3: Unknown scope is counted, not hidden
- **Given**: a spec whose `reconcile.md` targets a capability without `entrypoints`
- **When**: the scope is compared or updated
- **Then**: the input is counted as unresolved with `reason=no-entrypoints`, never read as "no overlap"

### Scenario 4: A finished task leaves the registry
- **Given**: a registered task whose worktree was removed by a successful `devkit worktree finish`
- **When**: the agent runs `devkit spec scope sweep --apply` in the base checkout
- **Then**: the record is reported as `[SWEEP: <task> verdict=removed reason=worktree-missing ...]` and is gone,
  while a record whose revision changed since it was read is kept with `SPEC_SCOPE_STALE_REVISION`
