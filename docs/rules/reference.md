# Rules Reference

The governance rules the `spec` bundle ships. `devkit sync` deploys them with the bundle's `core` preset and
`devkit rules` runs them with devkit's own rules: `devkit rules check` (whole workspace, or named targets),
`check --staged` (the commit gate), `check --ci` and `devkit rules fix`. `devkit rules explain <RULE-id>` prints a
rule's guide. A project tunes phases, severities and exclusions in `[rules]` of `.devkit/config.toml`
([devkit rules reference](https://github.com/mjkimR/devkit/blob/main/docs/rules/reference.md)).

Every rule reads the document index ([documents overview](../documents/overview.md)) through the run's workspace
cache, so `--staged` and `--ci` see the snapshot they evaluate. As with every devkit rule, a violation is reported
only in the files the run targets. Files of completed spec bundles are work history: checked only when named as
explicit targets, never rewritten (`RULE-spec-lifecycle` checks completed bundles: its conditions concern them).

Not ported yet: specrig's document namespaces (`docs/packages/<name>/`); the rules check the global `docs/` tree only.

## Catalog

| Rule | Phase, severity | Checks | Fix |
| --- | --- | --- | --- |
| `RULE-document-reference` | linter, error | Relation fields hold full IDs of the right kind; every reference resolves to exactly one document; prose uses `` `ID` ``; no relative links to ID-bearing documents; no duplicate IDs; no proposal sharing its slug with a spec. | `[ID]` to `` `ID` ``; a handed-off `PROP-<slug>` to its `SPEC-<slug>`. |
| `RULE-id-convention` | linter, error | Dated partitions (`docs/decisions/<YYYY-MM>/<YYYYMMDD>-<slug>.md`, `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/`, feedback files); `id`/`reconcile_id` derived from the path (`ADR-`, `SPEC-`, `PLAN-`, `TASKS-`, `REC-`, `FB-<slug>`); Living Spec stems (`CAP-<AREA>-<slug>`, `US-<slug>`, `ARCH-[<NN>[-<n>]-]<slug>`, no sequence numbers, arc42 chapters only); `area` matching the directory; the first H1's ID token; duplicate IDs; no date- or number-based references (`ADR-0006`, `US-010`). | `id`, `reconcile_id`, `area` and the H1 token aligned to the path. Files are never moved. |
| `RULE-spec-format` | linter, error | Every Markdown file under `docs/capabilities/`, `docs/stories/` and `docs/proposals/` has a well-formed frontmatter block with string `id`, `title` and `status`. | Adds a missing block or missing fields (`id` from the file stem, `title` from the H1, `status: draft`, `created_at`). |
| `RULE-traceability-link` | linter, error | A story's `capabilities` and a capability's `stories` link both ways. | Appends the missing reverse ID, keeping the list's style, when both IDs are unique. |
| `RULE-task-coverage` | linter, error | Each acceptance-criterion heading of a spec carries one `[AC-NN]`, IDs are unique, every criterion is cited by a task of `tasks.md` (on the task or its `_Requirements:_` line) and tasks cite only defined ones. A pair is checked when either file is targeted. | none |
| `RULE-spec-lifecycle` | linter, error | A completed spec has a resolved `reconcile.md`; a spec whose reconcile is resolved and whose tasks are all checked is marked `completed`. Completed bundles are checked too. | Sets `status: completed` in a targeted `spec.md`. |

## Layout

Each rule is a class in `devkit_spec.rules.<name>`; the bundle deploys `rules/<name>/<name>.py`, which subclasses it,
and the guide `rules/<name>/<name>.md`. Keeping the code in the package means one tested implementation and a
deployed file that never changes when the rule does.
