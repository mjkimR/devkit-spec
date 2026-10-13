---
id: CAP-DLV-proposal-incubation
title: Proposal Incubation and Handoff
summary: The proposal lifecycle under docs/proposals/PROP-<slug>/ (devkit spec proposal new, padr, handoff, prune), from scaffolding and preliminary decisions to the approved handoff that creates a spec bundle, promotes PADRs to ADRs, moves materials and rewrites links and ID references.
area: delivery
status: active
created_at: 2026-10-13
stories:
  - US-incubate-and-hand-off-a-proposal
entrypoints:
  - src/devkit_spec/proposals/
  - src/devkit_spec/cli/proposals.py
---

# [CAP-DLV-proposal-incubation] Proposal Incubation and Handoff

## 1. Summary

A proposal incubates an idea (a feature, a technical spike, an architectural change) before it becomes a feature
spec: Routes 3 and 4 shape it in a proposal bundle bound to workflow `incubated-delivery`. `devkit_spec.proposals`
implements the lifecycle and `devkit spec proposal new|padr|handoff|prune` exposes it. The handoff is a cross-layout
move devkit's own `devkit workflow handoff` cannot make: it creates the spec bundle (`CAP-DLV-spec-bundles`), carries
the proposal body, promotes preliminary decisions, moves materials, rewrites what pointed into the proposal and
removes it.

## 2. Scope & Boundary

- **In-Scope**: the proposal bundle layout and frontmatter, slug rules, `new`, `padr`, the approval rule, `handoff`
  (validation, writes, body carrying, link and ID rewriting, roll-back) and `prune`.
- **Out-of-Scope**:
  - The stages and gates of `incubated-delivery` and of the workflow the spec follows: `CAP-DLV-delivery-workflows`.
  - The spec bundle skeleton and binding rules shared with `devkit spec new`: `CAP-DLV-spec-bundles`.
  - Registering the new bundle's work scope: `CAP-COLL-work-scope-registry`.
  - Format and reference rules over proposal files: `CAP-GOV-spec-rules`.
- **Non-Goals**:
  - **Scope Excluded**: inferring approval. Handoff never derives the user's choice from context.
  - **Scope Excluded**: moving into a worktree. Handoff runs in the workspace it is given; task worktrees are
    devkit's `devkit worktree`.
  - **Scope Excluded**: archives. Rejected and handed-off proposals are deleted; Git history keeps them.

## 3. Business Rules & Policies

1. **A proposal and a spec never share a slug**: a handed-off `PROP-<slug>` maps to exactly one `SPEC-<slug>`.
   `new` and `handoff` MUST refuse a slug whose `SPEC-<slug>` exists (`SPEC_PROPOSAL_SLUG_CONFLICT`); a document that
   cannot be indexed never blocks them.
2. **Approval is explicit**: handoff MUST require `status: accepted`, or `draft`/`reviewing` with
   `--direction-chosen`, which the agent passes only when the user explicitly chose the proposal's direction.
   Anything else is `SPEC_PROPOSAL_NOT_APPROVED` (`INTERACTION`: stop and ask the user).
3. **The follow-up workflow is `handoff_workflow`**: `workflow` and `workflow_hash` in `proposal.md` are devkit's
   binding of the proposal unit itself; the workflow the spec follows after handoff is `handoff_workflow` (a
   workflow id without prefix, e.g. `bugfix`; default `direct-delivery`). Rationale: `ADR-handoff-workflow-key`.
4. **Validate everything before writing**: handoff checks the slug, the proposal file and its frontmatter, the
   approval, `namespace` (`global` or registered, else `SPEC_PROPOSAL_INVALID`), `summary` (a string, else
   `SPEC_PROPOSAL_INVALID`), the slug conflict, the workflow binding and every path it would create before its first
   write. A path that already exists, two PADRs that would become the same ADR, or an ADR ID another document already
   declares is `SPEC_PROPOSAL_TARGET_EXISTS`.
5. **Roll back a failed write**: a file system error while writing the spec bundle, the blueprint, the ADRs or moving
   the materials removes what was written, moves the materials back and keeps the proposal
   (`SPEC_PROPOSAL_HANDOFF_FAILED`).
6. **Promoted decisions are accepted**: a PADR promoted to an ADR is accepted by definition.
7. **Rewriting never fails a handoff**: what cannot be mapped stays as it was and is reported
   (`SPEC_PROPOSAL_LINK_UNRESOLVED`); rewritten ID references are reported for rereading
   (`SPEC_PROPOSAL_REFS_REWRITTEN`), because whether a sentence named the proposal as its origin or as the work to do
   cannot be decided mechanically.
