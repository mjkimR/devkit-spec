---
id: SPEC-planning-effort-safeguards
title: Planning effort safeguards
summary: 'Makes the choice of Planning effort visible and hard to skip: the Host proposes Planning effort with a proposal''s plan-intent, proposal Planning at medium always runs one challenger, and the plan-accept request shows the applied effort and the support roles that ran.'
status: completed
created: 2026-10-16
related_capabilities:
  - CAP-DLV-delivery-workflows
  - CAP-HARN-agent-guidance
related_stories:
  - US-incubate-and-hand-off-a-proposal
workflow: sdd-spec-feature
workflow_hash: sha256:200b62037a75f0224fc4deeffe8b5d6a0f6bcc5ded729a0606e1d24b4ac34d38
---

# [SPEC-planning-effort-safeguards] Planning effort safeguards

## 1. Problem Statement & Motivation

The first Planning run under the reworked workflow (`PROP-backlog-roadmap-and-issues`, 2026-10-16, `direct` mode)
started at the default `medium` effort without the Host proposing a value, skipped the `challenger` as "not needed",
and reversed a strategy-layer decision on the strength of the author's own comparison. The user caught it only
because the Host's report happened to say "challenger not run". A retroactive `high` run then found 6 major issues.

Three gaps let that happen:

- **No stop at the choice.** `activity-effort` is "chosen when the activity starts" (the `spec` skill's
  `references/effort.md`), but the `direct` path has no point that asks for it; a `planning-worker` receives effort
  in its payload, the Host does not. The guidance also steers toward silence: "Propose a value other than `medium`
  only when the activity needs it".
- **Self-judged criticism.** At `medium`, proposal Planning runs `scout` and `challenger` "when needed", decided by the
  author of the work under criticism.
- **Invisible at the decision.** The `plan-accept` request shows the change summary and the decisions, not the effort
  applied or which support roles ran.

The fix follows the strategy layer, which is the source of truth for the effort table (workbench
`docs/strategy-layer/01-master-flow.md` §2.3), so 01 changes first.

## 2. User Stories

- **US-1**: As a user deciding `plan-intent` for a proposal, I want the Host to propose the Planning effort with a
  reason, so that I choose it deliberately instead of inheriting a silent default.
- **US-2**: As a user, I want every proposal Planning at `medium` or above to be criticized from a context other than
  the author's, so that the direction I accept has been attacked at least once.
- **US-3**: As a user deciding `plan-accept`, I want to see the effort applied and the support roles that ran, so that
  a skipped review is visible where I decide.

## 3. Non-Goals

1. **Scope Excluded**: changes to devkit (`devkit workflow next` printing effort or support roles at a gate).
   - **Rationale**: devkit is SDD-agnostic; the data already exists in envelopes and `devkit workflow envelope check`.
   - **When to Reconsider**: when the Host's presentation proves unreliable in practice; recorded as a follow-up in
     01 §10.
2. **Scope Excluded**: autohub's `plan-accept` screen. Recorded as a follow-up in 01 §10's autohub table.
3. **Scope Excluded**: storing `activity-effort` in the Unit or the configuration; it stays run input.
4. **Scope Excluded**: a mechanical check that blocks `plan-accept` without a `challenger` envelope.
   - **Rationale**: with `challenger` required from `medium` up, a block would matter only for a deliberate `low`;
     visibility at the decision (US-3) covers the rest at lower cost.
   - **When to Reconsider**: a `plan-accept` is given at `medium` or `high` without a `challenger` envelope.
5. **Scope Excluded**: effort proposals for other activities beyond restating the existing rule; Development effort
   is already confirmed when the activity starts.

## 4. Acceptance Criteria & Behavioral Contracts

The checks below read the changed files; "states" means the quoted rule is present in the named file and no
contradicting older wording remains in it.

### [AC-01] Strategy layer first
- **Given** workbench `docs/strategy-layer/01-master-flow.md`
- **When** this spec is integrated
- **Then** §2.3's Planning (`proposal`) row states `challenger` once at `medium` (plus `scout` when the direction needs
  evidence), §2.3 replaces "agent는 필요할 때만 다른 값을 제안한다" with a rule that the effort is always proposed at
  the activity start, §3's `plan-intent` row or §5 states that a proposal's `plan-intent` request includes the
  proposed Planning effort, §6.2 states that the `plan-accept` request shows the applied effort and the support roles
  that ran, §9 lists the decisions, and §10 lists the devkit-spec changes as `완료` and the devkit and autohub
  follow-ups

### [AC-02] Challenger always at medium
- **Given** the bundle files `skills/spec/references/effort.md`, `workflows/sdd-proposal.md`,
  `subagents/planning-worker.md` and `skills/spec-delegate/SKILL.md`
- **When** each is read
- **Then** each states that proposal Planning at `medium` runs one `challenger` pass (and `scout` when the direction
  needs evidence), at `high` two or more options compared, a `challenger` and a re-review after changes, at `low`
  questions only; `rg -n "challenger.{0,40}when needed|when needed.{0,40}challenger"` over `src/devkit_spec/bundle/`
  returns no line

### [AC-03] Effort proposed with plan-intent
- **Given** the `spec` skill (`SKILL.md` Tier 1, `references/classification.md` §1, `references/effort.md`)
- **When** each is read
- **Then** the classification reference states that the Host's `plan-intent` request for a proposal includes the
  proposed Planning `activity-effort` with its reason, the effort reference states criteria for proposing `high`
  (reverses an upstream or accepted decision, creates a contract or document kind, affects more than one package)
  and that the effort is always stated when the activity starts, and the sentence "Propose a value other than
  `medium` only when the activity needs it" no longer appears

### [AC-04] Effort and roles shown at plan-accept
- **Given** `workflows/sdd-proposal.md` §Gate rules and the `planning-worker` contract's Return
- **When** each is read
- **Then** the `plan-accept` bullet states that the acceptance request shows, besides the change summary and the
  decisions, the `activity-effort` of each Planning run (from its `worker` envelope) and the support-role envelopes
  present (`challenger`, `scout`, or "none"), and names a gap when a run's effort required a `challenger` that has no
  envelope

### [AC-05] Bound proposals rebound
- **Given** the proposals on the base bound to `sdd-proposal` before this change
- **When** `devkit workflow next --unit docs/proposals/PROP-<slug>` runs for each after the change
- **Then** none reports `WORKFLOW_DRIFT`

### [AC-06] Living Spec and checks
- **Given** the integrated change
- **When** `just ci` runs and `CAP-DLV-delivery-workflows` is read
- **Then** `just ci` exits 0, and `CAP-DLV-delivery-workflows` states the Planning effort rule (challenger from
  `medium`, effort and support roles shown at `plan-accept`)

## 5. Assumptions

- The workflow hash of `sdd-proposal` changes with its body; rebinding the existing proposals
  (`devkit workflow bind`) is part of this change, as an earlier commit did after a workflow edit.
- The strategy-layer edits are written in the workbench checkout and committed by the user, as for the previous
  strategy-layer change.
- "Affects more than one package" in the `high` criteria means devkit, devkit-spec or autohub, or several packages of a
  monorepo.
