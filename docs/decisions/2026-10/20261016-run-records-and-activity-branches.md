---
id: ADR-run-records-and-activity-branches
title: Record each run in one worker envelope and run each activity on its own branch
summary: A run's questions and problem live in its one worker envelope, answers and resolutions reference it, unresolved problems and unanswered questions hold every gate and the merge, and every activity runs on plan-<slug> or dev-<slug>, continued only through an explicit attach that devkit-spec verifies.
status: accepted
created_at: 2026-10-16
---

# [ADR-run-records-and-activity-branches] Record each run in one worker envelope and run each activity on its own branch

- **Status**: Accepted
- **Date**: 2026-10-16
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `CAP-DLV-delivery-workflows`, `CAP-DLV-proposal-incubation`,
  `CAP-DLV-project-policy`, `CAP-HARN-agent-guidance`

---

## 1. Context & Problem Statement

`ADR-task-kind-and-planning-depth` left Planning's question rounds, the problem and resolution records and the blocked
state to devkit envelope contracts adopted separately. Until they existed, the Host recorded its check of a worker's
committed range as a `validation` envelope and treated the latest failed one as the block, so two rules decided
whether a unit was blocked. Worktrees were named after the bare slug, so the Planning and the Development activity of
one slug could not each have a branch, and nothing verified that a resumed branch carried the unit it was resumed for.
devkit now ships the contracts (`question` fields in a `worker` envelope, `answer`, `resolution`, the hold on gates and
`worktree finish --merge`, activity branch names, `--no-worktree`, `--existing-branch` with the `devkit.attach_check`
extension point, stale-branch hygiene). The strategy layer's master flow (workbench
`docs/strategy-layer/01-master-flow.md` §4.7, §7.2 and §8) settles how spec-driven delivery uses them.

---

## 2. Decision Drivers

- One rule for blocked: a problem without a resolution that names it, whoever found it.
- A run's record is one file in every mode, so `cloud-pr`, where the run's container disappears, keeps the same trail.
- What another actor does later (answering, fixing) is its own record, written by that actor.
- devkit stays free of spec-driven knowledge; which unit belongs to which activity is checked here.

---

## 3. Considered Options

### Option 1: One worker envelope per run, references for answers and resolutions (Selected)
- **Overview**: every run ends with exactly one `worker` envelope holding its `questions` and `problem`; an `answer`
  names it in `answers_to`, a `resolution` in `resolves`. The Host's failed range check is a problem in the Host's
  own `worker` envelope; an accepted range writes nothing. There is no `question` or `validation` kind.
- **Pros**: one record per run, one blocked rule, answers and fixes traceable to the run that needed them.
- **Cons**: a Host that blocks a range writes a `worker` envelope although it is not a worker role.

### Option 2: Separate question and problem kinds
- **Overview**: a `question` envelope beside the `worker` envelope, a problem as its own kind.
- **Pros**: each record has one purpose.
- **Cons**: the same questions in two files, and two places that can disagree about why a run stopped.

---

## 4. Decision Outcome

Option 1, with activity branches:

- A `planning-worker` writes its questions with `--questions-file` in its `worker` envelope; the run that processes the
  answers records them first as an `answer` envelope. Any run that stops on a problem records `--problem`, `--tried`
  and `--recovery`; whoever actually fixes it commits a `resolution` with the fix. devkit holds the gates from the holding run's stage on, and the handoff, while a
  problem is unresolved or a question unanswered (gates passed before stay passed) and refuses `devkit worktree finish --merge`; a pull request merges
  only while `devkit workflow envelope check` reports neither.
- Every `spec` and `proposal` activity runs on `plan-<slug>` or `dev-<slug>`, in a worktree or, in `direct` mode
  without one, on a branch started with `--no-worktree`. A branch that exists is continued only with
  `--existing-branch <branch> --unit <dir>`; devkit-spec's `devkit.attach_check` extension refuses a unit that is not
  the branch's (`plan-<slug>`: `PROP-<slug>` bound to `sdd-proposal`; `dev-<slug>`: the spec bundle bound to an
  `sdd-spec-*` workflow, or the accepted proposal before its handoff). The handoff runs only on `dev-<slug>`.

---

## 5. Consequences

- `ADR-worker-delivers-committed-result` stays: a failed range check is a `failed` worker envelope; it is cleared by a
  resolution that names it, not by a later check.
- `devkit spec proposal handoff` refuses any checkout on another branch than `dev-<slug>`
  (`SPEC_PROPOSAL_WRONG_WORKTREE`); `ADR-branch-guards-and-close-discard` extends the guard to the base checkout.
- `/spec-next` reports `[PENDING_QUESTION]`, `[BLOCKED]` and stale activity branches; the feedback hygiene playbook
  lists stale branches for the user to resume or discard.
- A stale branch's unit is shown only when an attach recorded it; the Host maps the slug otherwise.
