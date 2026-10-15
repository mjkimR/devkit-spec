---
reconcile_id: REC-list-unknown-status
feature: SPEC-list-unknown-status
status: resolved
targets:
  - file: docs/capabilities/documents/CAP-DOCS-document-lookup.md
    resolution: modified
  - file: docs/architecture/ARCH-08-cross-cutting.md
    resolution: modified
---

# Reconciliation: `SPEC-list-unknown-status`

- `CAP-DOCS-document-lookup`: the `--status` filter states the `SPEC_LIST_STATUS_UNKNOWN` notice (values no indexed
  document of the selected kinds carries, every kind without `KIND`, historical and other-namespace documents
  included; the statuses that occur in `[FIX]`; the filter still applies). The common warnings rule covers the notice
  and says it never changes the exit code, the exit-code section says notices always exit `0`, the summary names the
  notice, and the error-code row (added with the code) now says every kind counts without `KIND`.
- `ARCH-08-cross-cutting`: the advisory code family table names `CAP-DOCS-document-lookup` as the owner of
  `SPEC_LIST_STATUS_UNKNOWN`.
- No story changes: `US-find-the-right-documents` describes finding documents by ID, reference, code path and meaning;
  the notice refines the existing `list --status` filter without a new user goal.
- No decision changes: the notice follows the existing advisory and output contracts; no lasting policy changes.
