---
id: SPEC-handoff-unit-records
title: Proposal handoff and the workflow records of the proposal unit
summary: Proposal handoff drops the proposal unit's devkit decision records and envelopes instead of moving them to docs/materials, and records the spec's G1 and G2 from the user's recorded acceptance of the proposal's direction.
status: in-progress
created: 2026-10-15
related_capabilities:
  - CAP-DLV-proposal-incubation
  - CAP-DLV-delivery-workflows
related_stories: []
workflow: direct-delivery
workflow_hash: sha256:6fe2644b9464ea860e6d6928748778b4ffd7a255e92ddea5fe10eba59138f287
---

# [SPEC-handoff-unit-records] Proposal handoff and the workflow records of the proposal unit

## 1. Problem Statement & Motivation

A proposal bundle is a devkit workflow unit: `devkit workflow answer` writes its G1 and G2 answers to
`decisions/<NN>-<request>.yaml`, beside the proposal's PADRs, and a delegated spike writes envelopes to `envelopes/`.
`devkit spec proposal handoff` treats them as non-PADR extras and moves them to
`docs/materials/<YYYY-MM>/<YYYYMMDD>-<slug>/`, where workflow state nobody reads piles up in the durable research
area. The new spec then starts with G1 and G2 open although the user already accepted the proposal's direction, so
the agent either asks again or records them from the proposal's answers, a practice no rule states
(`FB-handoff-moves-gate-decisions-to-materials`).

Handed off from the handoff-unit-records proposal; its spike findings are kept in section 5.

## 2. User Stories

- As a developer, I want a handoff to leave no workflow records of the proposal in `docs/materials/`, so the
  materials area holds research only and Git history keeps the proposal's records.
- As the agent, I want the handoff to record the spec's gates from the user's recorded acceptance of the proposal's
  direction, so I neither ask the user twice nor record approvals by an unwritten practice.

## 3. Non-Goals

1. **Scope Excluded**: replacing `--direction-chosen` with a check of the proposal's direction record.
2. **Scope Excluded**: any devkit change, including moving devkit's unit records out of `decisions/`.
3. **Scope Excluded**: carrying gates answered by policy (`auto`) or a Route 4 team acceptance without a decision
   record; those specs open their gates as before.

## 4. Acceptance Criteria & Behavioral Contracts

### [AC-01] Proposal unit records are dropped

- **Given** a proposal bundle whose `decisions/` holds devkit decision records (including a malformed `NN-*.yaml`)
  and PADRs, and whose `envelopes/` holds envelopes
- **When** `devkit spec proposal handoff` runs
- **Then** no decision record or envelope is written under `docs/materials/` or the spec bundle; the PADRs are
  promoted and other extras (a `decisions/notes.yaml`, `notes.md`) are carried as before; the result lists the
  dropped workspace-relative paths in `dropped_records` (text: one `[DROPPED_RECORD: <path>]` each); a proposal whose
  only extras were such records creates no materials directory.

### [AC-02] The spec's gates are recorded from the user's direction answer

- **Given** a proposal whose effective `gate:direction` record (of its bound workflow, not cancelled, with no later
  return record) is `accept` with `by: user`, handed off to `direct-delivery`
- **When** the handoff runs
- **Then** the spec has `decisions/01-gate-intent.yaml` and `decisions/02-gate-direction.yaml`, each `accept` with
  `by: user` and note `PROP-<slug>`, written through devkit's `record_answer` against the spec's open requests;
  the result lists them in `carried_gates` (`request`, `decision` path; text: `[CARRIED_GATE: <request>
  decision=<path>]`); `devkit workflow next` on the spec reports both gates done.

### [AC-03] Nothing is recorded without the user's answer

- **Given** a proposal with no direction record, a direction record by `policy`, a declined or cancelled one, one
  followed by a return record, an `accepted` proposal without records, or a spec left unbound
- **When** the handoff runs
- **Then** no decision record is written in the spec and `carried_gates` is empty. For a spec bound to `bugfix`, only
  `gate:intent` is recorded, since its direction gate opens after `characterize`.

### [AC-04] A recording failure never fails the handoff

- **Given** an answer that devkit refuses or that cannot be written
- **When** the handoff records the spec's gates
- **Then** the handoff stays done, the gates recorded before the failure stay, and a `SPEC_PROPOSAL_GATE_NOT_CARRIED`
  warning names the spec and, in `[FIX]`, the `devkit workflow answer` command to record the gate.

### [AC-05] Living Spec, workflows and guidance

- **Given** the change
- **When** an agent reads `CAP-DLV-proposal-incubation`, the gate rules of `incubated-delivery`, `direct-delivery`
  and `bugfix`, and the `spec` and `spec-next` references on handoff
- **Then** they state that the handoff drops the proposal's unit records and records the spec's gates from the
  user's direction answer, and that otherwise the spec's gates are asked as before; `just ci` passes.

## 5. Spike Findings

- devkit's public loaders identify the unit records exactly: `load_decisions(unit)` returns each decision record and
  each malformed `NN-*.yaml` with its unit-relative `file`, `load_envelopes(unit)` each envelope and malformed
  envelope. A PADR or another file under `decisions/` is not among them.
- Carrying the records into the spec does not work: devkit counts only the decision records of the bound workflow's
  current segment, and an envelope without a workflow scope counts in every workflow, so a spike's envelope could
  satisfy a check of the spec.
- In `SPEC-orchestration-mode` the spec's G1 and G2 were recorded `--by user` right after the handoff from the
  proposal's answers; specrig never asked again either. The user's acceptance of the proposal's direction covers the
  spec's goal, scope and verification. Carrying an existing explicit answer is not inference; deriving one from
  `status: accepted` would be.
- Moving devkit's `decisions/` is not needed: it would touch every unit and existing record for one consumer's naming
  collision.
