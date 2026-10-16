---
id: SPEC-proposal-effort-hints
title: Separate Planning and Development effort hints on proposals
summary: Adds separate Planning and Development effort hint fields to proposal frontmatter so Backlog and Planning preserve recommended activity-effort values that Host sessions and autohub submission screens pre-fill and let the user override.
status: in-progress
created: 2026-10-16
related_capabilities:
  - CAP-DLV-proposal-incubation
  - CAP-DLV-delivery-workflows
  - CAP-DOCS-document-lookup
  - CAP-GOV-spec-rules
  - CAP-HARN-agent-guidance
related_stories:
  - US-incubate-and-hand-off-a-proposal
  - US-route-development-intent
workflow: sdd-spec-feature
workflow_hash: sha256:20b913108a194572244fd42f0587ce3fe7fecfb7610c8afb52fa6b35e79fb0e0
---

# [SPEC-proposal-effort-hints] Separate Planning and Development effort hints on proposals

## 1. Problem Statement & Motivation

Handed off from proposal PROP-proposal-effort-hints on 2026-10-16.

- **Parent design**: the strategy layer's master flow (workbench `docs/strategy-layer/01-master-flow.md` §2, §2.3, §3,
  §6.2, §7.1, §9 `Q63`, §10), architecture (`02-architecture.md` §3), and policy (`03-policy.md` §2 and §8).
- **Problem**:
  1. `activity-effort` (`low` | `medium` | `high`) is chosen when each activity starts and recorded authoritatively
     only in the run's `worker` envelope (`activity_effort`). However, the best moment to judge a proposal's Planning
     effort is when Backlog frames `plan-intent`, and the best moment to judge its Development effort is at the end of
     Planning (`direction-handoff`). Without separate hint fields on `proposal.md`, a later session or executor must
     re-derive the recommendation from scratch.
  2. Planning effort and Development effort frequently differ (an open design question with a small code change needs
     `high` Planning and `low`/`medium` Development; a clear design touching multiple packages needs `low`/`medium`
     Planning and `high` Development).
  3. Because `devkit spec proposal handoff` deletes `proposal.md` when creating the spec bundle on `dev-<slug>`, local
     Hosts running `handoff` before starting the Development turn lose `dev_effort` unless `HandoffResult` returns it.
     Meanwhile `spec.md` must never store `planning_effort` or `dev_effort`.

## 2. User Stories

- **US-incubate-and-hand-off-a-proposal**: As a developer or agent incubating a proposal across Backlog, Planning and
  Development, I want `proposal.md` to carry separate `planning_effort` and `dev_effort` hints (`low` | `medium` |
  `high`, default `medium`) that are validated by `RULE-spec-format` and `handoff`, exposed by `devkit spec list
  proposal`, and returned as `dev_effort` on `handoff` without copying them to `spec.md`.
- **US-route-development-intent**: As a Host or operator starting Planning or Development of a proposal (locally or in
  `autohub`), I want the proposal's `planning_effort` or `dev_effort` hint to pre-fill the initial `activity-effort`
  recommendation while allowing the user to confirm or override it at submission time.

## 3. Non-Goals

1. **Scope Excluded**: Storing `planning_effort` or `dev_effort` on `spec.md`, or treating proposal hint fields as
   authoritative execution evidence (`worker` envelopes remain the sole record of applied `activity_effort`).
2. **Scope Excluded**: Adding hint fields for work mode (`direct` | `local-orchestrated` | `cloud-pr`) or model settings
   (`model-effort`).
3. **Scope Excluded**: Blocking `plan-accept` or `handoff` when a user overrides the hint with a different effort at run
   start, or requiring retroactive commits to `proposal.md` when overridden.

## 4. Acceptance Criteria & Behavioral Contracts

### [AC-01] Proposal scaffolding with `--planning-effort` and `--dev-effort`
- **Given** a workspace where `devkit spec proposal new <slug>` is invoked
- **When** `--planning-effort` and `--dev-effort` are omitted or passed as `low`, `medium` or `high`
- **Then** `proposal.md` is scaffolded with `planning_effort: <value>` and `dev_effort: <value>` (each defaulting to
  `medium`), `CreatedProposal.to_dict()` and `[PROPOSAL: ...]` include `planning_effort` and `dev_effort`, and passing
  any value outside `low` | `medium` | `high` fails with `ARGUMENT_INVALID` naming `--planning-effort` or
  `--dev-effort`.

### [AC-02] `RULE-spec-format` validation of proposal effort hints
- **Given** a proposal anchor (`docs/proposals/PROP-<slug>/proposal.md` or `docs/proposals/PROP-<slug>.md`)
- **When** `devkit rules check` runs `RULE-spec-format`
- **Then** a proposal without `planning_effort` or `dev_effort` passes (legacy compatibility), a proposal with
  `planning_effort` or `dev_effort` set to `low`, `medium` or `high` passes, and a proposal whose `planning_effort` or
  `dev_effort` is not a string in `low` | `medium` | `high` reports a non-fixable `RULE-spec-format` `ERROR` on that
  field's line naming the allowed values.

### [AC-03] Proposal handoff validates effort hints, returns `dev_effort`, and omits both from `spec.md`
- **Given** an accepted proposal on `dev-<slug>`
- **When** `devkit spec proposal handoff <slug>` runs
- **Then** preflight validates `planning_effort` and `dev_effort` if present (raising `SPEC_PROPOSAL_INVALID` before
  writing anything if either is not `low` | `medium` | `high`), `HandoffResult.to_dict()` includes `"dev_effort"` (the
  string or `None` when omitted on a legacy proposal), `[HANDOFF: ...]` includes `dev_effort=<value>` when present, and
  the resulting `spec.md` frontmatter contains neither `planning_effort` nor `dev_effort`.

### [AC-04] `devkit spec list` exposes proposal fields (`task_kind`, `planning_effort`, `dev_effort`)
- **Given** proposals in the workspace (with or without `task_kind`, `planning_effort`, `dev_effort` in frontmatter)
- **When** `devkit spec list proposal` (or `devkit spec list`) runs in text or JSON format
- **Then** each proposal item includes `task_kind`, `planning_effort` and `dev_effort` (value or `None`/`-` when absent
  on legacy proposals) in JSON `documents[]` and on `[DOCUMENT: ...]` sentinel lines, and `--where
  planning_effort=<val>` / `--where dev_effort=<val>` filters proposals accordingly.

### [AC-05] Bundle workflow, subagent and skill guidance for proposal effort hints
- **Given** the `devkit-spec` bundle (`sdd-proposal.md`, `planning-worker.md`, `spec/SKILL.md`,
  `spec/references/classification.md`, `spec/references/effort.md`, `spec-orchestrate/SKILL.md`)
- **When** synchronized and inspected
- **Then** Backlog guidance instructs setting `--planning-effort` and `--dev-effort` and proposing `planning_effort`
  (and provisional `dev_effort`) at `plan-intent`; `sdd-proposal` and `planning-worker` instruct reviewing and updating
  `dev_effort` in `proposal.md` before `plan-accept` and showing recommended `dev_effort` (plus any difference between
  `planning_effort` and applied `activity_effort`) in the `plan-accept` request; Development start guidance instructs
  reading `dev_effort` from `proposal.md` or `HandoffResult.dev_effort` as the initial recommendation; and all bound
  units and `.devkit/managed/` assets are synchronized.
