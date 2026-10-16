---
id: CAP-GOV-spec-rules
title: Spec Governance Rules
summary: Defines the ten governance rules the spec bundle ships for devkit rules (references, IDs, frontmatter, traceability, task coverage, spec lifecycle and progress, reconcile records, entrypoints, summaries), their shared targeting and snapshot behavior, fixes and layout.
area: governance
status: active
stories:
  - US-keep-the-living-spec-consistent
  - US-adopt-in-an-existing-repository
entrypoints:
  - src/devkit_spec/rules/
  - src/devkit_spec/bundle/rules/
created_at: 2026-10-13
---

# [CAP-GOV-spec-rules] Spec Governance Rules

## 1. Summary

The `spec` bundle ships ten deterministic rules that keep the Living Spec and the feature specs consistent. `devkit
sync` deploys them with the bundle's `core` preset, and devkit's rule engine runs them beside its own rules:
`devkit rules check` (whole workspace or named targets), `check --staged` (the commit gate), `check --ci --base <ref>`
and `devkit rules fix`. This capability is the catalog and the contract summary of each rule; the full guide of a rule
(examples, remediation steps) is what `devkit rules explain <RULE-id>` prints, deployed beside the rule.

## 2. Scope & Boundary

- **In-Scope**: the rule catalog, behavior every spec rule shares (document index, targeting, history, namespaces,
  configuration failures), each rule's checks and fix, and how the rules are packaged.
- **Out-of-Scope** (Non-Goals):
  - The rule engine (phases, severities, `[rules]` configuration, `explain`, `phases`, output sentinels, exit codes):
    devkit's ([devkit rules reference](https://github.com/mjkimR/devkit/blob/main/docs/rules/reference.md)).
  - The document model the rules read: `CAP-DOCS-document-model`.
  - The entrypoint path contract and derivation: `CAP-TRACE-code-entrypoints` (this capability summarizes
    `RULE-code-entrypoints` only).
  - Judging content quality (whether tasks fulfil criteria, whether a summary is accurate). Scope Excluded: the rules
    check structure and links; tests and review judge substance.
  - Moving files. Scope Excluded: no fix ever moves or renames a file.

## 3. Business Rules & Policies

### 3.1 Catalog

Every rule is phase `linter` and is deployed by the `core` preset; every rule is severity `error` except
`RULE-spec-progress` (`warning`), a progress hint that never blocks a commit.

| Rule | Checks | Fix |
| --- | --- | --- |
| `RULE-document-reference` | Relation fields hold full IDs of the right kind; every reference resolves to exactly one document; prose uses the code-span form; no relative links to ID-bearing documents; no duplicate IDs; no proposal sharing its slug with a spec. | Bracket form to code-span form; a handed-off `PROP-<slug>` to its `SPEC-<slug>`. |
| `RULE-id-convention` | Dated partitions and path-derived IDs; Living Spec stems; `area` matching the directory; the first H1's ID token; duplicate path-derived IDs; no date- or number-based references. | `id`, `reconcile_id`, `area` and the H1 token aligned to the path. |
| `RULE-spec-format` | Capabilities, stories and proposals have a frontmatter block with string `id`, `title`, `status`; a proposal's or spec's `namespace` is `global` or registered. | Adds a missing block or missing fields. |
| `RULE-traceability-link` | A story's `capabilities` and a capability's `stories` link both ways. | Appends the missing reverse ID. |
| `RULE-task-coverage` | Acceptance-criterion IDs of a spec and the task references of its `tasks.md` cover each other. | none |
| `RULE-spec-lifecycle` | A spec's `status`, its task checklist and its `reconcile.md` status agree. | Sets `status: completed` on a stale `spec.md`. |
| `RULE-spec-progress` | A `draft` or `planned` spec with a checked task is marked `in-progress`. | Sets `status: in-progress`. |
| `RULE-reconcile-contract` | A `reconcile.md` is well formed; in a snapshot run its `modified` targets changed in the diff. | none |
| `RULE-code-entrypoints` | Every `entrypoints` path of a capability or story is a valid, existing workspace path. | none |
| `RULE-document-summary` | Searchable documents carry a short English `summary`. | none |

### 3.2 Shared Behavior

