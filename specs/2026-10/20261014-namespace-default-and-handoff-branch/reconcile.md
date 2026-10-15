---
reconcile_id: REC-namespace-default-and-handoff-branch
feature: SPEC-namespace-default-and-handoff-branch
status: resolved
targets:
  - file: docs/capabilities/delivery/CAP-DLV-spec-bundles.md
    resolution: modified
  - file: docs/capabilities/delivery/CAP-DLV-proposal-incubation.md
    resolution: modified
  - file: docs/capabilities/documents/CAP-DOCS-namespaces.md
    resolution: modified
---

# Reconciliation: `SPEC-namespace-default-and-handoff-branch`

- `CAP-DLV-spec-bundles`: business rule 7 (the namespace of the current directory when `--namespace` is omitted),
  the `--namespace` row, the `namespace=` field of the `[SPEC: ...]` line and the JSON `namespace` key, `cwd` in the
  library example, and the `SPEC_CONFIG_INVALID` condition.
- `CAP-DLV-proposal-incubation`: business rule 11 (hand off in the slug's own worktree), the `--namespace` row, the
  `new` output, `cwd` in the library section, the new `SPEC_PROPOSAL_WRONG_WORKTREE` code and the
  `SPEC_CONFIG_INVALID` condition.
- `CAP-DOCS-namespaces`: the `--namespace` row of `devkit spec new` and `devkit spec proposal new` names the default.
- No story changes: `US-incubate-and-hand-off-a-proposal` and `US-run-parallel-work-safely` already cover creating
  bundles and keeping parallel tasks apart.
- No architecture or decision changes: the guard is one more pre-write validation of the handoff, and the default
  reuses the existing selection rule.
- The bundle's `living-spec-writing` instruction and `spec-specify` skill carry the package glossary and namespace
  guidance (AC-07); they are bundle assets, not Living Spec documents.
- No deferred work is retained. The proposal-content comparison (non-goal 1) and ID-less materials (non-goal 2) stay
  out of scope.