8. **Removal last**: the proposal is removed after every write and rewrite; if it cannot be removed the handoff still
   succeeded and `SPEC_PROPOSAL_CLEANUP_FAILED` names what to delete. Other files in the bundle (outside
   `proposal.md`, `target-docs.md`, `PADR-*.md` and `materials/`) are removed with it.
9. **Rejection**: a rejected proposal (`status: rejected`) is retired by recording a brief rejection ADR in
   `docs/decisions/` and deleting the bundle directory; no `archive/` directory is kept.
10. **Discovery is dynamic**: active proposals are listed with `devkit spec list proposal`, never through catalog
    tables maintained in README files.

## 4. Interfaces & Data Contracts

### 4.1 Bundle Layout

```text
docs/proposals/PROP-<slug>/
├── proposal.md       # required: background, hypothesis, spike questions, design; the workflow anchor
├── target-docs.md    # optional (--with-target-docs): blueprint of the Living Spec changes once accepted
├── decisions/        # preliminary decision records, PADR-<slug>.md
└── materials/        # research, benchmarks, surveys
```

A single-file proposal `docs/proposals/PROP-<slug>.md` can be handed off too; it has no PADRs, materials or
blueprint, and its body is not carried (the spec gets the plain skeleton). `target-docs.md` is recommended for
`size: M`, `L` or `XL` or when Living Spec structural changes are expected: `proposal.md` says why, `target-docs.md`
what `docs/` will look like.

Markdown under `materials/` needs frontmatter `id`, `title` and `status` while it is inside the bundle
(`RULE-spec-format`); follow the material convention (file `<YYYYMMDD>-<slug>.md`, `id: MAT-<slug>`, `created_at`, H1
`# [MAT-<slug>] <title>`). Non-Markdown files need no metadata. After handoff the files live under `docs/materials/`,
where frontmatter is optional.

### 4.2 Slugs

A slug is normalized: a leading `PROP-` and a trailing `.md` are dropped, every run of characters other than letters,
digits, `_` and `-` becomes `-`, outer dashes are trimmed, and the result is lower-cased (`"PROP-Fast Engine"` is
`fast-engine`). A slug, or a PADR title, with no letter or digit left is `SPEC_PROPOSAL_SLUG_INVALID`.

### 4.3 `proposal.md` Frontmatter

| Key | Meaning |
| --- | --- |
| `id` | `PROP-<slug>`. |
| `title` | `--title` (default: the slug). |
| `summary` | One or two English sentences (`--summary`); carried to `spec.md`. Without the option, `new` writes the commented placeholder `# summary: <one or two English sentences: what this proposal changes and why>`, which the agent replaces with the field before committing. |
| `status` | `draft` (scaffolded), `reviewing`, `accepted`, `rejected`. |
| `created_at` | Scaffold date. |
| `target_area` | `--target-area` (default `capabilities/<area>/`, a trailing `/` added): the capability area on graduation. |
| `namespace` | Optional (`--namespace`): `global` or a registered namespace (`CAP-DOCS-namespaces`); carried to `spec.md`. Every file of the bundle belongs to it. |
| `priority` | `critical`, `high` (scaffolded), `medium`, `low`. |
| `size` | `S` (single fix), `M` (scaffolded; 1-2 sessions), `L` (complex module), `XL` (major overhaul). |
| `milestone` | Optional (`--milestone`): milestone, phase or release; carried to `spec.md`. |
| `boundaries` | `owns` (scaffolded: the target area) and `excludes` (scaffolded: `docs/decisions/`); carried to `plan.md` and `tasks.md`. |
| `handoff_workflow` | Optional (`--handoff-workflow`): the workflow the spec follows; without it a commented `# handoff_workflow: bugfix` line is scaffolded. |
| `workflow`, `workflow_hash` | devkit's binding of the proposal unit (`incubated-delivery`). |

The scaffolded body has sections `1. Background & Hypothesis`, `2. Technical Spike Questions`,
`3. Proposed Design & Impact` and `4. Lifecycle & Retirement Criteria`.

### 4.4 PADRs and the Blueprint

