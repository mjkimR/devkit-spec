---
id: US-incubate-and-hand-off-a-proposal
title: Incubate a Proposal and Hand It Off to a Spec
summary: An AI coding agent shapes an idea whose direction must be decided first in a proposal bundle, records preliminary decisions, and, once the user accepts the direction, hands it off to a bound spec bundle with decisions promoted, materials moved, approvals carried and references rewritten.
area: delivery
actor: AI coding agent
status: active
entrypoints:
  - src/devkit_spec/bundle/workflows/sdd-proposal.md
  - src/devkit_spec/proposals/feedback.py
  - src/devkit_spec/proposals/handoff.py
created_at: 2026-10-13
capabilities:
  - CAP-DLV-proposal-incubation
  - CAP-DLV-spec-bundles
  - CAP-DLV-delivery-workflows
---

# [US-incubate-and-hand-off-a-proposal] Incubate a Proposal and Hand It Off to a Spec

## 1. User Story Narrative

- **As a**: AI coding agent handling a request whose direction is not yet clear
- **I want to**: shape the idea in a proposal, gather evidence and preliminary decisions, and turn the approved
  proposal into a spec bundle without losing anything that pointed at it
- **So that**: the user decides the direction on evidence, and the delivery that follows starts from a consistent
  Living Spec instead of dangling links to a deleted proposal

---

## 2. Background & Context

`proposal`-depth work starts in Backlog with `devkit spec proposal new <slug>`, which binds `proposal.md` to
`sdd-proposal`; the user's confirmation of the draft is `plan-intent`, which includes the Planning `activity-effort`
the agent proposes. Planning runs on `plan-<slug>`: the `spike` stage gathers evidence through the `scout` role and
criticism through the `challenger` role, which the effort requires from `medium` up, `devkit spec proposal padr`
records preliminary decisions and the questions for the user are collected in one round. After `plan-accept`, `devkit
workflow next` reports the proposal unit complete, and Development starts with `devkit spec proposal handoff <slug>`,
which creates the spec bundle bound to `sdd-spec-<task_kind>`.

---

## 3. Acceptance Criteria (Given / When / Then)

### Scenario 1: An accepted proposal is handed off
- **Given**: a proposal bundle with `status: accepted`, one PADR and a non-empty `materials/`
- **When**: the agent runs `devkit spec proposal handoff <slug>`
- **Then**: `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` exists with `spec.md` bound to `sdd-spec-feature`, the PADR is an
  accepted ADR under `docs/decisions/<YYYY-MM>/`, the materials are under `docs/materials/<YYYY-MM>/<YYYYMMDD>-<slug>/`,
  the proposal directory is gone, and the output lists `[PROMOTED_ADR: ...]`, `[MATERIALS: ...]` and
  `[NEXT_CMD: devkit workflow next --unit <dir>]`

### Scenario 2: Approval is never inferred
- **Given**: a proposal with `status: draft` or `reviewing`: `plan-accept` was not given
- **When**: the agent runs `devkit spec proposal handoff <slug>`
- **Then**: the command exits `2` with `SPEC_PROPOSAL_NOT_APPROVED` and writes nothing

### Scenario 3: References into the proposal follow it
- **Given**: a story that cites the proposal by ID and links its `proposal.md`
- **When**: the handoff completes
- **Then**: the ID now names the spec and the link points at `spec.md`, each reported as a `[REWRITTEN: ...]` line,
  and a `SPEC_PROPOSAL_REFS_REWRITTEN` notice asks the agent to reread the rewritten sentences

### Scenario 4: A defect proposal hands off to the bugfix workflow
- **Given**: a proposal created with `--task-kind bugfix` and accepted
- **When**: the agent hands it off
- **Then**: the spec bundle holds only `spec.md`, bound to `sdd-spec-bugfix`, and the proposal's target
  area and boundaries appear in its `### Target Area & Boundaries` notes

### Scenario 5: The proposal's approvals carry by name
- **Given**: an accepted proposal whose unit recorded `gate:plan-intent` and `gate:plan-accept` by the user
- **When**: the agent hands it off
- **Then**: the spec holds the same two requests as decision records with note `PROP-<slug>`, each reported as
  `[CARRIED_GATE: ...]`; `plan-intent` is not asked again and `plan-accept` satisfies no spec stage


### Scenario 6: Planning observations follow the outcome
- **Given** a proposal with open and settled feedback, captured inside its own write boundary
- **When** Planning returns to the user and the proposal is later handed off
- **Then** each enabled run sweep has fresh recorded coverage, open feedback enters the spec with unchanged IDs,
  statuses and observation dates, settled feedback is preserved as material, and Development supplies its own sweep

### Scenario 7: Deletion without handoff preserves open work
- **Given** rejected or decomposed proposal feedback
- **When** the Host deletes the original proposal
- **Then** open feedback is preserved once in the month-level backlog with retrievable historical context and valid
  current references; invalid input, collisions or unresolved live dependencies prevent deletion
