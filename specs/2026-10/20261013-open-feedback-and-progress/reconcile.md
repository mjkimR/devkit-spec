---
reconcile_id: REC-open-feedback-and-progress
feature: SPEC-open-feedback-and-progress
status: resolved
targets:
  - file: docs/capabilities/documents/CAP-DOCS-document-model.md
    resolution: modified
  - file: docs/capabilities/documents/CAP-DOCS-document-lookup.md
    resolution: modified
  - file: docs/capabilities/delivery/CAP-DLV-proposal-incubation.md
    resolution: modified
  - file: docs/capabilities/governance/CAP-GOV-spec-rules.md
    resolution: modified
  - file: docs/architecture/ARCH-05-1-containers.md
    resolution: modified
  - file: docs/architecture/ARCH-05-2-components.md
    resolution: modified
  - file: docs/glossary.md
    resolution: modified
---

# Reconciliation: `SPEC-open-feedback-and-progress`

- `CAP-DOCS-document-model`: historical documents exclude a completed bundle's `feedback/` (section 3.1 item 7,
  the `status` field, the library example).
- `CAP-DOCS-document-lookup`: `--history` no longer governs feedback; the open-critical-feedback example drops it.
- `CAP-DLV-proposal-incubation`: the handoff rewrite scans the feedback of completed bundles.
- `CAP-GOV-spec-rules`: ten rules; the catalog and section 3.9 add `RULE-spec-progress` (warning); the history
  behavior keeps feedback current; later sections renumbered.
- `ARCH-05-1-containers`, `ARCH-05-2-components`: ten rule files and rules.
- The glossary's historical document entry excludes feedback.
- `CAP-DOCS-document-search` needs no change: its candidates follow `CAP-DOCS-document-model`.
- No story changes: `US-find-the-right-documents` and `US-keep-the-living-spec-consistent` describe completed bundles
  as history in general terms that still hold.
- No deferred work is retained.
