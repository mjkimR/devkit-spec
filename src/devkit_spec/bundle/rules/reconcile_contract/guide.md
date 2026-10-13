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
as an explicit target.

**Diff evidence.** In a snapshot run (`devkit rules check --staged`, which the commit gate runs, and `--ci` on a pull
request), a `resolved` record that the diff changes must have each `modified` target changed or deleted by that diff:
commit the Living Spec edits together with the record that resolves them. `--ci` judges the whole branch against its
merge base, so a target changed in an earlier commit of the branch counts there. A record whose frontmatter is
unchanged from the base (only its body was edited, such as a rewritten link) claims nothing new and is not
re-checked. A plain `devkit rules check` has no diff and checks the form only.
