---
id: US-incubate-and-hand-off-a-proposal
title: Incubate a Proposal and Hand It Off to a Spec
summary: An AI coding agent shapes a high-uncertainty idea in a proposal bundle, records preliminary decisions, and, once the user approves the direction, hands it off to a bound spec bundle with decisions promoted, materials moved and references rewritten.
area: delivery
actor: AI coding agent
status: active
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

Routes 3 and 4 start with `devkit spec proposal new <slug>`, which binds `proposal.md` to `incubated-delivery`. The
optional `spike` stage gathers evidence through the `scout` and `challenger` roles; `devkit spec proposal padr`
records preliminary decisions. After the direction gate (G2), `devkit workflow next` reports the proposal unit
complete, and `devkit spec proposal handoff <slug>` creates the spec bundle bound to the proposal's
`handoff_workflow`.

---

## 3. Acceptance Criteria (Given / When / Then)

### Scenario 1: An accepted proposal is handed off
- **Given**: a proposal bundle with `status: accepted`, one PADR and a non-empty `materials/`
- **When**: the agent runs `devkit spec proposal handoff <slug>`
- **Then**: `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` exists with `spec.md` bound to `direct-delivery`, the PADR is an
  accepted ADR under `docs/decisions/<YYYY-MM>/`, the materials are under `docs/materials/<YYYY-MM>/<YYYYMMDD>-<slug>/`,
  the proposal directory is gone, and the output lists `[PROMOTED_ADR: ...]`, `[MATERIALS: ...]` and
  `[NEXT_CMD: devkit workflow next --unit <dir>]`

### Scenario 2: Approval is never inferred
- **Given**: a proposal with `status: draft` and no explicit choice by the user
- **When**: the agent runs `devkit spec proposal handoff <slug>` without `--direction-chosen`
- **Then**: the command exits `2` with `SPEC_PROPOSAL_NOT_APPROVED` and writes nothing

### Scenario 3: References into the proposal follow it
- **Given**: a story that cites the proposal by ID and links its `proposal.md`
- **When**: the handoff completes
- **Then**: the ID now names the spec and the link points at `spec.md`, each reported as a `[REWRITTEN: ...]` line,
  and a `SPEC_PROPOSAL_REFS_REWRITTEN` notice asks the agent to reread the rewritten sentences

### Scenario 4: A defect proposal hands off to the bugfix workflow
- **Given**: a proposal created with `--handoff-workflow bugfix` and accepted
- **When**: the agent hands it off
- **Then**: the spec bundle holds only `spec.md` with `kind: bugfix`, bound to `bugfix`, and the proposal's target
  area and boundaries appear in its `### Target Area & Boundaries` notes
