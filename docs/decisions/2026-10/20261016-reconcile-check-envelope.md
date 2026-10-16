---
id: ADR-reconcile-check-envelope
title: Record the reconcile verification as a reconcile-check envelope the Living Spec stage reads
summary: Every activity-effort records the verification of the implementer's reconcile as a reconcile-check envelope at living-spec-draft, whose exit requires it, so the check is enforced and its findings never reopen the review round.
status: accepted
created_at: 2026-10-16
---

# [ADR-reconcile-check-envelope] Record the reconcile verification as a reconcile-check envelope the Living Spec stage reads

- **Status**: Accepted
- **Date**: 2026-10-16
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `CAP-DLV-delivery-workflows`

---

## 1. Context & Problem Statement

The strategy layer's master flow (workbench `docs/strategy-layer/01-master-flow.md` §2.3) has the implementer write
the Living Spec reflection and `reconcile.md` at every `activity-effort`, verified by the implementer at `low`, by the
`reviewer` at `medium` and by a separate `reconciler` at `high`. Nothing recorded or enforced that verification: a
walkthrough of the local flow found no defined place for the `medium` reviewer's reconcile check, and recording it as
a `review` envelope with a finding sent `devkit workflow next` back to `review-refine`, whose exit reads the latest
review round.

---

## 2. Decision Drivers

- The verification is enforced by the workflow, not only described.
- One stage exit for every effort; only who verifies changes.
- A reconcile finding is fixed in the reconcile, never by reopening the code review.

---

## 3. Considered Options

### Option 1: A `reconcile-check` envelope read by the `living-spec-draft` exit (Selected)
- **Overview**: `living-spec-draft` (shared by `sdd-spec-feature` and `sdd-spec-bugfix`) exits on
  `envelope-completed(reconcile-check)` besides the resolved record and the completed spec.
- **Pros**: enforced at every effort with devkit's existing `envelope-completed` primitive; no devkit change; the
  review round is untouched.
- **Cons**: one more envelope per Unit-path Development.

### Option 2: Record it as a `review` round
- **Overview**: the reviewer's reconcile check is a second review round.
- **Cons**: a finding reopens `review-refine`; nothing requires the check at `low` or `high`.

---

## 4. Decision Outcome

Option 1:

- Every effort writes a `reconcile-check` envelope at `living-spec-draft`: at `low` the implementer's self-check,
  stated as such; at `medium` the reviewer's check of the written reconcile, returned separately from its code review;
  at `high` the `reconciler`'s independent verification. The roles stay read-only: the implementer records their
  returned fields.
- On findings the implementer fixes the reflection or `reconcile.md` and writes a new `reconcile-check`; the latest
  one decides.
- A contradiction between the implementation and a contract still takes the stage's return to the build stage.

---

## 5. Consequences

- The reviewer and reconciler contracts return the fields of a `reconcile-check`; the reconciler's former envelope
  kind `reconciler` is gone.
- Units bound before this change see a new unmet exit at `living-spec-draft` (a schema drift to accept with
  `devkit workflow bind`).
