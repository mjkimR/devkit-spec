---
reconcile_id: REC-subagent-procedure-in-contract
feature: SPEC-subagent-procedure-in-contract
status: resolved
targets:
  - file: docs/capabilities/delivery/CAP-DLV-delivery-workflows.md
    resolution: modified
  - file: docs/capabilities/harness/CAP-HARN-agent-guidance.md
    resolution: modified
  - file: docs/architecture/ARCH-05-1-containers.md
    resolution: modified
---

# Reconciliation: `SPEC-subagent-procedure-in-contract`

- `CAP-DLV-delivery-workflows`: the spike paragraph (skill `spec-delegate` only); 4.6 role contracts (`skill`
  optional, the table's skill column for `challenger` and `scout`, what a contract body holds, where caller guidance
  lives, which roles have a shell, `challenger` delegated on request, payload-only invocation).
- `CAP-HARN-agent-guidance`: the skill count (12) in the scope, the `core` preset and the asset table; the
  `spec-challenge` and `spec-scout` rows removed from 4.4; the skill reference list gains
  `spec/references/playbooks.md` and `spec-delegate/references/hosts.md` (AC-08).
- `ARCH-05-1-containers`: the skill count of the `spec` bundle container.
- `README.md` carries the same count; it is not a Living Spec document.
- No story changes: no user-facing flow changes, only where a role's procedure is stored and what the caller sends.
- No decision changes: no `MUST` changes. `ADR-skills-named-spec` lists the skill names of its time and stays as
  accepted history.
- No deferred work is retained. Shell access for `challenger` and `reconciler` and skill preloading (non-goals 2 and
  4) stay out of scope with their reconsider triggers in `spec.md`.
