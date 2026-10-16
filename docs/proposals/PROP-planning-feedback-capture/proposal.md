---
id: PROP-planning-feedback-capture
title: Feedback capture in Planning
summary: "Keeps Planning feedback in its proposal bundle, carries open observations into the spec at handoff, and preserves them before proposal cleanup. Adds run-level capture and a Planning feedback sweep using the existing policy."
status: accepted
created_at: 2026-10-16
target_area: capabilities/harness/
priority: medium                      # critical | high | medium | low
size: M                               # S | M | L | XL
boundaries:
  owns:
    - capabilities/harness/
    - capabilities/delivery/
    - capabilities/documents/
    - capabilities/governance/
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

Proposal-local feedback, capture at the end of every Planning run, and a sweep before Planning returns to the user
keep observations available for both acceptance and rejection. Handoff carries open feedback into Development; cleanup
preserves open feedback when no handoff happens.

## 2. Design Questions and Alternatives

### 2.1 Location and ownership (Q1, Q2)

| Option | Planning writes | Handoff | Rejection or decomposition | Assessment |
| --- | --- | --- | --- | --- |
| Global backlog | `specs/<YYYY-MM>/feedback/<YYYYMMDD>-<name>.md` | No relocation | Already outside the proposal | Simple retirement, but widens every Planning executor's write boundary |
| Proposal-local feedback (recommended) | `docs/proposals/PROP-<slug>/feedback/<name>.md` | Open files go to the spec's `feedback/`; settled files remain preserved materials | Keep files with the proposal until cleanup; move open files to the global backlog before deletion | Keeps one activity's work together and its worker boundary unchanged; requires explicit relocation and path-rule support |

`PADR-planning-feedback-in-proposal` records the recommended location and its retirement rules. Here **unresolved**
means exactly `status: open`; `promoted`, `dismissed` and `forwarded` are settled. Moving a file never changes its
status, ID or observation date. Capture and handoff do not perform feedback hygiene.

### 2.2 Capture and terminal sweep (Q3, Q4)

| Option | Benefit | Failure or cost |
| --- | --- | --- |
| Capture every run; sweep only at plan-accept and after a rejection | Closest to the draft's timing | A fresh rejection sweep needs an agent after the decision, conflicting with the no-worker/no-Cloud-Agent rejection procedure |
| Capture and sweep before every Planning return to the user (recommended) | Both question rounds and the final acceptance request already have a sweep before either acceptance or rejection | More sweeps; each covers its current run and the committed accumulated records, deduplicating prior observations |
| Run capture only, no proposal sweep | Smallest procedural change | No completion evidence or deliberate check for missed observations |

The recommended option puts the sweep before the executor ends a run, including runs waiting for answers. A rejection
uses the latest committed sweep; it starts no new worker and does not claim to inspect a later conversation. A run
stopped by an unsolved problem records its coverage gap instead of claiming a successful sweep. This timing replaces
the draft's fresh rejection-time sweep and is a direction choice for `plan-accept`.

### 2.3 Pilot procedure fixes (Q5)

The answer path for decisions without a prior worker question and the missing commit instruction after `plan-intent`
remain deferred observations for Backlog/hygiene, not fixes in this feature. Development records or links their
feedback destinations before completion; this Planning does not claim that those records already exist. Effort proposal and Challenger display
are already handled by the current effort reference and proposal workflow; this change preserves those requirements.

## 3. Proposed Design & Impact

### 3.1 Capture and discoverability

- Planning executors write observations in their own proposal's `feedback/`, on `plan-<slug>`. File names and IDs use
  the existing undated feedback convention: `<name>.md`, `FB-<name>`. Choose names unused in the repository, and keep
  existing all-namespace deduplication. No global write permission is added to the Planning worker.
- The `spec-feedback` skill permits this location alongside the existing spec-local and month-level destinations.
  It removes the blanket prohibition on `docs/` only for this exact proposal feedback location.
