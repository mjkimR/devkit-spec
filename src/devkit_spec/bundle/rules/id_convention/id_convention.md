# RULE-id-convention

A document's ID is a slug derived from its path. Dates order dated documents in their partitions; they are never part
of an ID, and neither are sequence numbers (they collide across parallel branches and make references ambiguous).

## Dated Partitions: ADR, Change Spec, Feedback

| Document | Path | ID |
| :--- | :--- | :--- |
| ADR | `docs/decisions/{YYYY-MM}/{YYYYMMDD}-{slug}.md` | `ADR-{slug}` |
| Spec bundle | `specs/{YYYY-MM}/{YYYYMMDD}-{slug}/spec.md`, `plan.md`, `tasks.md`, `reconcile.md` | `SPEC-{slug}`, `PLAN-{slug}`, `TASKS-{slug}`, `reconcile_id: REC-{slug}` |
| Feedback in a bundle | `specs/{YYYY-MM}/{YYYYMMDD}-{slug}/feedback/{name}.md` | `FB-{name}` |
| Month-level feedback | `specs/{YYYY-MM}/feedback/{YYYYMMDD}-{name}.md` | `FB-{name}` |

`{slug}` and `{name}` are kebab-case, and the `{YYYY-MM}` partition must match the date prefix. A feedback file
inside a bundle has no date prefix.

## Living Spec: Capability, Story, Architecture

The ID is the file stem:

| Document | Path | Also required |
| :--- | :--- | :--- |
| Capability | `docs/capabilities/{area}/CAP-{AREA}-{slug}.md` | `{AREA}` upper-case letters and digits; `area: {area}` |
| Story | `docs/stories/{area}/US-{slug}.md` | `area: {area}`; only `README.md` directly under `docs/stories/` |
| Architecture | `docs/architecture/ARCH-{slug}.md` or `ARCH-{NN}[-{n}]-{slug}.md` | `{NN}` an arc42 chapter below, `{n}` a sub-document (1-9) |

The first segment of `{slug}` must contain a letter: `CAP-HARN-001-foo` and `US-010-bar` are sequence numbers.

| NN | arc42 chapter | NN | arc42 chapter |
| :--- | :--- | :--- | :--- |
| 01 | Introduction and Goals | 07 | Deployment View |
| 02 | Architecture Constraints | 08 | Cross-cutting Concepts |
| 03 | System Scope and Context (C4 L1) | 09 | Architecture Decisions: `docs/decisions/`, no ARCH document |
| 04 | Solution Strategy | 10 | Quality Requirements |
| 05 | Building Block View (`05-1` containers, `05-2` components) | 11 | Risks and Technical Debts |
| 06 | Runtime View | 12 | Glossary: `docs/glossary.md`, no ARCH document |

Chapter numbers follow arc42's reading order, not allocation order. A deep-dive outside the chapters is `ARCH-{slug}`.

## Violations

- A path off the convention above (wrong depth, an undated or misdated partition, a sequence-number slug, chapter 09
  or 12, a capability or story outside an area directory). `README.md` files are not checked here. Nothing else is
  reported for the file until it is moved.
- No frontmatter.
- A frontmatter `id` (`reconcile_id` in `reconcile.md`) other than the path requires, or a capability's or story's
  `area` other than its directory. `devkit rules fix` sets them (inserting a missing one).
- A first `# ` heading whose `[ID]` or `` `ID` `` token is not the ID (a plan, tasks or reconcile heading may also name
  `SPEC-{slug}`). `devkit rules fix` rewrites the token.
- An ADR, spec or Living Spec ID that another file's path also derives: slugs are unique per document type across
  partitions and areas (feedback slugs only within their bundle). Rename one slug.
- A date- or number-based reference in the frontmatter or prose of any Markdown file under `docs/` (except
  `docs/materials/`) or `specs/`: `SPEC-20261006`, `FB-20261006`, `ADR-0006`, `PADR-0001`, `US-010`, `CAP-HARN-007`,
  or `ARCH-06` without a slug. Reference documents as `` `ADR-{slug}` ``, `` `SPEC-{slug}` ``,
  `` `CAP-{AREA}-{slug}` ``, `` `US-{slug}` ``, `` `ARCH-{NN}-{slug}` ``. Code blocks, indented code, inline code,
  HTML comments and escapes are not checked; Markdown link labels and targets are.

## Remediation

1. Move the file to the required path. `devkit rules fix` never moves files; `devkit spec resolve <ID>` finds a
   document by ID.
2. Run `devkit rules fix` to align `id` / `reconcile_id`, `area` and the heading token with the path.
3. Replace date- or number-based references with the slug ID by hand.

## Scope

Fields are read from their top-level frontmatter lines as written. Files of completed spec bundles are work history:
checked only when named as explicit targets, and never rewritten. Like every devkit rule, a violation is reported only
in the files the run targets, while duplicates are detected across the whole workspace. Package document roots
(`docs/packages/<name>/`) are not identifier targets yet; their references are checked.