- `padr <slug> <title> [--summary TEXT]` writes `decisions/PADR-<title slug>.md` with `id`, `title`, `summary` (or
  the commented placeholder `# summary: <one or two English sentences: what is decided and why>`), `proposal:
  PROP-<slug>`, `status: draft`, `created_at`, and a body shaped like the decision template (`- **Status**: Draft`,
  `- **Date**`, then Context & Problem Statement, Decision Drivers, Considered Options, Decision Outcome,
  Consequences). PADR IDs are unique across the repository (`SPEC_PROPOSAL_EXISTS`).
- `target-docs.md` declares `id: PROP-<slug>-target`, `proposal: PROP-<slug>`, `status: draft`, `created_at` and
  `targets: []` (one `- file: <workspace-relative path>` per Living Spec file the proposal changes; read by
  `devkit spec scope compare`). Its body covers the capability ledger, stories, architecture and decisions,
  conventions and governance, and a before/after comparison.

### 4.5 Handoff Steps

With `<YYYY-MM>` and `<YYYYMMDD>` today's date:

1. **Spec bundle** `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` with the skeletons of `CAP-DLV-spec-bundles`: `spec.md`
   (`SPEC-<slug>`, the proposal's `summary`, `status: planned`, `created`, the proposal's `namespace` and
   `milestone`; the problem statement starts with `Handed off from proposal PROP-<slug> on <date>.` and the
   preserved materials and blueprint references, then the carried body), `plan.md` (target area, blueprint
   reference, planned and excluded boundaries) and `tasks.md` (one task whose boundary is `boundaries.owns`, else
   `target_area`, and whose `_Requirements:` lists every acceptance criterion ID).
2. **Workflow binding** of `spec.md` to `handoff_workflow`. A named workflow MUST resolve and validate, or the
   handoff fails before writing (`SPEC_PROPOSAL_WORKFLOW_INVALID`). Without one, `direct-delivery` is bound when the
   project has it; otherwise `spec.md` stays unbound with a `SPEC_PROPOSAL_UNBOUND` notice. A `bugfix` spec carries
   `kind: bugfix` and gets `spec.md` only; the target area and boundaries go into a `### Target Area & Boundaries`
   section of its carried notes.
3. **Blueprint**: `target-docs.md` is copied into the spec bundle as written; step 6 then rewrites its `proposal`
   provenance and its links like those of any other file.
4. **PADR promotion**: each `decisions/PADR-<slug>.md` becomes `docs/decisions/<YYYY-MM>/<YYYYMMDD>-<slug>.md`. Every
   `PADR-<slug>` in it becomes `ADR-<slug>`, a frontmatter `status: draft` (or `proposed`) becomes
   `status: accepted`, and a body line `- **Status**: Draft` (or `Proposed`) becomes `- **Status**: Accepted`. The
   rest of the frontmatter, `summary` included, is kept. Other files under `decisions/` are not promoted.
5. **Materials**: a non-empty `materials/` moves to `docs/materials/<YYYY-MM>/<YYYYMMDD>-<slug>/`.
6. **Rewriting** of what pointed into the proposal (4.7).
7. **Removal** of the proposal.

The new spec's workflow is then evaluated from its first stage; its G1 is the spec bundle's intent, normally
confirmed by the accepted proposal. Inside a linked worktree with `[tool.spec] worktree = true`, the CLI also
registers the new bundle in the work-scope registry (`CAP-COLL-work-scope-registry`); a registration failure is a
`SPEC_SCOPE_REGISTER_FAILED` warning and the handoff stays done.

### 4.6 Carrying the Proposal Body

The body of a bundle's `proposal.md` after the frontmatter and the first H1 is split into H2 sections (fenced code is
never a heading), each classified by its heading, case-insensitively:

| Heading contains | Lands in | How |
| --- | --- | --- |
| (text before the first H2), `background`, `hypothesis`, `problem`, `motivation`, `origin` | 1. Problem Statement & Motivation | heading kept as H3, inner headings demoted one level |
| `non-goal`, `non goal`, `scope excluded`, `out of scope` | 3. Non-Goals | body only; a placeholder item when none |
| `acceptance` | 4. Acceptance Criteria & Behavioral Contracts | body only, with acceptance criterion IDs |
| anything else | 5. Carried Proposal Notes | heading kept as H3, inner headings demoted; not contracts |

Bodies are verbatim apart from heading levels; leading and trailing blank lines and trailing horizontal rules are
trimmed. Acceptance criteria get IDs so the spec satisfies `RULE-task-coverage`: an H3 with exactly one `[AC-NN]`
keeps it; another H3 becomes `### Scenario <n> [AC-NN]: <text>`; a body without H3 gets a
`### Scenario <n> [AC-NN]: Carried from proposal` heading before each top-level list item (or one before everything
when it has no list); an empty section gives one placeholder `### [AC-01] <scenario>` with Given/When/Then lines. New
IDs are numbered `AC-<count + 1>` in order.