1. **Document index**: every rule reads documents through the run's workspace cache (`CAP-DOCS-document-model`), so
   `--staged` and `--ci` evaluate the snapshot they name (devkit's `ctx.snapshot`) and a fix is seen by the recheck.
2. **Targeting**: as with every devkit rule, a violation is reported only in the files the run targets: a commit
   checks the files it changes, `devkit rules check` without targets the whole workspace. A rule whose relation spans
   several files (task coverage, lifecycle, traceability, entrypoints) states below where it reports when only one
   side is targeted.
3. **History**: files of completed spec bundles, their `feedback/` aside, are work history: checked only when named as explicit targets, never
   rewritten by a fix. `RULE-spec-lifecycle` is the exception: its conditions concern completed bundles, so it checks
   them in every run.
4. **Materials**: `docs/materials/` (and any `/materials/` directory, including `docs/packages/<name>/materials/`)
   is free-form and exempt from every authoring rule.
5. **Namespaces**: `docs/packages/<name>/` follows the conventions of `docs/` (`CAP-DOCS-namespaces`); IDs and
   references stay repository-wide.
6. **Malformed `[tool.spec]`**: a malformed `[tool.spec]` table is not a violation. It MUST fail the run
   (`SPEC_CONFIG_INVALID` naming the table, attributed to the rule, exit `2`), as devkit fails on its own malformed configuration, because
   the rules cannot tell which documents follow which conventions.
7. **Fixes**: fixes are deterministic, idempotent, honor `devkit rules fix --dry-run`, write only targeted current
   files, and change only the bytes they own.
8. **Tuning**: a project tunes phases, severities, exclusions and settings in `[rules]` of `.devkit/config.toml`
   (devkit's), for example `[rules.phase_overrides]` to move `RULE-document-summary` to `hygiene` while summaries are
   written, and `[rules.settings.RULE-document-summary] max_length`.

### 3.3 `RULE-document-reference`

Documents reference each other by exact, resolvable full IDs. Checks every current document that is not a material.

- MUST report: a relation field of the wrong shape, a value that is not a full ID, or an ID of the wrong kind
  (`stories`, `related_stories` take `US`; `capabilities`, `related_capabilities` take `CAP`; `spec` takes `SPEC`;
  `plan` takes `PLAN`).
- MUST report a reference to an ID no document declares or several documents declare; a missing or duplicated ID is
  fixed by hand (the rule never guesses which document was meant).
- MUST report a bracket reference in prose (fixable: converted to the code-span form).
- MUST report a `PROP-<slug>` reference that does not resolve when exactly one `SPEC-<slug>` exists, typically added
  on another branch after the handoff (fixable: rewritten to `SPEC-<slug>`). The fix never changes a spec's
  `proposal` provenance field and skips completed specs and materials.
- MUST report a relative Markdown link to a document that has an ID. External URLs, images, code files, documents
  without IDs and links with a fragment or query keep Markdown links.
- MUST report an ID declared by several documents (on each), and a `PROP-<slug>` beside a `SPEC-<slug>` (handoff
  deletes the proposal, so the pair is an unfinished handoff or a reused slug).
- Reference extraction follows `CAP-DOCS-document-model`: code, comments, escapes, link labels and
  `~~strikethrough~~` are not prose, so a historical mention of a removed document MAY stay in strikethrough.

### 3.4 `RULE-id-convention`

A document's ID is a slug derived from its path; dates order dated partitions and are never part of an ID, and
sequence numbers are forbidden (they collide across parallel branches).

- **Dated partitions**: ADR `docs/decisions/<YYYY-MM>/<YYYYMMDD>-<slug>.md` with `ADR-<slug>`; spec bundle
  `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/{spec,plan,tasks,reconcile}.md` with `SPEC-`, `PLAN-`, `TASKS-<slug>` and
  `reconcile_id: REC-<slug>`; feedback `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/feedback/<name>.md` (no date prefix) or
  `specs/<YYYY-MM>/feedback/<YYYYMMDD>-<name>.md`, or proposal-local
  `docs/proposals/PROP-<slug>/feedback/<name>.md` (no date prefix), with `FB-<name>`. Slugs are kebab-case, their first segment MUST
  contain a letter (a year or number there would read as a retired number-based ID), and the month partition MUST
  match the date prefix.
- **Living Spec stems** (the ID is the file stem): `docs/capabilities/<area>/CAP-<AREA>-<slug>.md` (`<AREA>`
  upper-case letters and digits, `area: <area>`); `docs/stories/<area>/US-<slug>.md` (`area: <area>`; only
  `README.md` directly under `docs/stories/`); `docs/architecture/ARCH-<slug>.md` or `ARCH-<NN>[-<n>]-<slug>.md` with
  `<NN>` an arc42 chapter (`01`-`11` except `09`, decisions, and `12`, the glossary) and `<n>` a sub-document `1`-`9`
  (`05-1` containers, `05-2` components). The first slug segment MUST contain a letter. Namespace docs roots use the
  same layout.
- MUST report: a path off the convention (nothing else is reported for that file until it moves; `README.md` files
  are not checked); no frontmatter; an `id`/`reconcile_id` or `area` other than the path requires (fixable); a first
  `# ` heading opened by a bracket or code-span ID token that is not the ID (fixable; in a spec bundle file the token
  MAY follow a leading `<label>: `, and a plan, tasks or reconcile heading MAY name `SPEC-<slug>`; an ID later in the
  heading is a reference, not the document's own, and never rewritten); in any file but a spec bundle file
  (`spec.md`, `plan.md`, `tasks.md`, `reconcile.md`; feedback, in a bundle or not, is checked), a first `# ` heading
  that does not open with an ID token but names an ID of the document's own kind (`# Capability [CAP-X-old] Title`;
  reported, not fixable: the heading should read `# [<ID>] <title>`); an ID another file's path also derives (slugs are unique per document type across partitions and
  areas, feedback slugs within their bundle; detected across the whole workspace); a date- or number-based reference
  (such as ``ADR-0006``, ``US-010``, ``CAP-HARN-007``, ``SPEC-20261006`` or an `ARCH-<NN>` without slug) in the
  frontmatter or prose of any Markdown file under `docs/` (materials excepted) or `specs/`. Code blocks, indented
  code, inline code, HTML comments and escapes are not checked; Markdown link labels and targets are.
- Fields are read from their top-level frontmatter lines as written.

### 3.5 `RULE-spec-format`

Every capability, story and proposal starts with a YAML frontmatter block that sets `id`, `title` and `status` as
non-blank strings.

- **Scope**: Markdown files under `docs/capabilities/`, `docs/stories/`, `docs/proposals/`, and `capabilities/`,
  `stories/` of each namespace docs root, except `README.md`, templates, directories starting with `.` and
  `materials/`. Unlike the index, a file is checked even when it declares no ID.
- MUST report: no block (`---` on the first line, closed by `---`); a malformed block (unclosed, invalid YAML,
  duplicate keys, not a mapping; fixed by hand); a missing, blank or non-string `id`, `title` or `status`; a
  `namespace` in `proposal.md` (under `docs/proposals/`) or `spec.md` that is not a string naming `global` or a
  registered namespace (not fixable). The `namespace` field is checked in current proposals and specs, and in every
  one of them when the run targets `.devkit/config.toml`.
- **Fix**: fills what is missing and leaves present values alone: `id` the ID the path derives, `title` the first
  `# ` heading (a leading ID token dropped) else the file stem, `status: draft` (`open` for proposal feedback), and `created_at` today when none of
  `created_at`, `created`, `date` is set. The path derives the file stem for a capability, story, single-file
  proposal or PADR, `PROP-<slug>` for a bundle's `proposal.md` and `PROP-<slug>-target` for its `target-docs.md`, and
  `FB-<name>` for its direct `feedback/<name>.md`; any other file under `docs/proposals/` derives none, and its missing `id` is reported without a fix.

### 3.6 `RULE-traceability-link`

Stories and capabilities form an M:N relation recorded on both sides by exact ID: a story's `capabilities`, a
capability's `stories` (under `docs/` and every namespace docs root; links MAY cross packages).

- MUST report a one-sided link on the document missing the reverse link; when the run does not target that document,
  on the document that declares the link instead.
- **Fix**: appends the source ID to the target's list, creating the field when absent and keeping a flow or block
  list in its style. It fixes a link only when both IDs are declared by exactly one document and the field is absent
  or a list, and only in targeted documents (`devkit rules fix <target document>` when the run targets only the
  source).
- Missing targets, duplicate IDs, wrong kinds and malformed fields are `RULE-document-reference`'s.

### 3.7 `RULE-task-coverage`

Each `specs/**/tasks.md` is checked against the `spec.md` beside it; a spec without `tasks.md`, and a completed spec
unless explicitly targeted, is not checked.

- **Criteria**: every H3 under the H2 whose title contains `Acceptance Criteria` MUST carry exactly one `[AC-NN]`
  (`AC-` and two or more digits, compared as written); IDs MUST be unique and the spec MUST define at least one.
- **Coverage**: a checklist task (`- [ ]`, `- [x]`, also `*` or `+`, nested tasks included) covers an ID written in
  its text as `[AC-NN]` or listed on a direct child line `- _Requirements: AC-01, AC-02_`. Tables, prose, blockquotes,
  frontmatter, fenced code, HTML comments, a `_Requirements:_` line that is not a direct child of a task, and an item
  indented four or more spaces that is not a task's direct child cover nothing.
- MUST report: a criterion heading without exactly one valid ID, a duplicate ID or no criteria; acceptance criteria
  without a task; tasks referencing undefined criteria; an invalid requirement ID; a missing or unreadable `spec.md`
  or unparsable spec frontmatter.
- **Targeting**: the pair is checked when either file is targeted, and each violation is reported on the file it
  belongs to; files matched by `[rules] exclude` are never reported. Not fixable.

### 3.8 `RULE-spec-lifecycle`

In a spec bundle the `status` of `spec.md`, the checklist of `tasks.md` and the `status` of `reconcile.md` MUST agree
(statuses compared trimmed and case-insensitively), because workflow stages are derived from them.

- MUST report: `spec.md` `completed` without `reconcile.md`; `spec.md` `completed` with a `reconcile.md` other than
  `resolved`; `spec.md` not `completed` while every task is checked (at least one, none open, counted as devkit's
  `tasks-checked` check counts them) and `reconcile.md` is `resolved` (stale status; a bundle without tasks is never
  stale).
- Every `spec.md` under `specs/` is checked, completed ones included. A targeted run checks a bundle when it targets
  its `spec.md`, `tasks.md` or `reconcile.md`; the violation is on `spec.md` (line 1) when that is targeted, else on
  the targeted `reconcile.md` or `tasks.md`.
- **Fix**: sets `status: completed` by rewriting only the value of the top-level `status:` line of a targeted
  `spec.md`, keeping a trailing comment (`# draft | planned | ...`; a `#` counts as one only after whitespace and
  outside a quoted value, so `status: "draft #2"` becomes `status: completed`); a `spec.md` without a `status:` line is fixed by
  hand.

### 3.9 `RULE-spec-progress`

A spec's `status` says where its work is; nothing else moves it to `in-progress`. devkit gives each rule one severity,
so this hint is a rule of its own (`SPEC-open-feedback-and-progress`).

- SHOULD report (severity `warning`): `spec.md` `draft` or `planned` (trimmed, case-insensitive) while at least one
  task of `tasks.md` is checked. A bundle in `RULE-spec-lifecycle`'s stale state (every task checked, `reconcile.md`
  `resolved`) is left to that rule, so the two fixes never disagree.
