---
id: ADR-approval-gates-intent-direction-integration
title: Map G1, G2 and G3 to devkit's intent, direction and integration gates
summary: The delivery workflows express specrig's human gates G1, G2 and G3 as devkit approval gates named intent, direction and integration, governed by [workflow.approvals]; devkit's default of ask for every gate is kept.
status: superseded
created_at: 2026-10-13
superseded_by: ADR-integration-approval-asserted
---

# [ADR-approval-gates-intent-direction-integration] Map G1, G2 and G3 to devkit's intent, direction and integration gates

- **Status**: Superseded by `ADR-integration-approval-asserted`
- **Date**: 2026-10-13
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `CAP-DLV-delivery-workflows`, `CAP-DLV-project-policy`

---

## 1. Context & Problem Statement

specrig's workflows had three human decision points: G1 (the user's intent: goal, scope, verification), G2 (the
direction among alternatives) and G3 (approval to integrate), expressed as human exit checks (`intent-recorded`,
`direction-chosen`, `approval-given`) and configured in `.specrig/config.yml`, where `direction` defaulted to `auto`.
devkit's workflow engine has approval gates: a stage declares `human_gate: <name>`, `[workflow.approvals]` sets each
gate to `ask`, `auto` or `off` (default `ask`), and `devkit workflow answer` records the user's decision.

---

## 2. Decision Drivers

- Gate decisions are recorded, never inferred, and a policy can delegate them explicitly.
- devkit stays SDD-agnostic: its defaults are not tuned for one methodology.
- Stage definitions shared by several workflows stay identical (`devkit workflow validate`).

---

## 3. Considered Options

### Option 1: devkit gates `intent`, `direction`, `integration` (Selected)
- **Overview**: G1, G2 and G3 are the stages whose `human_gate` is `intent`, `direction` and `integration`; the human
  exit checks are dropped and `entry` lists name the gate stage's predecessor checks.
- **Pros**: policy per gate, recorded decisions, `[WAITING: human gate:<gate>]` from `devkit workflow next`.
- **Cons**: devkit's default `ask` differs from specrig's `direction = auto`.

### Option 2: Keep human exit checks
- **Overview**: port `intent-recorded`, `direction-chosen` and `approval-given` as declared `human` checks.
- **Pros**: closest to specrig.
- **Cons**: no gate policy, no decision records; `--given` would assert approvals.

### Option 3: Change devkit's default for `direction` to `auto`
- **Overview**: make devkit match specrig.
- **Pros**: specrig behaviour without configuration.
- **Cons**: a methodology default inside the SDD-agnostic foundation.

---

## 4. Decision Outcome

We decided to adopt **Option 1**, keeping devkit's default `ask` for every gate.

**Rationale**: devkit's gates give recorded, policy-governed decisions; a project that wants specrig's behaviour sets
`direction = "auto"` in `[workflow.approvals]`.

---

## 5. Consequences

- **Positive**: under `auto` a gate passes by policy and `devkit workflow next` shows `source=policy`, reported as
  policy delegation, never as a human approval; `off` skips the stage.
- **Negative / Risks**: without configuration every gate waits for the user, including G2.
- **Follow-ups**: the `exception` stage has no gate (its decision is the `exception-handled` human check); G3 has no
  exit checks of its own and is asked once the final change report holds; `incubated-delivery` uses `intent` and
  `direction` only; the intent gate always needs the user's intent; neither `ask` nor `auto` grants commit, merge,
  publication or deletion authority.
