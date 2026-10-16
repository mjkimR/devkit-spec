---
reconcile_id: REC-review-role-policy
feature: SPEC-review-role-policy
status: resolved
targets:
  - file: docs/capabilities/delivery/CAP-DLV-delivery-workflows.md
    resolution: modified
  - file: docs/capabilities/harness/CAP-HARN-agent-guidance.md
    resolution: modified
  - file: docs/glossary.md
    resolution: modified
  - file: docs/decisions/2026-10/20261016-medium-review-delegation.md
    resolution: modified
---

# Reconciliation: review role policy

Reflect the distinct read-only roles, mandatory initial medium code review, conditional initial reconcile
self-verification and discretionary medium repeat delegation. Preserve stages, effort and completion evidence.
`ADR-medium-review-delegation` records the lasting policy and supplements `ADR-reconcile-check-envelope`.
Existing capability entrypoints already cover workflows and subagents; metadata-only harness and glossary changes
do not justify broader entrypoints. No concrete follow-up is deferred.
