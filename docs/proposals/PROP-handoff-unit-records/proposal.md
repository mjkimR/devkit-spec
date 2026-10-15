---
id: PROP-handoff-unit-records
title: Proposal handoff and the workflow records of the proposal unit
summary: "Decide what a proposal handoff does with the devkit workflow records of the proposal unit (gate decisions and envelopes), which share the decisions/ directory with PADRs, and whether the handed-off spec's gates can reuse the proposal's answers."
status: draft                         # draft | reviewing | accepted | rejected
created_at: 2026-10-15
target_area: delivery/
priority: medium                      # critical | high | medium | low
size: S                               # S | M | L | XL
boundaries:
  owns:
    - delivery/
  excludes:
    - docs/decisions/
workflow: incubated-delivery
workflow_hash: sha256:c6cf386f9eb37b061d626d4bc701dd4e01f43674666d160179f69da5c391463e
---

# [PROP-handoff-unit-records] Proposal handoff and the workflow records of the proposal unit

## 1. Background & Hypothesis

A proposal bundle is a devkit workflow unit, so `devkit workflow answer` writes its G1 and G2 answers to
`docs/proposals/PROP-<slug>/decisions/NN-gate-<gate>.yaml`. The same `decisions/` directory holds the proposal's
PADRs. At handoff, `devkit spec proposal handoff` promotes each `decisions/PADR-<slug>.md` and carries every other
file of `decisions/` to `docs/materials/<YYYY-MM>/<YYYYMMDD>-<slug>/decisions/` (rule for non-PADR extras), so the
workflow decision records land in the tracked materials area. The new spec bundle then starts with G1 and G2 open,
although `incubated-delivery` says its G1 is normally confirmed by the accepted proposal. Observed in
`FB-handoff-moves-gate-decisions-to-materials`.

specrig wrote no gate records at all (approvals were reported, and G3 was a `--given` declaration), so it has no
precedent for this collision; its `decisions/` held only PADRs.

Hypothesis: workflow records of the proposal unit are dropped at handoff (Git keeps them), and the spec's G1 and G2
are either asked again as today or satisfied from the proposal's answers in one explicit, recorded way.

## 2. Technical Spike Questions

- **Q1**: Which unit records can a proposal hold (`decisions/NN-*.yaml`, `envelopes/`), and how does the handoff tell
  them apart from PADRs and research extras without guessing from names?
- **Q2**: Should handoff drop those records, keep them only in Git history, or carry them into the spec bundle?
- **Q3**: Can the spec's G1 and G2 be satisfied from the proposal's answers (for example by the handoff recording
  `--by user` answers that cite the proposal), and does that weaken "approval is never inferred"?
- **Q4**: Would moving devkit's unit records out of `decisions/` (a devkit change) be cleaner than special-casing the
  handoff?

## 3. Proposed Design & Impact

To be decided after the spike. Candidates: exclude `decisions/NN-*.yaml` and `envelopes/` from the handoff's extras
(`src/devkit_spec/proposals/handoff.py`), document the behavior in `CAP-DLV-proposal-incubation`, and state in
`incubated-delivery` how the spec's gates follow from the proposal's.

## 4. Lifecycle & Retirement Criteria

- Expected acceptance checks: a handoff of a proposal with answered gates writes no unit record under
  `docs/materials/`; the spec's gate behavior after handoff matches the documented rule; handoff tests cover both.
- On acceptance: set `status: accepted` and run `devkit spec proposal handoff handoff-unit-records`. On rejection:
  record a rejection ADR and delete the proposal directory.
