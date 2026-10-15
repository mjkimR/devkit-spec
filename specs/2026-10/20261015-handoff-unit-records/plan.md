---
id: PLAN-handoff-unit-records
spec: SPEC-handoff-unit-records
---

# Technical Plan: `SPEC-handoff-unit-records` Proposal handoff and the workflow records of the proposal unit

## 1. Constitution & Invariant Review

"Approval is never inferred" holds: the handoff records the spec's gates only from an existing decision record in
which the user accepted the proposal's direction, never from `status: accepted`, `--direction-chosen` or context.
Records name the authority (`by: user`) and the note holds only the proposal ID. `CAP-DLV-proposal-incubation` rule 8
("nothing in the bundle is lost") changes: the dropped records stay in Git history. Workflow frontmatter is
untouched, so no workflow hash changes.

## 2. Architecture Overview & Impact

- **Impacted Components**:
  - `src/devkit_spec/proposals/handoff.py`: before writing, collect the proposal unit's records with devkit's
    `load_decisions` and `load_envelopes` and the user's effective direction answer; exclude the records from the
    extras; after the proposal is removed, record the spec's open `gate:intent` and `gate:direction` with
    `record_answer` (`Workspace(root, lint=None, ancestor=None)`, `lint=False`). `HandoffResult` gains
    `dropped_records` and `carried_gates`.
  - `src/devkit_spec/errors.py`: `ProposalGateNotCarriedWarning` (`SPEC_PROPOSAL_GATE_NOT_CARRIED`, warning).
  - `src/devkit_spec/cli/proposals.py`: `[DROPPED_RECORD: <path>]` and `[CARRIED_GATE: <request> decision=<path>]`
    lines, JSON keys from `to_dict`.
  - Docs: `CAP-DLV-proposal-incubation` (rule 8, a new rule, 4.5, 4.10), `ARCH-06-runtime-view` (handoff notes).
  - Bundle: gate rules in `workflows/incubated-delivery.md`, `direct-delivery.md`, `bugfix.md`;
    `skills/spec/references/worktree.md`; `skills/spec-next/references/post-handoff.md`.
- **New Dependencies**: None (devkit's public `devkit.workflow` exports only).

## 3. Verification & Test Plan

- Unit: `tests/proposals/test_proposal_handoff.py` covers AC-01 to AC-04: dropped records and envelopes (malformed
  included) next to carried extras and PADRs, no materials directory for records alone, carried gates for
  `direct-delivery` and intent only for `bugfix`, each no-carry case, and a refused answer as a warning.
- CLI: `tests/proposals/test_proposal_cli.py` checks the new text lines and JSON keys.
- Commands: `just ci`; a handoff of a scratch proposal in a temporary project shows the lines and `devkit workflow
  next` on the spec.