- Targeting and placement are `RULE-spec-lifecycle`'s, with `tasks.md` as the only other file.
- **Fix**: sets `status: in-progress` by rewriting only the value of the top-level `status:` line of a targeted
  `spec.md`, keeping a trailing comment.

### 3.10 `RULE-reconcile-contract`

`reconcile.md` records how a change was reconciled into the Living Spec (written by the `spec-sync` skill).

- MUST report: no or malformed frontmatter, or no `reconcile_id`; `status` other than `pending` or `resolved`;
  `targets` missing or not a list (`targets: []` when nothing is affected); a target that is not a mapping, a `file`
  that is not a unique workspace-relative path in canonical form (`docs/a.md`, not `./docs/a.md`), a `resolution` other than `modified` or `waived`, or a waiver whose
  `rationale` has fewer than 20 non-whitespace characters.
- **Diff evidence**: in a snapshot run (`--staged`, `--ci`), a `resolved` record the diff changes MUST have every
  `modified` target changed or deleted by that diff. `--ci` judges the whole branch against its merge base. A record
  whose frontmatter is unchanged from the base is not rechecked. A plain `devkit rules check` checks the form only.
- Every targeted record of a current bundle; a completed bundle's record only when explicitly targeted. Not fixable.

### 3.11 `RULE-code-entrypoints`

