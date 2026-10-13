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

Document namespaces: in a monorepo, each package registered in `[[tool.spec.namespaces]]` of `.devkit/config.toml`
([policy](../policy.md)) keeps its Living Spec under `docs/packages/<name>/`, which follows the same conventions as
`docs/`: `RULE-id-convention`, `RULE-spec-format` and `RULE-traceability-link` check
`docs/packages/<name>/{capabilities,stories,architecture}/` as they check `docs/{capabilities,stories,architecture}/`.
IDs and references stay repository-wide. `RULE-spec-format` also checks the `namespace` field of proposals and specs;
a run that targets `.devkit/config.toml` rechecks every one of them. A malformed `[tool.spec]` table is not a
violation: it fails the run (`RULES_EXECUTION_FAILED` naming the table, exit 2), as devkit fails on its own malformed
configuration, because the rules cannot tell which documents follow which conventions.

## Catalog

| Rule | Phase, severity | Checks | Fix |
| --- | --- | --- | --- |
| `RULE-document-reference` | linter, error | Relation fields hold full IDs of the right kind; every reference resolves to exactly one document; prose uses `` `ID` ``; no relative links to ID-bearing documents; no duplicate IDs; no proposal sharing its slug with a spec. | `[ID]` to `` `ID` ``; a handed-off `PROP-<slug>` to its `SPEC-<slug>`. |
| `RULE-id-convention` | linter, error | Dated partitions (`docs/decisions/<YYYY-MM>/<YYYYMMDD>-<slug>.md`, `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/`, feedback files); `id`/`reconcile_id` derived from the path (`ADR-`, `SPEC-`, `PLAN-`, `TASKS-`, `REC-`, `FB-<slug>`); Living Spec stems (`CAP-<AREA>-<slug>`, `US-<slug>`, `ARCH-[<NN>[-<n>]-]<slug>`, no sequence numbers, arc42 chapters only); `area` matching the directory; the first H1's ID token; duplicate IDs; no date- or number-based references (`ADR-0006`, `US-010`). | `id`, `reconcile_id`, `area` and the H1 token aligned to the path. Files are never moved. |
| `RULE-spec-format` | linter, error | Every Markdown file under `docs/capabilities/`, `docs/stories/` and `docs/proposals/` (and a namespace's `capabilities/` and `stories/`) has a well-formed frontmatter block with string `id`, `title` and `status`; a proposal's or spec's `namespace`, when set, is `global` or a registered namespace. | Adds a missing block or missing fields (`id` from the file stem, `title` from the H1, `status: draft`, `created_at`). |
| `RULE-traceability-link` | linter, error | A story's `capabilities` and a capability's `stories` link both ways. | Appends the missing reverse ID, keeping the list's style, when both IDs are unique. |
| `RULE-task-coverage` | linter, error | Each acceptance-criterion heading of a spec carries one `[AC-NN]`, IDs are unique, every criterion is cited by a task of `tasks.md` (on the task or its `_Requirements:_` line) and tasks cite only defined ones. A pair is checked when either file is targeted. | none |
| `RULE-spec-lifecycle` | linter, error | A completed spec has a resolved `reconcile.md`; a spec whose reconcile is resolved and whose tasks are all checked is marked `completed`. Completed bundles are checked too. | Sets `status: completed` in a targeted `spec.md`. |
| `RULE-reconcile-contract` | linter, error | A `reconcile.md` has `reconcile_id`, `status` `pending` or `resolved`, and `targets` of unique workspace-relative `file`s with `resolution` `modified` or `waived`, each waiver with a rationale of at least 20 non-whitespace characters. Not yet: specrig's diff evidence (a `modified` target must be in the resolving diff). | none |
| `RULE-code-entrypoints` | linter, error | Every `entrypoints` item of a capability or story (incl. `docs/packages/<name>/`) is a string, a literal workspace-relative path (no glob, absolute, `..`, backslash, colon, control char) and an existing file or directory inside the workspace ([Code entrypoints](../entrypoints.md)). A commit that deletes code without touching the document is caught only by a whole-workspace run. | none |

## Layout

Each rule is a class in `devkit_spec.rules.<name>`; the bundle deploys `rules/<name>/<name>.py`, which subclasses it,
and the guide `rules/<name>/<name>.md`. Keeping the code in the package means one tested implementation and a
deployed file that never changes when the rule does.