### 4.7 Rewriting Links and References

Every Markdown file under `docs/` and `specs/` is scanned, except the proposal itself, directories starting with `.`,
symbolic links and the files of completed spec bundles (`spec.md` with `status: completed`), which record the
proposal as it was; their `feedback/` is scanned, since feedback stays current.

- **Relative Markdown links** (inline links and images outside code, devkit's `extract_links`) that resolve into the
  proposal are pointed at the new locations: `proposal.md` (or the single file) to `spec.md`, `target-docs.md` to its
  copy, each PADR to its ADR, anything under `materials/` to the same path under the moved directory (whether or not
  the file exists), and the bundle directory to the spec bundle. URLs, root-relative and fragment-only links are left
  alone; a `#fragment` or `?query` is kept. Files written for the bundle's location (the carried `spec.md`, the
  copied blueprint, the moved materials) have their links resolved from where they were written, so a link outside
  the bundle keeps its target and one that still resolves to the same file keeps its spelling.
- **Document ID references** (frontmatter reference fields, `` `ID` `` and `[ID]` in prose, and the `proposal`
  provenance field) are rewritten from the IDs of the documents actually written: `PROP-<slug>` to `SPEC-<slug>`,
  each `PADR-<slug>` to its `ADR-<slug>`, and `PROP-<slug>-target` to itself (a `[ID]` becomes `` `ID` ``). Bare
  text, inline code other than a lone ID and fenced code do not change.

| Unresolved reason | Meaning |
| --- | --- |
| `unmapped` | A link into the proposal with no new location (`decisions/`, a file that was not promoted). |
| `removed` | A reference to an ID declared inside the proposal that nothing replaced (a non-`PADR-*` file under `decisions/`). |
| `ambiguous` | Another document declares the same ID, so it is not rewritten. |
| `unreadable`, `unwritable` | The file could not be read, parsed or written (line `0`). |

The `spec-next` skill's post-handoff check follows up the reported lines.

### 4.8 Prune

A handoff deletes the proposal in the worktree it runs in; merging that branch removes the tracked files from the
base checkout but leaves their directories. `devkit spec proposal prune [<slug>]` removes `docs/proposals/PROP-<slug>/` (every `PROP-*` directory without a slug) when it
holds no file at any depth (a symbolic link counts as a file). A directory holding any file is kept. devkit-spec's
`devkit.post_finish` extension prunes the finished slug after a successful `devkit worktree finish`
(`ADR-cleanup-after-worktree-finish`); the command remains for other checkouts and a failed extension.

### 4.9 Commands and Options

Every command takes `-w/--workspace-root`, `--format text|json`, `-q`, `-v` and `--strict` (`CAP-HARN-command-mount`).

```bash
uv run devkit spec proposal new fast-engine --title "Fast Engine" --target-area capabilities/governance/
uv run devkit spec proposal new fast-engine --milestone "Phase 1" --with-target-docs
uv run devkit spec proposal new rate-limits --namespace api --handoff-workflow bugfix
uv run devkit spec proposal new fast-engine --summary "Replaces the regex rule engine with an AST parser."
uv run devkit spec proposal padr fast-engine "Use AST parser"        # decisions/PADR-use-ast-parser.md
uv run devkit spec proposal handoff fast-engine                      # status: accepted
uv run devkit spec proposal handoff fast-engine --direction-chosen   # draft/reviewing; the user chose the direction
uv run devkit spec proposal prune [<slug>]                           # base checkout; finish's extension does it per slug
```

| Option | Command | Meaning |
| --- | --- | --- |
| `--title/-t` | `new` | Title (default: the slug). |
| `--target-area/-a` | `new` | Capability area the proposal targets (default `capabilities/<area>/`); also the owned boundary. |
| `--milestone/-m` | `new` | Milestone, phase or release; carried to `spec.md`. |
| `--handoff-workflow` | `new` | Write `handoff_workflow: <id>` (default at handoff: `direct-delivery`). |
| `--namespace` | `new` | Write `namespace: <name>`: `global` or registered in `[[tool.spec.namespaces]]`, else `ARGUMENT_INVALID` with the valid names in `[FIX]`. Omitted: no field, the bundle is global. |
| `--summary` | `new`, `padr` | Write `summary: <text>`. Empty, or with a letter outside the Latin script: `ARGUMENT_INVALID` (`[TARGET] --summary`), nothing written. A promoted ADR keeps its PADR's summary. |
| `--with-target-docs` | `new` | Also write `target-docs.md`. |
| `--direction-chosen` | `handoff` | Hand off a `draft` or `reviewing` proposal whose direction the user chose explicitly. |