- At `capture=observed`, direct Hosts, Planning workers and Development workers record concrete observations before
  their last work commit, including a run ending with questions or a problem. Development keeps its spec-local
  destination. At `requested-only`, autonomous capture records nothing; explicit requests retain their override.
- The document index already discovers ID-bearing Markdown under `docs/`, and namespace resolution already follows
  the proposal anchor. Extend path validation and applicable rule guides/tests so feedback files receive feedback
  validation, not proposal/PADR validation. `list feedback`, `resolve`, `refs` and all-namespace deduplication must work
  before and after handoff, including for feedback in rejected proposals awaiting cleanup.

### 3.2 Handoff and other endings

- Before writing, handoff classifies direct Markdown feedback files by their existing status. It plans open files
  into `<new-spec>/feedback/<name>.md` and settled files into the existing preserved-materials destination under
  `feedback/`. Empty or absent feedback directories keep existing behavior.
- Feedback moves participate in the existing destination, collision, symlink and rollback checks, and in the relocation
  map used for link rewriting. No open feedback file may be carried twice or silently become historical materials.
  An unreadable file, malformed feedback frontmatter, unknown/missing status or unsafe feedback source is refused
  before writing, with the existing structured invalid/target error contract. Nothing is overwritten.
- Every open observation is retained, even if its target is this proposal. IDs remain unchanged; existing handoff
  rewriting handles references from the proposal to the new spec. A failed relocation restores the proposal and its
  feedback with the same atomicity/rollback guarantees as materials.
- **Rejected**: retain feedback in the rejected proposal, so rejection remains the existing state-and-answer commit.
  The later Host hygiene pass moves open files into the month-level backlog before deleting the proposal. Settled
  records remain in Git history; the rejection ADR keeps the proposal/rejection reference.
- **Returned for decomposition**: retain feedback while the original draft exists. Before Backlog deletes the original
  during a split, move its open feedback to the month-level backlog in the same commit. Do not copy it into every child.
- Cleanup uses its current month/date for destination naming and preserves the observation's `created_at`. Check
  destinations and IDs before moving; on a collision or invalid file leave the source proposal intact and report it.
  A failed preservation never authorizes deletion. This applies to any proposal deletion with feedback, including a
  draft abandoned before a handoff; the current draft branch guard still applies.
- Before deletion without handoff, inspect references from retained feedback and other current documents to the
  retiring proposal, PADRs and settled sibling feedback. Historical context/evidence mentions use the existing
  strikethrough convention and retain a source Git revision/path so the context remains retrievable. Relative links
  in moved feedback are updated for their new location. A live dependency or target is not silently changed into a
  historical mention: if it cannot remain valid, keep the proposal and report the unresolved dependency. Validate
  document references after the planned move/deletion in the same cleanup commit. Never leave an open feedback file
  with a dangling canonical ID or broken context link.

### 3.3 Workflow and sweep evidence

- Add `collect-feedback` between `spike` and `direction-handoff` in `sdd-proposal`. Its exit is
  `envelope-check-pass(feedback swept)`; its role, isolation, skills and artifacts match the Development stage exactly
  (`feedback/*.md`, `envelopes/feedback-NN.yaml`), satisfying devkit's shared-stage validation. Its entry can use
  `anchor-exists`: shared-stage comparison does not compare entry conditions.
- The Planning procedure runs the sweep before every return to the user, even when questions hold `plan-accept`.
  Each run writes a new `feedback` envelope at `collect-feedback`, then its single `worker` envelope. A passing older
  sweep does not cover a later run: the procedure checks that run's evidence before returning; no new devkit freshness
  check or timestamp protocol is introduced. The final sweep is complete before requesting `plan-accept`.
- With `collect-feedback=off`, skip the autonomous sweep and write no sweep envelope; observed run-level capture
  still applies. With the stage enabled and `capture=requested-only`, write the existing passing policy-skip evidence
  and record no autonomous observations. Zero observations also passes. Explicit user sweeps still write no envelope.
