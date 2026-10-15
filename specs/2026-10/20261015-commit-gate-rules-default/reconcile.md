---
reconcile_id: REC-commit-gate-rules-default
feature: SPEC-commit-gate-rules-default
status: resolved
targets:
  - file: docs/glossary.md
    resolution: modified
  - file: docs/architecture/ARCH-03-context.md
    resolution: modified
  - file: docs/architecture/ARCH-06-runtime-view.md
    resolution: modified
---

# Reconciliation: `SPEC-commit-gate-rules-default`

- Glossary, **Commit gate**: devkit's built-in `rules-check` gate, on by default, runs the rules on the staged tree.
- `ARCH-03-context`: devkit owns the hook wrappers and both built-in pre-commit gates; `rules-check` is what runs the
  spec rules at commit time.
- `ARCH-06-runtime-view`, scenario 3: the gate calls the rule engine in its own process, evaluates in place or on a
  materialized tree, and refuses with `GATE_RULES_FAILED`.
- No capability or story changes: `CAP-GOV-spec-rules` and `US-keep-the-living-spec-consistent` describe the commit
  gate as `check --staged` on the exact staged tree, which still holds.
- No decision changes: the default comes from devkit; `ADR-rules-implemented-in-the-package` already requires
  devkit-spec in the commit gate's environment.
- No deferred work is retained.