### 4.10 Output

```text
[PROPOSAL: PROP-fast-engine path=docs/proposals/PROP-fast-engine/proposal.md dir=docs/proposals/PROP-fast-engine target_docs=- workflow=incubated-delivery]
[NEXT_CMD: devkit workflow next --unit docs/proposals/PROP-fast-engine]
[PADR: PADR-use-ast-parser path=docs/proposals/PROP-fast-engine/decisions/PADR-use-ast-parser.md proposal=PROP-fast-engine]
[HANDOFF: PROP-fast-engine spec=SPEC-fast-engine dir=specs/2026-10/20261013-fast-engine workflow=direct-delivery]
[TARGET_DOCS: specs/2026-10/20261013-fast-engine/target-docs.md]
[MATERIALS: docs/materials/2026-10/20261013-fast-engine]
[PROMOTED_ADR: ADR-use-ast-parser path=docs/decisions/2026-10/20261013-use-ast-parser.md padr=PADR-use-ast-parser]
[REWRITTEN: docs/stories/core/US-x.md:5 kind=id from=PROP-fast-engine to=SPEC-fast-engine]
[REWRITTEN: docs/stories/core/US-x.md:9 kind=link from=../../proposals/PROP-fast-engine/proposal.md to=../../../specs/2026-10/20261013-fast-engine/spec.md]
[UNRESOLVED_LINK: docs/stories/core/US-x.md:9 kind=link target=../../proposals/PROP-fast-engine/decisions/ reason=unmapped]
[SCOPE: SPEC-fast-engine namespace=3f2a... revision=1 scopes=6 unresolved=2 shared_path=/repo/.git/devkit-spec-scope token=...]
[NEXT_CMD: devkit workflow next --unit specs/2026-10/20261013-fast-engine]
[PRUNED: docs/proposals/PROP-fast-engine]
[OK: nothing to prune]
```

- `new`: one `[PROPOSAL: ...]` line (`target_docs=-` without `--with-target-docs`, `workflow=-` when unbound), then
  `[NEXT_CMD: ...]` when `proposal.md` is bound to `incubated-delivery`. JSON: `id`, `dir`, `path`, `target_docs`,
  `workflow`, `next_command`, `notices`.
- `padr`: one `[PADR: ...]` line. JSON: `id`, `path`, `proposal`.
- `handoff`: `[HANDOFF: ...]` (`workflow=-`: unbound), `[TARGET_DOCS: ...]` and `[MATERIALS: ...]` when the bundle had
  them, one `[PROMOTED_ADR: ...]` per PADR, one `[REWRITTEN: <path>:<line> kind=link|id from= to=]` per rewrite, one
  `[UNRESOLVED_LINK: <path>:<line> kind= target= reason=]` per link or reference left as it was, `[SCOPE: ...]` when
  it registered the bundle, and `[NEXT_CMD: ...]` when `spec.md` is bound. JSON: `proposal`, `spec`, `dir`,
  `workflow`, `target_docs`, `materials`, `decisions` (`id`, `path`, `padr`), `rewritten_files`, `rewritten`
  (`path`, `line`, `kind`, `from`, `to`), `unresolved` (`path`, `line`, `kind`, `target`, `reason`), `next_command`,
  `notices`, `scope` (`record`, `token`, `namespace`, `shared_path`, or `null`).
- `prune`: `[PRUNED: <dir>]` per directory removed, else `[OK: nothing to prune]`. JSON: `{"pruned": [...]}`.

### 4.11 Library

```python
from devkit_spec.proposals import create_padr, create_proposal, handoff_proposal, prune_proposals

created = create_proposal(root, "fast-engine", title="Fast Engine", with_target_docs=True)  # CreatedProposal
create_padr(root, "fast-engine", "Use AST parser", summary="Parses rules with an AST.")  # CreatedDecision
result = handoff_proposal(root, "fast-engine", direction_chosen=False)  # HandoffResult
result.dir, result.workflow, result.decisions, result.rewritten, result.unresolved, result.notices
prune_proposals(root, "fast-engine")  # list of removed dirs
```

