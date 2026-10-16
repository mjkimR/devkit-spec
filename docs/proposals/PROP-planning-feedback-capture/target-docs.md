---
id: PROP-planning-feedback-capture-target
title: Target contracts for Planning feedback capture
status: draft
proposal: PROP-planning-feedback-capture
created_at: 2026-10-16
targets:
  - file: docs/capabilities/harness/CAP-HARN-agent-guidance.md
  - file: docs/capabilities/delivery/CAP-DLV-delivery-workflows.md
  - file: docs/capabilities/delivery/CAP-DLV-proposal-incubation.md
  - file: docs/capabilities/documents/CAP-DOCS-document-model.md
  - file: docs/capabilities/governance/CAP-GOV-spec-rules.md
---

# Target contracts for Planning feedback capture

- `CAP-HARN-agent-guidance`: proposal-local destination; per-run capture for direct and worker execution; sweeps before
  every Planning return; existing capture/stage policy matrix; unchanged Planning write root; preservation before cleanup.
- `CAP-DLV-delivery-workflows`: proposal collect-feedback stage, its shared-stage contract and proposal-local evidence;
  a new sweep per Planning run, with no fresh rejection worker and no evidence carried to Development.
- `CAP-DLV-proposal-incubation`: open/settled feedback routing during handoff, preflight safety, rollback, relocation
  rewriting, historical-reference/context preservation and reference validation before deletion without handoff. A rejected proposal retains feedback until cleanup.
- `CAP-DOCS-document-model`: proposal-local feedback is a supported location for the existing feedback document kind;
  current feedback remains discoverable before and after relocation.
- `CAP-GOV-spec-rules`: path/ID/H1 validation for proposal-local feedback without treating it as a proposal or PADR.

Source implementation targets are `proposals/handoff.py`, its relocation helpers as needed, `rules/id_convention.py`
and its guide/tests, the `spec-feedback` skill and sweep reference, `spec` Planning/close/worker-record references,
`spec-next` workflow signals, both worker contracts, `spec-delegate` payload/worker references, the feedback-hygiene
playbook's proposal-cleanup instructions as applicable, and `workflows/sdd-proposal.md`, all under `src/devkit_spec/`.
Tests extend the proposal handoff, lookup/namespace, rule and workflow suites. No CLI command or upstream private API
is introduced. A needed upstream public primitive is reported as a dependency rather than implemented in this package.

The new ADR is promoted from `PADR-planning-feedback-in-proposal`; no existing ADR is edited. Outside this repository,
strategy 01 §6.2 must be updated first after acceptance and before Development handoff. The proposal's §3.4 supplies
verification scenarios for the later spec and tasks; this blueprint is not a claim that the behavior already exists.