Every `entrypoints` item of a capability or story (`docs/` and namespace docs roots) MUST be a string, a literal
workspace-relative path, and an existing file or directory inside the workspace. In a snapshot run it also reports
every current document that declares a path the diff deletes. Not fixable. The full contract is
`CAP-TRACE-code-entrypoints`.

### 3.12 `RULE-document-summary`

`summary` is the main signal of `devkit spec search` (`CAP-DOCS-document-search`).

- MUST report: a capability, story, decision, architecture document, `proposal.md` or `spec.md` without `summary`
  (a file still carrying the skeleton marker `<!-- devkit:skeleton -->` is exempt until written); a `summary` that is
  not a non-empty string; a letter outside the Latin script in any `summary` (digits, punctuation and symbols are
  allowed); a `summary` longer than `max_length` characters.
- Setting: `max_length` (default `300`, a positive integer). Materials are exempt. Not fixable: a summary is written,
  never generated.

## 4. Interfaces & Data Contracts

### 4.1 Commands (devkit's)

| Command | Effect on the spec rules |
| --- | --- |
| `devkit rules check [FILES]...` | Runs every rule; without targets the whole workspace. `--phase linter` or `--phase hygiene` selects a phase. |
| `devkit rules check --staged` | The commit gate: evaluates the staged Git tree (snapshot run). |
| `devkit rules check --ci --base <ref>` | Evaluates `HEAD` against its merge base with `<ref>` (snapshot run; default `origin/main`). |
| `devkit rules fix [FILES]... [--dry-run]` | Applies the fixes above. |
| `devkit rules explain <RULE-id>` | Prints the rule's phase, severity, effective settings and its guide. |

