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

### Spike Findings

- **Q1**: a proposal unit holds devkit decision records (`decisions/<NN>-<request>.yaml`, written by `devkit workflow
  answer`) and envelopes (`envelopes/<kind>-<NN>.yaml`, written by `devkit workflow envelope new`, for example by a
  delegated spike). devkit's public loaders find exactly these files: `load_decisions(unit)` returns each record and
  each malformed `NN-*.yaml` with its unit-relative `file`, `load_envelopes(unit)` likewise. Another file under
  `decisions/` (`PADR-*.md`, a `notes.yaml`) is not one of them, so the handoff needs no name pattern of its own.
- **Q2**: carrying the records into the spec bundle does not work. devkit counts only the decision records of the
  bound workflow's current segment, so `incubated-delivery` records in a `direct-delivery` unit are dead weight that
  still takes sequence numbers, and an envelope without a workflow scope counts in every workflow, so a spike's
  envelope could satisfy a check of the spec. Moving them to `docs/materials/` (today) puts workflow state in the
  durable research area, where nobody reads it. Git history keeps the proposal anyway.
- **Q3**: in `SPEC-orchestration-mode` the spec's G1 and G2 were recorded `--by user` right after the handoff, from
  the proposal's answers, without a second question: an undocumented carry. specrig never asked again either (its G1
  exit was the spec directory's existence and its G2 was conditional). The direct-delivery G1 rule (recorded once the
  user confirmed goal, scope and verification) is met by the proposal's direction answer, because the user accepted
  the proposal's design and acceptance checks there. Carrying an existing explicit `accept` by the user for the same
  work is not inference; deriving one from `status: accepted` or from context would be. The library form of `devkit
  workflow answer` (`record_answer`) validates against the spec's open requests, so the handoff can record through
  devkit's public surface. In `bugfix` the direction gate opens only after `characterize`, so it cannot be answered at
  handoff time.
- **Q4**: not needed. With Q1's loaders the handoff identifies devkit's records exactly, while moving devkit's
  `decisions/` would touch every unit, devkit's docs and every existing record for one consumer's naming collision.
  Revisit only if another consumer collides with it.

## 3. Proposed Design & Impact

Options:

- **Records (Q2)**: **R1** drop the proposal unit's decision records and envelopes at handoff and list them in the
  result (recommended); R2 carry them into the spec bundle (rejected, Q2); R3 keep moving them to `docs/materials/`
  (today, rejected).
- **Gates (Q3)**: **A1** the handoff records the spec's gates from the proposal's answer (recommended); A2 ask the
  user again after every handoff; A3 a skill rule that has the agent record them after the handoff, without code.

Chosen direction (G2): R1 + A1.

- `devkit spec proposal handoff` drops every decision record and envelope devkit's loaders return for the proposal
  unit (malformed ones included) instead of carrying them; PADRs and other extras are carried as today. The result
  lists the dropped paths (`dropped_records`).
- When the proposal's effective `gate:direction` record is `accept` with `by: user`, the handoff records, after the
  spec bundle is bound, `gate:intent` and then `gate:direction` (when it is open at that point; not in `bugfix`)
  through `record_answer`, `by: user`, note `PROP-<slug>`, and lists them in the result (`carried_gates`). Otherwise
  (direction by policy, a Route 4 team acceptance without a record, an unbound spec) nothing is recorded and the
  spec's gates open as today. A recording failure never fails the handoff: it is a warning whose `[FIX]` is the
  `devkit workflow answer` command.
- Impact: `src/devkit_spec/proposals/handoff.py` and its tests; `CAP-DLV-proposal-incubation` (rule 8 and a new
  rule); the gate rules of `incubated-delivery`, `direct-delivery` and `bugfix` (G1 of a handed-off spec).

Non-Goals: replacing `--direction-chosen` with a check of the proposal's direction record; any devkit change.

## 4. Lifecycle & Retirement Criteria

- Expected acceptance checks: a handoff of a proposal with answered gates writes no unit record under
  `docs/materials/`; the spec's gate behavior after handoff matches the documented rule; handoff tests cover both.
- On acceptance: set `status: accepted` and run `devkit spec proposal handoff handoff-unit-records`. On rejection:
  record a rejection ADR and delete the proposal directory.
