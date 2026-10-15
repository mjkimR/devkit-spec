---
reconcile_id: REC-handoff-unit-records
feature: SPEC-handoff-unit-records
status: resolved
targets:
  - file: docs/capabilities/delivery/CAP-DLV-proposal-incubation.md
    resolution: modified
  - file: docs/capabilities/delivery/CAP-DLV-delivery-workflows.md
    resolution: modified
  - file: docs/architecture/ARCH-06-runtime-view.md
    resolution: modified
---

# Reconciliation: Proposal handoff and the workflow records of the proposal unit

The incubation capability states the new rule 12: the proposal unit's devkit decision records and envelopes are
dropped with the proposal, and the spec's open G1 and G2 are recorded from the user's recorded acceptance of the
proposal's direction, with a `SPEC_PROPOSAL_GATE_NOT_CARRIED` warning when that fails. Rule 8, the bundle layout, the
handoff steps (a new step 8) and the output section follow. The delivery capability's G1 and incubation rules point
to it, and the runtime view shows the recording step.

The bundle's workflow gate rules (`incubated-delivery`, `direct-delivery`, `bugfix`) and the `spec` and `spec-next`
handoff references say the same; they are bundle assets, not Living Spec documents.

No ADR: the change applies rule 2 ("approval is never inferred") as it stands, carrying only an existing answer of the
user. Deferred: replacing `--direction-chosen` with a check of the proposal's direction record.
