---
id: FB-handoff-moves-gate-decisions-to-materials
title: Proposal handoff moves the proposal's gate decision records into docs/materials
scope: repo
kind: question
category: spec-ambiguity
target: devkit spec proposal handoff
skill: spec
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: promoted
created_at: 2026-10-15
---

# [FB-handoff-moves-gate-decisions-to-materials] Proposal handoff moves the proposal's gate decision records into docs/materials

## 1. Friction / Question (friction, question)

- **Context**: Handing off the orchestration-mode proposal, whose G1 and G2 were answered (`decisions/01-gate-intent.yaml`,
  `decisions/02-gate-direction.yaml`).
- **Expectation**: The proposal's workflow records either stay with the proposal's history or are dropped; the new
  spec's G1 is "normally confirmed by the accepted proposal" (`incubated-delivery.md`).
- **Actual**: The handoff treated `decisions/` like research material and moved both YAML files to
  `docs/materials/2026-10/20261015-orchestration-mode/decisions/`, a tracked current-state area. The new spec started
  with G1 and G2 unanswered, so both were answered again.
- **Workaround (or Interpretation Chosen)**: Kept the moved files and answered the spec's G1 and G2 with `--by user`.
- **Suggestion**: Decide whether workflow decision records under a proposal's `decisions/` (devkit's unit records,
  not PADRs) are dropped at handoff (Git keeps them) or carried, and whether the handed-off spec's G1/G2 can be
  satisfied by the proposal's answers instead of asking again.

## Diagnostic Details

- **Reproduction**: Answer G1 and G2 of a proposal, then `devkit spec proposal handoff <slug> --direction-chosen`.
- **Expected / Actual**: Expected no unit records under `docs/materials/`; actual two decision YAML files there.
- **Versions**: devkit-spec `d75e673`; devkit-agt `856f1af`.
- **Conditions**: proposal `status: draft`, handoff inside the slug's worktree.
- **Workarounds Attempted**: none beyond re-answering the spec gates.
- **Related Assets**: `src/devkit_spec/proposals/handoff.py`, `workflows/incubated-delivery.md`,
  `CAP-DLV-proposal-incubation`.

## Evidence

```text
[MATERIALS: docs/materials/2026-10/20261015-orchestration-mode]
$ find docs/materials/2026-10 -type f
docs/materials/2026-10/20261015-orchestration-mode/decisions/01-gate-intent.yaml
docs/materials/2026-10/20261015-orchestration-mode/decisions/02-gate-direction.yaml
$ devkit workflow next --unit specs/2026-10/20261015-orchestration-mode   -> [WAITING: human gate:intent]
```

- **Disposition**: `SPEC-handoff-unit-records` (draft): what handoff does with the proposal unit's gate records and envelopes, and how the spec's gates follow.
