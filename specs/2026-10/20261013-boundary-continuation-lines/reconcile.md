---
reconcile_id: REC-boundary-continuation-lines
feature: SPEC-boundary-continuation-lines
status: resolved
targets:
  - file: docs/capabilities/traceability/CAP-TRACE-code-entrypoints.md
    resolution: modified
---

# Reconciliation: `SPEC-boundary-continuation-lines`

- `CAP-TRACE-code-entrypoints`: the code side of the derivation reads continuation lines of a `_Boundary` value and
  names what ends one.
- `CAP-COLL-work-scope-registry` defers `_Boundary` parsing to `CAP-TRACE-code-entrypoints`; no change.
- No story, architecture or decision changes. No deferred work is retained.