`create_proposal` also takes `target_area`, `milestone`, `handoff_workflow`, `namespace` and `summary`;
`carry_proposal_body` and `ensure_ac_ids` implement 4.6, `RelocationPlan`, `Rewritten` and `Unresolved` 4.7.

### 4.12 Codes

`0` success; `2` refused or failed (nothing was handed off). Warnings exit `0` (`1` under `--strict`).

| Code | Level | Class | Condition |
| --- | --- | --- | --- |
| `SPEC_PROPOSAL_SLUG_INVALID` | `ERROR` (`INPUT_ERROR`) | `ProposalSlugError` | The slug, or a PADR title, keeps no letter or digit after normalization. |
| `SPEC_PROPOSAL_EXISTS` | `ERROR` (`INPUT_ERROR`) | `ProposalExistsError` | `new`: the bundle or `PROP-<slug>.md` exists. `padr`: a document already declares the PADR ID; `[TARGET]` lists it. |
| `SPEC_PROPOSAL_SLUG_CONFLICT` | `ERROR` (`INTERACTION`) | `ProposalSlugConflictError` | `SPEC-<slug>` exists (`[TARGET]`); the user picks another slug or drops the duplicate. |
| `SPEC_PROPOSAL_NOT_FOUND` | `ERROR` (`INPUT_ERROR`) | `ProposalNotFoundError` | No bundle or single-file proposal has the slug (`padr`: no bundle). |
| `SPEC_PROPOSAL_INVALID` | `ERROR` (`MAINTENANCE`) | `ProposalInvalidError` | The proposal, its blueprint or a PADR cannot be read or its frontmatter does not parse; or, at handoff, `namespace` is not a string naming `global` or a registered namespace, or `summary` is not a string. |
| `SPEC_PROPOSAL_NOT_APPROVED` | `ERROR` (`INTERACTION`) | `ProposalNotApprovedError` | Status is not `accepted` (or `draft`/`reviewing` with `--direction-chosen`). |
| `SPEC_PROPOSAL_WORKFLOW_INVALID` | `ERROR` (`MAINTENANCE`) | `ProposalWorkflowError` | `handoff_workflow` is not a string, or names a definition that does not resolve or validate; `[DETAIL]` carries devkit's code. |
| `SPEC_PROPOSAL_TARGET_EXISTS` | `ERROR` (`BLOCKED`) | `ProposalTargetExistsError` | The spec bundle, an ADR file or the materials directory exists, two PADRs map to one ADR, or another document declares a promoted ADR's ID. |
| `SPEC_PROPOSAL_HANDOFF_FAILED` | `ERROR` (`MAINTENANCE`) | `ProposalHandoffError` | A write failed; what was written is removed, the materials moved back, the proposal kept. |
| `SPEC_PROPOSAL_CLEANUP_FAILED` | `WARNING` | `ProposalCleanupWarning` | The handoff completed but the proposal could not be removed. |
| `SPEC_PROPOSAL_LINK_UNRESOLVED` | `WARNING` | `ProposalLinkUnresolvedWarning` | Links or references into the proposal were left as they were; the `[UNRESOLVED_LINK]` lines list them. |
| `SPEC_PROPOSAL_REFS_REWRITTEN` | `NOTICE` | `ProposalReferencesRewrittenNotice` | ID references now name the spec or the ADRs; reread each `[REWRITTEN ... kind=id]` sentence. |
| `SPEC_PROPOSAL_UNBOUND` | `NOTICE` | `ProposalUnboundNotice` | `new`: `incubated-delivery` is not available, `proposal.md` is unbound. `handoff`: no `handoff_workflow` and `direct-delivery` is not available, `spec.md` is unbound. The `[FIX]` is `devkit workflow bind --unit <dir> --workflow <id>`. |
| `ARGUMENT_INVALID` | `ERROR` (`INPUT_ERROR`) | devkit's `ArgumentError` | `new`: `--namespace` is neither `global` nor registered. `new`, `padr`: `--summary` is empty or not English. |
| `SPEC_CONFIG_INVALID` | `ERROR` (`INPUT_ERROR`) | `SpecConfigError` | A namespace other than `global` must be validated (`--namespace`, or a proposal's `namespace` at handoff) and `[tool.spec]` is malformed. |
| `SPEC_SCOPE_REGISTER_FAILED` | `WARNING` | `ScopeRegisterFailedWarning` | A handoff in a task worktree could not register its bundle (`CAP-COLL-work-scope-registry`). |