Violations use devkit's `[VIOLATION: <RULE-id> severity= file= line= status= message= remediation= guide=]` sentinel, where `status` is
`open` or `fixable` and `guide` is the deployed guide path.

### 4.2 Configuration

```toml
[rules.phase_overrides]
RULE-document-summary = "hygiene"   # while a repository's documents get summaries

[rules.settings.RULE-document-summary]
max_length = 300
```

### 4.3 Packaging

Each rule is a class in `devkit_spec.rules.<name>` (`ADR-rules-implemented-in-the-package`). The bundle deploys
`rules/<name>/rule.py`, a thin subclass (devkit instantiates only classes a rule file defines), and the guide
`rules/<name>/guide.md`, to `.devkit/managed/spec/rules/<name>/`. Keeping the logic in the package means one tested
implementation and a deployed file that never changes when the rule does. A rule whose judgment lives in a bundle
instruction names it in `related` (`spec:living-spec-writing` for the reference, traceability, summary, identifier and
lifecycle rules, `spec:contract-authoring` for `RULE-task-coverage`), and `devkit rules explain` prints its deployed
path. `devkit_spec.rules` exposes `document_index(ctx)`, `namespaces(ctx)` and the targeting helpers the rules share.

A rule's tests live in its folder, `rules/<name>/tests/test_rule.py`, and deploy with it. They load the rule with
`devkit.rules.testing.load_rule(__file__)`, which loads the folder as devkit loads the deployed copy (the `rule.py`
subclass, so the deployed file and the `devkit_spec.rules.<name>` implementation are tested together), and evaluate
it with `check(RULE, tmp_path, files, ...)`; they use nothing from the repository's `tests/`. `devkit rules test
RULE-<id>` runs the deployed copy's tests in an isolated pytest run (no project configuration or `conftest.py`), and
without IDs every rule's tests. The repository's own `pytest` collects the same files under
`src/devkit_spec/bundle/rules/`.

### 4.4 Error Codes

| Code | Level | Condition |
| --- | --- | --- |
| `RULES_EXECUTION_FAILED` | `ERROR` (devkit's) | A rule raised an exception that is not an advisory; exit `2`. An advisory a rule raises keeps its own code: a malformed `[tool.spec]` table is `SPEC_CONFIG_INVALID` with the rule's ID. |
