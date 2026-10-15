---
id: FB-current-reference-material
title: "A material used as a current map conflicts with materials being history"
scope: repo
kind: question
category: instruction-conflict
target: "MAT-port-map"
skill: spec-sync
agent: claude-code
origin: agent
severity: noise
recurring: false
status: promoted
created_at: 2026-10-13
---

# [FB-current-reference-material] A material used as a current map conflicts with materials being history

## 1. Friction / Question (friction, question)

- **Context**: Reconciling a change that ports a feature the port map marked as not ported
- **Expectation**: living-spec-writing places dated materials with history, which suggests they are not rewritten
- **Actual**: AGENTS.md cites the port map as the record of where each component went, so its row was wrong after this change
- **Workaround (or Interpretation Chosen)**: Rewrote the row in place and listed the material as a reconcile target
- **Suggestion**: Decide whether the port map is current-state (move it out of materials) or history (stop citing it as current)

## Evidence

```text
living-spec-writing: Change history belongs in Git, append-only ADRs ... and dated `docs/materials/`.
AGENTS.md: [`MAT-port-map`] records where each of its components went.
```

- **Disposition**: docs/development/port-map.md: S-Lane; the map moved out of materials as a current development document; references, the accepted ADR included, became links (one-off exception approved by the user during the migration)