- Store sweep and worker envelopes in the proposal's `envelopes/`. Handoff drops them as it already drops workflow
  records, while carrying open feedback files. Development performs its own sweep; Planning evidence does not satisfy it.
- A rejection before any Planning run has no run observations to sweep. No new rejection execution is introduced in
  `direct`, `local-orchestrated` or `cloud-pr`. Partial/failed runs expose their gap; rejection never fabricates PASS.

### 3.4 Verification scenarios for the Development spec

| Scenario | Given / When / Then |
| --- | --- |
| V1 Location | Given a reviewing proposal, when Planning records feedback, then it stays in that proposal's boundary and is found by `list feedback`, `resolve` and `refs`; rules validate the path, ID and H1. |
| V2 Handoff | Given open and settled proposal feedback, when handoff succeeds, then only open files enter the spec's `feedback/`, settled files go to materials, and IDs/statuses/dates stay unchanged. |
| V3 Failure safety | Given a collision, invalid status/frontmatter or unsafe link, handoff refuses without changing sources; inject a failure after a feedback move and verify full rollback. |
| V4 Other endings | Given a rejection or return to Backlog, feedback remains discoverable; before rejection/decomposition/abandonment cleanup deletes it, open feedback moves once to the global backlog, historical references and relative links remain retrievable, and document-reference validation passes; otherwise deletion stops. |
| V5 Capture | Given any run ending in completion, questions or a problem, observed capture is performed before its last commit; requested-only creates no autonomous observation. Review both worker contracts and the direct path. |
| V6 Policy | Given a proposal without a sweep, next names collect-feedback; zero observations and requested-only skip evidence pass; a failed sweep stays open; stage-off bypasses it with no envelope. Validate all shared stages. |
| V7 Rounds and rejection | Given another question round, a new sweep covers that run before its worker return. A later rejection starts no worker/Cloud Agent and uses that recorded coverage without claiming a fresh sweep. |
| V8 Regression | Given a proposal without feedback, existing handoff and carried-gate behavior is unchanged; Planning records are dropped, and Development requires its own sweep. |

### 3.5 Non-Goals

- **Scope Excluded**: changing feedback statuses, template content, or promotion/dismissal/forwarding decisions.
- **Scope Excluded**: feedback stages for Backlog or inline Planning; they have no runs or stages of their own.
- **Scope Excluded**: autohub UI, rejection orchestration changes, or a new devkit workflow/envelope API.
- **Scope Excluded**: implementing the two pilot procedure fixes of §2.3.

## 4. Lifecycle & Retirement Criteria

- **Before handoff**: after `plan-accept`, update the strategy layer's 01 §6.2 first: proposal-local feedback, every-run
  capture and pre-return sweep, open-feedback transfer on handoff and preservation before rejected/decomposed proposal
  deletion. Preserve the existing no-agent rejection procedure; document policy-off, requested-only and failure gaps.
- **Planning outputs**: this proposal, `PADR-planning-feedback-in-proposal`, the target-docs blueprint, source evidence
  and the Challenger result. The proposed decisions are not accepted until `plan-accept`.
- **Boundary extension**: document-model and governance contracts are affected because proposal-local feedback adds a
  supported path. This is required for the chosen location; ownership includes those areas as well as harness/delivery.
  No existing ADR is edited. The PADR is promoted by the normal handoff into a new ADR.
- **On acceptance**: record `gate:plan-accept` with `status: accepted`, commit and merge the Planning branch. Verify the
  strategy precondition, then start Development with `devkit spec proposal handoff planning-feedback-capture` on
  `dev-planning-feedback-capture`.
- **On rejection**: follow the current rejection procedure; implementation has not started. This proposal cannot rely
  on its proposed new feedback mechanics before they ship.
