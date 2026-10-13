# RULE-reconcile-contract

`reconcile.md` in a spec bundle records how the change was reconciled into the Living Spec (`docs/`). The
`spec-sync` skill writes it; `RULE-spec-lifecycle` requires it to be `resolved` before the spec is `completed`.

```yaml
---
reconcile_id: REC-<slug>
status: resolved            # pending while reconciliation is under way
targets:
  - file: docs/capabilities/core/CAP-CORE-search.md
    resolution: modified    # changed with this work
  - file: docs/stories/core/US-find-docs.md
    resolution: waived
    rationale: The story's acceptance criteria are unchanged by the new ranking mode.
---
```

## Violations

- No frontmatter, malformed frontmatter, or a missing `reconcile_id`.
- `status` other than `pending` or `resolved`.
- `targets` missing or not a list (use `targets: []` when nothing in the Living Spec is affected).
- A target that is not a mapping, a `file` that is not a unique workspace-relative path, a `resolution` other than
  `modified` or `waived`, or a waiver whose `rationale` has fewer than 20 non-whitespace characters: a waiver says why
  the file needs no change.

## Scope

Every targeted `reconcile.md` of a current spec bundle; a completed bundle's record is history, checked only when named
as an explicit target. Not checked yet: that each `modified` target is in the diff of the commit or pull request that
resolves the record; compare the targets with `git diff --name-only` yourself before resolving.
