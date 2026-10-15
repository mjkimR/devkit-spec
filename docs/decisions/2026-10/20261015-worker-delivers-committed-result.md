---
id: ADR-worker-delivers-committed-result
title: Workers deliver committed, self-contained results
summary: "An orchestration worker commits its build, complete and through the commit gate, and the host validates the cumulative committed range; a failing result is blocked and fixed by further commits, never discarded, so local and pull-request-based orchestration share one contract."
status: accepted
created_at: 2026-10-15
---

# [ADR-worker-delivers-committed-result] Workers deliver committed, self-contained results

- **Status**: Accepted
- **Date**: 2026-10-15
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `CAP-DLV-delivery-workflows`, the `worker` role contract, `spec-delegate`,
  `spec-orchestrate`, `spec-tasks`

---

## 1. Context & Problem Statement

`SPEC-orchestration-mode` introduced the `worker` role with every role's Git rule: read only. The worker left its
build unstaged; the host compared the working-tree diff with the write scope, then staged and committed. In the first
pilot the host also had to finish what the worker could not touch: the spec status `RULE-spec-progress` asks for once
tasks are checked, and a code-table row under `docs/` a test requires for a new advisory code. That hand-off only
works when host and worker share a working tree. When workers run elsewhere and deliver through their own branch or
pull request, their checks and the commit gate run before any host can repair the result, so a result that needs
repair fails there, and the host ends up doing the delegated work.

---

## 2. Decision Drivers

- One contract for local worktrees and pull-request-based (cloud) workers, so orchestration scales out.
- A clear cut between delegated and host work: the host validates and integrates; it does not finish builds.
- The commit gate and the unit's checks judge the worker's own output.
- Delegated work is never silently lost: a rejected result stays inspectable and fixable.

---

## 3. Considered Options

### Option 1: The worker commits a complete result; failures are blocked (Selected)
- **Overview**: the worker stages only its write scope, commits on the unit branch through the commit gate and
  returns the head; its result includes the task checkboxes, the spec status set by `devkit rules fix` and the `docs/`
  paths its tasks' `_Boundary:` name. The host validates the cumulative range from the last accepted head.
- **Pros**: the same result shape locally and in a pull request; the commit gate runs on the worker's work; the host's
  role shrinks to validation and integration.
- **Cons**: the worker gains a Git write action; a rejected range stays in the branch history.

### Option 2: Unstaged result, the host repairs and commits (status quo)
- **Overview**: as before, with added host steps for the spec status and required documentation.
- **Pros**: no role writes to Git.
- **Cons**: impossible where the worker's branch is checked before the host sees it; the host keeps finishing
  delegated work.

### Option 3: The worker commits; failures are reset or the pull request is closed
- **Pros**: a clean branch after a rejection.
- **Cons**: discards delegated work and its evidence; differs between local and pull-request delivery.

---

## 4. Decision Outcome

We decided to adopt **Option 1**.

- The `worker` role's Git actions are `[read, commit]`: stage write-scope paths, commit on its unit branch through the
  commit gate, leave the worktree clean. It never pushes, merges, rebases, resets, amends, stashes or checks out;
  publishing a branch or pull request belongs to the execution environment. Every other role stays `[read]`.
- The result is self-contained: tasks checked, the spec's `status` set only through `devkit rules fix <unit>/spec.md`,
  `docs/` written only where a task's `_Boundary:` names it, every given check passing.
- The host validates the cumulative range from the last accepted head (initially the head recorded before spawning)
  to the returned head: it descends from that head, every changed path is in the write scope, `spec.md` changes only
  in `status`, the worktree is clean and the base checkout unchanged.
- A failed validation is recorded as a `failed` worker envelope, which blocks the unit from review and integration.
  The commits stay (no reset; a pull request stays open and blocked); further commits by the worker or the host fix
  it, reverting out-of-scope changes, and the next validation covers the cumulative range.

**Rationale**: Option 1 is the only option in which the delegated result is complete where it is produced, which is
what pull-request-based orchestration needs, and blocking keeps every attempt traceable.

---

## 5. Consequences

- **Positive**: the host no longer repairs worker output; a worker's branch is reviewable as is; the pilot's three
  worker frictions are resolved by the contract.
- **Negative / Risks**: a rejected range remains in the unit branch's history until it is fixed; a worker with Git
  write access must be trusted not to bypass the commit gate (`--no-verify` stays forbidden, and the range check
  catches out-of-scope paths).
- **Follow-ups**: `PROP-worktree-host-compatibility` evaluates worker processes per worktree and host-native
  isolation under this contract.
