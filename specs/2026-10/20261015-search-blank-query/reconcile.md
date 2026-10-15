---
reconcile_id: REC-search-blank-query
feature: SPEC-search-blank-query
status: resolved
targets:
  - file: docs/capabilities/documents/CAP-DOCS-document-search.md
    resolution: modified
---

# Reconciliation: `SPEC-search-blank-query`

- `CAP-DOCS-document-search`: business rule 8 (now **Query**) states that an empty or whitespace-only query fails with
  `ARGUMENT_INVALID` (`[TARGET]` `QUERY`) and prints no `[SEARCH: ...]` line; the command section says the joined
  query must not be blank; the error paragraph lists the blank query among the `ARGUMENT_INVALID` conditions and
  limits "exit `0` with no hit" to a non-blank query. The summary and entrypoints are unchanged: the change is input
  validation inside `src/devkit_spec/cli/search.py`, already declared.
- No story changes: `US-find-the-right-documents` Scenario 2 searches with a non-blank intent, which behaves as before
  (AC-03).
- No architecture or decision changes: the check sits at the command line, reuses devkit's `ArgumentError`
  (`ARGUMENT_INVALID`) and adds no `SPEC_` code; `devkit_spec.search.search_documents` is unchanged.
- No deferred work is retained.
