---
reconcile_id: REC-proposal-effort-hints
spec: SPEC-proposal-effort-hints
status: resolved
targets:
  - file: docs/capabilities/delivery/CAP-DLV-proposal-incubation.md
    resolution: modified
  - file: docs/capabilities/delivery/CAP-DLV-delivery-workflows.md
    resolution: modified
  - file: docs/capabilities/documents/CAP-DOCS-document-lookup.md
    resolution: modified
  - file: docs/capabilities/governance/CAP-GOV-spec-rules.md
    resolution: modified
  - file: docs/capabilities/harness/CAP-HARN-agent-guidance.md
    resolution: modified
---

# Reconcile Record: `SPEC-proposal-effort-hints`

## 1. Reconciled Targets

- `docs/capabilities/delivery/CAP-DLV-proposal-incubation.md` (`modified`): Documented `planning_effort` and `dev_effort` proposal frontmatter fields (`low` | `medium` | `high`, default `medium`), `--planning-effort` and `--dev-effort` CLI options and `[PROPOSAL]` / `[HANDOFF]` outputs, `CreatedProposal` / `HandoffResult` library fields, handoff preflight validation (`SPEC_PROPOSAL_INVALID`), and non-propagation to `spec.md`.
- `docs/capabilities/delivery/CAP-DLV-delivery-workflows.md` (`modified`): Updated §3 rule 15 to describe how proposal `planning_effort` and `dev_effort` hints guide Planning and Development start while confirmed run effort is recorded on `worker-NN.yaml` envelopes.
- `docs/capabilities/documents/CAP-DOCS-document-lookup.md` (`modified`): Documented `task_kind`, `planning_effort`, and `dev_effort` fields on `devkit spec list` proposal items (`[DOCUMENT: ...]` sentinel and JSON `documents[]`).
- `docs/capabilities/governance/CAP-GOV-spec-rules.md` (`modified`): Updated `RULE-spec-format` catalog and §3.5 contract to cover `planning_effort` and `dev_effort` validation on proposal anchors.
- `docs/capabilities/harness/CAP-HARN-agent-guidance.md` (`modified`): Updated §3 rule 4 to document proposal effort hint scaffolding in Backlog, refinement before `plan-accept`, and handoff default usage.
