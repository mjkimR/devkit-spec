---
id: PROP-planning-feedback-capture
title: Feedback capture in Planning
summary: 'Gives proposal Planning a place and a moment to record feedback: a global location outside the proposal bundle, capture at the end of each Planning run, and a sweep before plan-accept and before a rejection, so observations survive proposals that never reach Development.'
status: draft                         # draft | reviewing | accepted | rejected
created_at: 2026-10-16
target_area: capabilities/harness/
priority: medium                      # critical | high | medium | low
size: M                               # S | M | L | XL
boundaries:
  owns:
    - capabilities/harness/
    - capabilities/delivery/
  excludes:
    - docs/decisions/
task_kind: feature                    # feature | bugfix: the spec follows sdd-spec-<task_kind>
workflow: sdd-proposal
workflow_hash: sha256:90918c632715461d07f99f683b8381bdbe6381ad6689a7575a72c002c18c1399
---

# [PROP-planning-feedback-capture] Feedback capture in Planning

- **Parent design**: the strategy layer's master flow (workbench `docs/strategy-layer/01-master-flow.md`, §5.1 on
  follow-ups reported as feedback, §6.2 proposal Planning, §6.2 rejection).
- **Related**: `CAP-HARN-agent-guidance` (feedback capture policy), `CAP-DLV-delivery-workflows` (the
  `collect-feedback` stage), `PROP-backlog-roadmap-and-issues` (Backlog reviews feedback as intake).

## 1. Background & Hypothesis

### 1.1 Problem

Feedback capture is built around Development. Proposal Planning has no place to write feedback and no moment to sweep
for it.

- **No location.** The `spec-feedback` skill places feedback of `spec` and `proposal` depth work in "the spec bundle you
  are working in"; during Planning that bundle does not exist yet. A file inside the proposal bundle would be moved to
  `docs/materials/` with every other bundle file at handoff (`CAP-DLV-proposal-incubation`), and the Planning worker's
  write boundary is the proposal directory.
- **No moment.** Only the Development workflows (`sdd-spec-feature`, `sdd-spec-bugfix`) have a `collect-feedback`
  stage, before `dev-integration`. `sdd-proposal` has none.
- **Observations are lost.** Planning may span several runs (question rounds), each a one-shot worker in
  `local-orchestrated` mode or a Cloud Agent in `cloud-pr`. What a run noticed is gone when it ends, long before a
  Development sweep. A proposal that is rejected, superseded or returned to Backlog for decomposition never reaches
  Development at all.

### 1.2 Observed in the pilot

The first Planning run under the reworked workflow (`PROP-backlog-roadmap-and-issues`, 2026-10-16, `direct` mode)
produced observations that had nowhere to go:

- **Effort not proposed at the start of Planning.** `activity-effort` is "chosen when the activity starts"
  (`spec` skill, `references/effort.md`), but the Host started Planning at the default `medium` without proposing a
  value; the work reversed a strategy-layer decision and warranted `high`, where a `challenger` is required. The
  prompt to choose sits inside one sentence of the `spec` skill's Tier 1; nothing in the `direct` path stops on it,
  while a `planning-worker` receives effort in its payload.
- **No record for decisions made in conversation.** The user settled the direction while discussing options, before
  any `worker` envelope with questions existed. `devkit workflow envelope answer` requires `--answers-to` a worker
  envelope, so the decisions went into the proposal and its PADRs without an `answer` record.
- **Commit before starting Planning is implicit.** `plan-intent` is recorded on the base in Backlog, and
  `devkit worktree start plan-<slug>` branches from the base HEAD, so the record must be committed first. The
  classification reference says to record it, not to commit it.

### 1.3 Hypothesis

A global feedback location, capture at the end of every Planning run and a sweep at the two points where Planning ends
(`plan-accept`, rejection) keep Planning observations at the cost of one small file each, the same as Development.

## 2. Technical Spike Questions

- **Q1. Location.** Use the global `specs/<YYYY-MM>/feedback/<YYYYMMDD>-<name>.md` for every Planning observation, or
  a `feedback/` directory in the proposal bundle that handoff moves to the spec bundle instead of `docs/materials/`
  (and rejection hygiene moves to the global location)? The global location survives every ending without new
  handoff rules.
- **Q2. Write boundary.** Planning runs on `plan-<slug>`. Does its write boundary include `specs/<YYYY-MM>/feedback/`,
  or are feedback files committed to the base like Backlog work (outside the worktree and pull-request policies)?
  The first keeps one commit stream per run; the second makes them visible before the Planning branch merges.
- **Q3. Run-level capture.** Add to the Planning and Development worker contracts, and to the Host's `direct` path,
  a step to record observations before the run's last commit when `FEEDBACK_POLICY capture=observed`?
- **Q4. Stage.** Add a `collect-feedback` stage to `sdd-proposal`, before `plan-accept` and on the rejection path,
  sharing the `[workflow.stages] collect-feedback` switch? Its exit check must work without a spec bundle: where does
  the sweep envelope live (the proposal's `envelopes/`, dropped at handoff)?
- **Q5. The pilot observations.** The effort item of 1.2 is handled separately (proposing Planning effort with
  `plan-intent`, a `challenger` always at `medium` for proposal Planning, and the applied effort and support roles shown
  before `plan-accept`). Are the other two items (an answer path for decisions made in conversation, the commit step
  after `plan-intent`) fixed here, or recorded as feedback once the location exists and settled by a hygiene pass?
  They are Planning-procedure fixes, not feedback mechanics.

## 3. Proposed Design & Impact

A working direction for Planning to test:

- **Location**: global feedback location for all Planning observations (Q1), written on the Planning branch (Q2).
- **Run-level capture**: worker contracts and the `spec` skill's Planning procedure gain "record observations, then
  commit" at the end of each run, under `capture=observed`.
- **Stage**: `sdd-proposal` gains `collect-feedback` before `plan-accept`; the rejection procedure runs the same sweep
  before the rejection commit. `[workflow.stages] collect-feedback = "off"` switches both off.
- **Impact**: `CAP-HARN-agent-guidance` (feedback locations and capture points), `CAP-DLV-delivery-workflows`
  (`sdd-proposal` stages), the `spec-feedback` skill, the Planning and Development worker contracts, the `spec` skill's
  Planning and rejection procedures; the strategy layer's 01 §6.2 first.

### 3.1 Non-Goals

- **Scope Excluded**: changes to feedback hygiene, its statuses or the feedback template.
- **Scope Excluded**: feedback capture in Backlog or inline Planning; they have no runs or stages of their own.
- **Scope Excluded**: autohub's rendering of Planning feedback.

## 4. Lifecycle & Retirement Criteria

- **Order of change**: the strategy layer's 01 §6.2 is updated first (workbench); this package then follows.
- Preliminary decisions: a PADR for the location and write boundary (Q1, Q2).
- On acceptance (`plan-accept`): record `gate:plan-accept`, set `status: accepted` and merge the Planning branch;
  Development starts with `devkit spec proposal handoff planning-feedback-capture`.
- On rejection: change only `status: rejected`, with the user's reason in the commit message; a later hygiene pass
  writes the rejection ADR and deletes the proposal directory.
