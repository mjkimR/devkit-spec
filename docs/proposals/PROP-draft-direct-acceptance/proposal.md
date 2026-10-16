---
id: PROP-draft-direct-acceptance
title: Direct acceptance of drafts that need no Planning
summary: Lets the user accept a draft proposal whose direction is already settled directly in Backlog, recording plan-intent and plan-accept together without a Planning branch, so small drafts such as decomposition results go straight to handoff.
status: draft                         # draft | reviewing | accepted | rejected
created_at: 2026-10-16
target_area: capabilities/delivery/
priority: medium                      # critical | high | medium | low
size: S                               # S | M | L | XL
boundaries:
  owns:
    - capabilities/delivery/
    - capabilities/harness/
  excludes:
    - docs/decisions/
task_kind: feature                    # feature | bugfix: the spec follows sdd-spec-<task_kind>
workflow: sdd-proposal
workflow_hash: sha256:90918c632715461d07f99f683b8381bdbe6381ad6689a7575a72c002c18c1399
---

# [PROP-draft-direct-acceptance] Direct acceptance of drafts that need no Planning

- **Parent design**: the strategy layer's master flow (workbench `docs/strategy-layer/01-master-flow.md`, §5.1 Backlog
  edits drafts only, §5.2 decomposition, §6.2 proposal Planning) and policy (`03-policy.md` §4: Planning acceptance
  commits go through the Planning branch's PR under `required`).
- **Origin**: `PROP-backlog-roadmap-and-issues` makes every request not yet started a draft proposal and has a
  decomposition yield drafts only; until this path exists, small drafts run Planning at `low` effort.
- **Related**: `ADR-task-kind-and-planning-depth` (depth is lowered only by a proposal's handoff),
  `CAP-DLV-proposal-incubation`, `CAP-DLV-delivery-workflows`.

## 1. Background & Hypothesis

### 1.1 Problem

- **Small drafts pay for a Planning they do not need.** Once every request not yet started is a draft, many drafts
  carry a settled direction: a piece split off a larger request, a follow-up promoted from feedback, a request whose
  contract is clear. Planning at `low` still starts `plan-<slug>`, commits `status: reviewing`, records `plan-accept`
  and merges the branch, then Development starts `dev-<slug>`: two branches, and two PRs under
  `pull_request = required`, for one decision the user could make on sight.
- **Effort cannot express it.** `activity-effort` sets how thoroughly an activity is done; skipping the activity is a
  routing decision, not a lower thoroughness, so an effort value such as `skip` would blur the axis.
- **Backlog may not accept today.** Backlog changes only a `draft` (01 §5.1, `devkit spec proposal check`); setting
  `status: accepted` and recording `plan-accept` belong to Planning.
- The workflow itself does not need Planning to run: `sdd-proposal`'s `spike` stage is optional and
  `direction-handoff` exits on `status: accepted` with the recorded `gate:plan-accept`, wherever they are committed.

### 1.2 Hypothesis

A Backlog path that lets the user give `plan-intent` and `plan-accept` together for an eligible draft, committed to
the base like other Backlog work, removes the Planning branch for drafts that need no Planning while keeping both
human decisions explicit and recorded, and keeps the proposal body, gates and provenance carried by the handoff.

## 2. Technical Spike Questions

- **Q1. Eligibility.** Which drafts may be accepted directly? Candidates: no open spike questions in the body, no
  `needs_decompose`, no `plan-<slug>` branch, `task_kind` settled, and the Host's classification that the direction
  needs no comparison. Is a size limit (for example `S` and `M`) useful, or is the user's decision enough?
- **Q2. Gates.** Are `plan-intent` and `plan-accept` two `devkit workflow answer` records made from one user decision,
  or does the user confirm each? Both are always the user's (`source=fixed`); the path must never infer either.
- **Q3. Policy.** Under `pull_request = required`, Planning's acceptance commit goes through the Planning PR
  (03 §4). Is a direct acceptance a Backlog commit (outside the policies, 03 §1), or does it still need a PR? The
  first is the point of the path; the second keeps a review trail for teams.
- **Q4. Compared with reclassification.** Instead of accepting, Backlog could delete the draft and start a `spec`
  Unit (or a `session` task) at pickup. That loses the carried body, gate records, `issue`, `milestone` and
  `decomposed_from` that a handoff keeps. Is reclassification still allowed for `session`-depth drafts, where a spec
  Unit would be heavier than the work?
- **Q5. Tooling.** Is the path a skill procedure over existing commands (`devkit workflow answer` twice, a status
  edit), or a command (working name `devkit spec proposal accept <slug> --direct`) that checks eligibility, records
  both gates and sets the status in one validated step? Does `devkit spec proposal check` need a mode for it?
- **Q6. Visibility before acceptance.** If `PROP-backlog-roadmap-and-issues`'s follow-up shows the applied effort and
  support roles before `plan-accept`, a direct acceptance shows "Planning skipped" in the same place.

## 3. Proposed Design & Impact

A working direction for Planning to test:

- **Path**: in Backlog, the Host proposes direct acceptance for an eligible draft (Q1) with its classification; on the
  user's explicit decision it records `gate:plan-intent` and `gate:plan-accept` (`--by user`), sets
  `status: accepted` and commits to the base as Backlog work (Q3). Development then starts `dev-<slug>` and runs
  `devkit spec proposal handoff` as for any accepted proposal.
- **Record**: the `plan-accept` note states that Planning was skipped and why the draft was eligible, as a decision,
  never the conversation.
- **Impact**: 01 §5.1 (Backlog may accept an eligible draft directly), §5.2 (small drafts from a decomposition),
  §6.2; 03 §1 and §4; `CAP-DLV-proposal-incubation` (the approval rule), `CAP-DLV-delivery-workflows` (whether
  `sdd-proposal` needs a change; likely none), the `spec` skill's classification reference.

### 3.1 Non-Goals

- **Scope Excluded**: a `skip` value for `activity-effort`.
- **Scope Excluded**: accepting without the user. Policy delegation (`auto`) never applies to `plan-intent` or
  `plan-accept`.
- **Scope Excluded**: lowering depth any other way than a proposal's handoff.

## 4. Lifecycle & Retirement Criteria

- **Depends on**: `PROP-backlog-roadmap-and-issues` (drafts as the queue for every request); can be planned in
  parallel.
- **Order of change**: the strategy layer's 01 and 03 are updated first (workbench); this package then follows.
- On acceptance (`plan-accept`): record `gate:plan-accept`, set `status: accepted` and merge the Planning branch;
  Development starts with `devkit spec proposal handoff draft-direct-acceptance`.
- On rejection: change only `status: rejected`, with the user's reason in the commit message; a later hygiene pass
  writes the rejection ADR and deletes the proposal directory.
