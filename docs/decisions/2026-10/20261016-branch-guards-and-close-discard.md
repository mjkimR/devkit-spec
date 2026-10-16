---
id: ADR-branch-guards-and-close-discard
title: Guard Development on dev-<slug> in every checkout and close tasks with finish --discard
summary: "A spec unit is created and a proposal handed off only on dev-<slug> in any checkout; the integration path no longer forces a worktree, the scope registry tracks linked worktrees only, and a close drops its branch with finish --discard."
status: accepted
created_at: 2026-10-16
supersedes: ADR-worktree-and-pull-request-levels
---

# [ADR-branch-guards-and-close-discard] Guard Development on dev-<slug> in every checkout and close tasks with finish --discard

- **Status**: Accepted
- **Date**: 2026-10-16
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `CAP-DLV-project-policy`, `CAP-DLV-spec-bundles`,
  `CAP-DLV-proposal-incubation`, `CAP-COLL-work-scope-registry`, `ARCH-08-cross-cutting`

---

## 1. Context & Problem Statement

`ADR-worktree-and-pull-request-levels` made `[tool.spec] worktree` and devkit's `[worktree] pull_request` `auto` or
`required` levels, made a pull-request-bound task run in a worktree, and guarded the handoff only in linked
worktrees. With activity branches (`ADR-run-records-and-activity-branches`) a `direct` task may run on `dev-<slug>` in
the base checkout (`devkit worktree start --no-worktree`). A review of the local flow found that a handoff on the base
branch then deleted the accepted proposal from the base, that `devkit spec new` could create a unit on any branch, that
a base-checkout task's scope record leaked past its finish, and that a close had no allowed way to drop an unmerged
branch. The strategy layer (workbench `docs/strategy-layer/01-master-flow.md` §4.7, §7.4, `03-policy.md` §3) settles
the rules.

---

## 2. Decision Drivers

- A unit lands only on its own activity branch, wherever the checkout is.
- The worktree is chosen for isolation, not by the integration path.
- No force-deletion outside a decided close.

---

## 3. Considered Options

### Option 1: Branch guards in every checkout, worktree by isolation, close through finish --discard (Selected)
- **Overview**: the handoff and `devkit spec new` refuse any branch but `dev-<slug>` in Git; the worktree level stays
  `auto`/`required` for `direct` mode with the 03 §3 criteria; the work-scope registry tracks linked worktrees only;
  devkit's `finish --discard` drops a closed task's branch and runs the post-finish cleanup.
- **Pros**: one rule for every checkout; small PR-bound tasks need no worktree; closes leave no records behind.
- **Cons**: a project that relied on creating a spec on its base branch must start `dev-<slug>` first.

### Option 2: Keep the guards to linked worktrees
- **Overview**: as before.
- **Cons**: the base checkout, now a normal place to work, stays unguarded.

---

## 4. Decision Outcome

Option 1:

- Both levels stay `"auto"` (default) or `"required"`, booleans rejected. `[tool.spec] worktree` applies to `direct`
  mode: `required` runs every `spec` and `proposal` activity in a worktree; under `auto` a worktree is used when the
  checkout holds unrelated changes, another task is in flight there or the user asks. The integration path does not
  choose it: a pull-request-bound task may run on its branch in the current checkout.
- In a Git checkout, linked or base, `devkit spec proposal handoff` (`SPEC_PROPOSAL_WRONG_WORKTREE`) and
  `devkit spec new` (`SPEC_WRONG_BRANCH`) refuse any branch but `dev-<slug>`. Outside Git nothing is checked. A slug is
  at most 59 characters so its activity branches fit devkit's 64.
- The work-scope registry tracks linked worktrees: a handoff or task in the base checkout registers nothing, and a
  record the base checkout holds anyway is released when its `--no-worktree` branch is finished or discarded.
- A close (depth escalation, supersede, abandon) drops the task's unmerged branch with
  `devkit worktree finish dev-<slug> --discard`, on the authority of the close's decider; no other path force-deletes
  a branch.

---

## 5. Consequences

- Inline Planning for `spec` depth starts `dev-<slug>` before `devkit spec new`.
- The post-finish extension releases a base-checkout record when the finish result's path is the base checkout.
- The rejection, decomposition and close procedures name `finish --discard` and the closing answers of open
  questions (01 §5.2, §6.2, §7.4).
