---
reconcile_id: REC-feedback-list-filters
feature: SPEC-feedback-list-filters
status: resolved
targets:
  - file: docs/capabilities/documents/CAP-DOCS-document-lookup.md
    resolution: modified
  - file: docs/materials/2026-10/20261013-specrig-port-map.md
    resolution: modified
---

# Reconciliation: `SPEC-feedback-list-filters`

- `CAP-DOCS-document-lookup`: the `--where` filter and its value contract, the feedback severity order, the feedback
  line and record fields, `--where` in `[NEXT_CMD]`, the `ARGUMENT_INVALID` condition, and the revised non-goals
  (feedback filters are `--where` fields; no per-kind defaults).
- `MAT-specrig-port-map`: the `list feedback` row no longer says the filters are not ported.
- No story changes: `US-find-the-right-documents` already covers finding documents by their fields.
- No architecture or decision changes: the filter stays inside the `list` command; `--where` reuses devkit's
  `ARGUMENT_INVALID`.
- No deferred work is retained.
