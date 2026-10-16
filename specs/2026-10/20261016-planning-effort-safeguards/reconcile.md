---
reconcile_id: REC-planning-effort-safeguards
feature: SPEC-planning-effort-safeguards
status: pending
targets:
  - file: docs/capabilities/delivery/CAP-DLV-delivery-workflows.md
    resolution: modified
  - file: docs/stories/delivery/US-incubate-and-hand-off-a-proposal.md
    resolution: modified
  - file: docs/glossary.md
    resolution: modified
---

# Reconciliation: `SPEC-planning-effort-safeguards`

- `CAP-DLV-delivery-workflows`: business rule 15 states the Planning effort levels (questions only at `low`, one
  `challenger` pass at `medium`, options compared with a `challenger` and a re-review at `high`), that the effort is
  always proposed with a reason when the activity starts (a proposal's with its `plan-intent`), and that the
  `plan-accept` request shows each Planning run's effort and the support-role envelopes. The delegation paragraph
  points to rule 15 for when the `challenger` runs. Section 4.2 keeps `spike` optional in the schema but states that
  it runs whenever the effort requires a `challenger` and that role returns are recorded at `spike`; section 4.6
  says the `challenger` has no stage of its own and is recorded at `spike`.
- `US-incubate-and-hand-off-a-proposal`: the background states that `plan-intent` includes the proposed Planning
  effort and that the `challenger` is required from `medium` up; the spike stage is no longer called optional for it.
- Glossary: "Role contract / support role" no longer says "always optional": the read-only roles are required or
  optional as the `activity-effort` asks (the `reviewer` at `medium` was already required on the Unit path), and the
  workers run only in `local-orchestrated` mode.
- `CAP-HARN-agent-guidance`: no change. It lists the skills and contracts, not the effort levels, which it leaves to
  `CAP-DLV-delivery-workflows`.
- No architecture change and no ADR: the effort table is owned by the strategy layer (workbench
  `docs/strategy-layer/01-master-flow.md` §2.3, decisions Q59–Q61), changed first in this work; no `MUST` of the
  Living Spec changed.
- No deferred work is retained. The devkit output of the effort record at a gate and autohub's `plan-accept` screen
  are non-goals of this spec, recorded as follow-ups in the strategy layer's §10.
