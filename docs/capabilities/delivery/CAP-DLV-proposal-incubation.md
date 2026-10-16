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
spec: `proposal`-depth work, whose direction must be decided first, shapes it in a proposal bundle bound to workflow
`sdd-proposal`. `devkit_spec.proposals`
implements the lifecycle and `devkit spec proposal new|padr|handoff|prune` exposes it. The handoff is a cross-layout
move devkit's own `devkit workflow handoff` cannot make: it creates the spec bundle (`CAP-DLV-spec-bundles`), carries
the proposal body, promotes preliminary decisions, moves materials, rewrites what pointed into the proposal and
removes it.

## 2. Scope & Boundary

- **In-Scope**: the proposal bundle layout and frontmatter, slug rules, `new`, `padr`, the approval rule, `handoff`
  (validation, writes, body carrying, link and ID rewriting, roll-back) and `prune`.
- **Out-of-Scope**:
  - The stages and gates of `sdd-proposal` and of the workflow the spec follows: `CAP-DLV-delivery-workflows`.
  - Planning's question rounds, acceptance and rejection procedure and the Backlog decomposition: the `spec` skills
    (`CAP-HARN-agent-guidance`).
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
2. **Approval is explicit**: handoff MUST require `status: accepted`, which is written once the user gave
   `plan-accept`. Anything else is `SPEC_PROPOSAL_NOT_APPROVED` (`INTERACTION`: stop and ask the user). A proposal
   marked `needs_decompose: true` is split in Backlog, never handed off (`SPEC_PROPOSAL_NEEDS_DECOMPOSE`), and one
   proposal hands off to exactly one spec.
3. **The follow-up workflow comes from `task_kind`**: `workflow` and `workflow_hash` in `proposal.md` are devkit's
   binding of the proposal unit itself; `task_kind` (`feature` or `bugfix`, confirmed at `plan-accept`) is the only
   axis value stored as a field, because the proposal is not yet bound to its spec workflow. The spec follows
   `sdd-spec-<task_kind>`; any other value is `SPEC_PROPOSAL_INVALID`. After handoff the bound workflow carries the
   `task-kind` and `spec.md` has no `kind` field (`ADR-task-kind-and-planning-depth`).
4. **Validate everything before writing**: handoff checks the slug, the proposal file and its frontmatter, the
   approval, `namespace` (`global` or registered, else `SPEC_PROPOSAL_INVALID`), `summary` (a string, else
   `SPEC_PROPOSAL_INVALID`), the slug conflict, the workflow binding and every path it would create before its first
   write. A path that already exists, two PADRs that would become the same ADR, an ADR ID another document already
   declares, a carried bundle file whose path under the materials directory a file or symbolic link of `materials/`
   takes too (or lies below; a `materials/` that is itself a symbolic link takes every such path), or a path it would
   create (the spec bundle, an ADR, the materials directory, a carried file) whose directory resolves outside the
   workspace is `SPEC_PROPOSAL_TARGET_EXISTS`; a legacy proposal or PADR slug whose first segment has no letter is
   `SPEC_PROPOSAL_SLUG_INVALID`.
5. **Roll back a failed write**: any failure while writing the spec bundle, the blueprint, the ADRs or moving the
   materials and carried files removes what was written, moves them back and keeps the proposal, so the handoff can
   be rerun. The roll-back MUST NOT remove a directory that still holds something it could not move back. An advisory
   error (such as `FRONTMATTER_INVALID` binding `spec.md`) is reported with its own code after a complete roll-back,
   any other failure, and any incomplete roll-back, as `SPEC_PROPOSAL_HANDOFF_FAILED`. Across file systems the materials and carried files are copied
   and their sources removed only after every write succeeded, so a partial copy is removed like any other written
   file.
6. **Promoted decisions are accepted**: a PADR promoted to an ADR is accepted by definition.
7. **Rewriting never fails a handoff**: what cannot be mapped stays as it was and is reported
   (`SPEC_PROPOSAL_LINK_UNRESOLVED`); rewritten ID references are reported for rereading
   (`SPEC_PROPOSAL_REFS_REWRITTEN`), because whether a sentence named the proposal as its origin or as the work to do
   cannot be decided mechanically.
8. **Removal last**: the proposal is removed after every write and rewrite; if it cannot be removed the handoff still
   succeeded and `SPEC_PROPOSAL_CLEANUP_FAILED` names what to delete. Nothing else in the bundle is lost with it:
   files outside `proposal.md`, `target-docs.md`, the promoted `PADR-*.md` and `materials/` are carried to the
   materials directory first (4.5, step 5), operating-system junk and the unit's workflow records (rule 12) aside.
9. **Rejection changes the status only**: the party that received the user's rejection sets `status: rejected`
   with the user's reason in the commit message (kept through a squash) and merges the Planning branch; no worker
   runs. A later hygiene pass writes a rejection ADR outside the proposal directory, referencing the proposal and the
   rejection commit, and deletes the proposal in the same commit; no `archive/` directory is kept. A `rejected`
   proposal is never resumed, accepted or handed off.
10. **Discovery is dynamic**: active proposals are listed with `devkit spec list proposal`, never through catalog
    tables maintained in README files.
11. **Hand off in the slug's own worktree**: at either `[tool.spec] worktree` level, a handoff in a linked worktree
    whose branch is not the slug (a detached HEAD included) MUST be refused before anything is read or written
    (`SPEC_PROPOSAL_WRONG_WORKTREE`), so the spec bundle never lands on another task's branch. The base checkout and
    a workspace outside Git are not checked.
12. **Workflow records stay behind; the approvals carry by name**: the proposal unit's devkit workflow records
    (decision records and envelopes as devkit's `load_decisions` and `load_envelopes` find them, malformed ones
    included) MUST NOT be carried; they are dropped with the proposal (Git history keeps them) and listed. The
    proposal's own approvals are carried under their own names, never re-labelled as another decision: for each of
    `gate:plan-intent` and `gate:plan-accept` whose effective record in the proposal's bound workflow (its latest
    that is not a `cancel`, followed by no return record that is not a `cancel`: stricter than devkit's voiding) is
    `accept`, the handoff records the same request in the bound spec with the record's `by` and note `PROP-<slug>`.
    `gate:plan-intent`, open at the spec's `intent` stage, is answered through devkit's `record_answer`;
    `gate:plan-accept`, which no spec workflow asks, is written as a decision record of the spec's workflow with the
    proposal's stage, kept for the audit trail and satisfying no stage. A gate of the spec answered by policy is
    skipped; an unbound spec records nothing. Carrying an existing answer is not inferring one (rule 2). A recording
    failure is a `SPEC_PROPOSAL_GATE_NOT_CARRIED` warning; the gates recorded before it stay and the handoff stays
    done.

## 4. Interfaces & Data Contracts

### 4.1 Bundle Layout

```text
docs/proposals/PROP-<slug>/
├── proposal.md       # required: background, hypothesis, spike questions, design; the workflow anchor
├── target-docs.md    # optional (--with-target-docs): blueprint of the Living Spec changes once accepted
├── decisions/        # preliminary decision records, PADR-<slug>.md; devkit's gate records <NN>-<request>.yaml
├── envelopes/        # devkit envelopes of the proposal unit (a delegated spike), when any
└── materials/        # research, benchmarks, surveys
```

A single-file proposal `docs/proposals/PROP-<slug>.md` can be handed off too; it has no PADRs, materials or
blueprint, and its body is not carried (the spec gets the plain skeleton). `target-docs.md` is recommended for
`size: M`, `L` or `XL` or when Living Spec structural changes are expected: `proposal.md` says why, `target-docs.md`
what `docs/` will look like.

Markdown under `materials/` follows the material convention (file `<YYYYMMDD>-<slug>.md`, `id: MAT-<slug>`,
`created_at`, H1 `# [MAT-<slug>] <title>`); `RULE-spec-format` skips `materials/` directories, so the frontmatter is
recommended, not checked. Non-Markdown files need no metadata. After handoff the files live under `docs/materials/`.

### 4.2 Slugs

A slug is normalized: a leading `PROP-` and a trailing `.md` are dropped, every run of characters other than letters,
digits, `_` and `-` becomes `-`, outer dashes are trimmed, and the result is lower-cased (`"PROP-Fast Engine"` is
`fast-engine`). A slug, or a PADR title, with no letter or digit left is `SPEC_PROPOSAL_SLUG_INVALID`. The slug of a
new proposal or PADR also needs a letter in its first `-` segment (`2024-budget` reads as the retired number-based ID
`2024`; `RULE-id-convention`): `new` and `padr` refuse one with `SPEC_PROPOSAL_SLUG_INVALID`, and `handoff` refuses a
legacy proposal or PADR whose slug starts that way, before writing anything, with a `[FIX]` to rename it.

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
| `task_kind` | `feature` (scaffolded default) or `bugfix` (`--task-kind`): the provisional `task-kind`, confirmed at `plan-accept`; the spec follows `sdd-spec-<task_kind>`. |
| `supersedes` | Optional (`--supersedes PROP-<old>`): the accepted proposal a close by supersede replaces. |
| `needs_decompose` | Optional (`--needs-decompose`): `true` marks a draft Backlog splits before Planning starts. |
| `workflow`, `workflow_hash` | devkit's binding of the proposal unit (`sdd-proposal`). |

The scaffolded body has sections `1. Background & Hypothesis`, `2. Technical Spike Questions`,
`3. Proposed Design & Impact` and `4. Lifecycle & Retirement Criteria`.

### 4.4 PADRs and the Blueprint

- `padr <slug> <title> [--summary TEXT] [--slug SLUG]` writes `decisions/PADR-<padr slug>.md`, where the PADR slug is
  `--slug` (a leading `PADR-` dropped, normalized as in 4.2) or else the title's slug; the title stays free text, so
  `padr plans "2024 roadmap" --slug roadmap-2024` works where the title alone is refused. The file has `id`, `title`, `summary` (or
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
2. **Workflow binding** of `spec.md` to `sdd-spec-<task_kind>`. For `task_kind: bugfix` the workflow MUST resolve
   and validate, or the handoff fails before writing (`SPEC_PROPOSAL_WORKFLOW_INVALID`, the devkit code in its
   details). For `feature` (or no field), `sdd-spec-feature` is bound when the project has it; otherwise `spec.md`
   stays unbound with a `SPEC_PROPOSAL_UNBOUND` notice. An `sdd-spec-bugfix` spec gets `spec.md` only; the target
   area and boundaries go into a `### Target Area & Boundaries` section of its carried notes.
3. **Blueprint**: `target-docs.md` is copied into the spec bundle as written; step 6 then rewrites its `proposal`
   provenance and its links like those of any other file.
4. **PADR promotion**: each `decisions/PADR-<slug>.md` becomes `docs/decisions/<YYYY-MM>/<YYYYMMDD>-<slug>.md`. Every
   `PADR-<slug>` in it becomes `ADR-<slug>`, a frontmatter `status: draft` (or `proposed`) becomes
   `status: accepted`, and a body line `- **Status**: Draft` (or `Proposed`) becomes `- **Status**: Accepted`. The
   rest of the frontmatter, `summary` included, is kept. Only the IDs of the PADRs this handoff promotes change, and
   never inside a file name (`PADR-<slug>.md` in a link is left to step 6). Other files under `decisions/` are not
   promoted.
5. **Materials**: `materials/` moves to `docs/materials/<YYYY-MM>/<YYYYMMDD>-<slug>/` when it holds a file other
   than operating-system junk (`.DS_Store`, `Thumbs.db`, `desktop.ini`) or a symbolic link. Every other bundle file the
   steps above do not carry (a `notes.md` beside `proposal.md`, an image, a non-PADR file under `decisions/`, a
   hidden file other than junk) moves into the same directory, except the unit's workflow records (rule 12), at its path relative to the bundle, which is created
   for them when `materials/` is not moved. Junk is never carried and is deleted with the proposal. Symbolic links
   are moved as links, never followed: a carried file whose path in `materials/` is taken, or lies below a file or
   symbolic link there or below a `materials/` that is itself a symbolic link, and a destination (the spec bundle,
   an ADR, the materials directory, a carried file) whose directory resolves outside the workspace are refused
   before writing (`SPEC_PROPOSAL_TARGET_EXISTS`).
6. **Rewriting** of what pointed into the proposal (4.7).
7. **Removal** of the proposal, with its workflow records.
8. **Gates**: the proposal's `plan-intent` and `plan-accept` records carried to the spec (rule 12).

A failure in steps 1 to 5 rolls back: what was moved goes back, what was written is removed (a directory created
inside the moved `materials/` is followed back and removed when empty), and the proposal is kept. A directory that
still holds something the roll-back could not move back is kept, never removed; `SPEC_PROPOSAL_HANDOFF_FAILED` then
lists what could not be undone in its details.

The new spec's workflow is then evaluated from its first stage, after the gates step 8 recorded. Inside a linked worktree, at either `[tool.spec] worktree` level, the CLI also
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
when it has no list); an empty section gives one placeholder `### [AC-01] <scenario>` with Given/When/Then lines. A
new ID is `AC-<position>` (its scenario's place among the H3s), or the next higher number when an H3 with one tag
already uses it, so the IDs of a carried section are unique.

### 4.7 Rewriting Links and References

Every Markdown file under `docs/` and `specs/` is scanned, except the proposal itself, directories starting with `.`,
symbolic links and the files of completed spec bundles (`spec.md` with `status: completed`), which record the
proposal as it was; their `feedback/` is scanned, since feedback stays current.

- **Relative Markdown links** (inline links and images outside code, devkit's `extract_links`) that resolve into the
  proposal are pointed at the new locations by devkit's `relocate_links`, which replaces each changed file
  atomically: `proposal.md` (or the single file) to `spec.md`, `target-docs.md` to its
  copy, each PADR to its ADR, anything under a moved `materials/` to the same path under the moved directory
  (whether or not the file exists; a link into a `materials/` that was not moved is `unmapped`), each carried file to
  its new path, and the bundle directory to the spec bundle. URLs, root-relative and fragment-only links are left
  alone; a `#fragment`, a `?query` and a trailing `/` are kept. Files written for the bundle's location (the carried `spec.md`, the
  copied blueprint, the promoted ADRs, the moved materials and carried files) have their links resolved from where
  they were written, so a link outside
  the bundle keeps its target and one that still resolves to the same file keeps its spelling.
- **Document ID references** (frontmatter reference fields, `` `ID` `` and `[ID]` in prose, and the `proposal`
  provenance field) are rewritten from the IDs of the documents actually written: `PROP-<slug>` to `SPEC-<slug>`,
  each `PADR-<slug>` to its `ADR-<slug>`, and `PROP-<slug>-target` to itself (a `[ID]` becomes `` `ID` ``). Bare
  text, inline code other than a lone ID and fenced code do not change.

| Unresolved reason | Meaning |
| --- | --- |
| `unmapped` | A link into the proposal with no new location (the `decisions/` directory, a path that does not exist). |
| `ambiguous` | Another document declares the same ID, so it is not rewritten. |
| `unreadable`, `unwritable` | The file could not be read, parsed or written (line `0`); the link rewrites of a file that could not be written are not reported as rewritten. |

The `spec-next` skill's post-handoff check follows up the reported lines.

### 4.8 Prune

A handoff deletes the proposal in the worktree it runs in; merging that branch removes the tracked files from the
base checkout but leaves their directories. `devkit spec proposal prune [<slug>]` removes `docs/proposals/PROP-<slug>/` (every `PROP-*` directory without a slug) when it
holds no file at any depth (a symbolic link counts as a file; devkit's `remove_empty_tree`). A directory holding any
file is kept, and one that cannot be listed fails the prune before anything is removed. devkit-spec's
`devkit.post_finish` extension prunes the finished slug after a successful `devkit worktree finish`
(`ADR-cleanup-after-worktree-finish`); the command remains for other checkouts and a failed extension.

### 4.9 Commands and Options

Every command takes `-w/--workspace-root`, `--format text|json`, `-q`, `-v` and `--strict` (`CAP-HARN-command-mount`).

```bash
uv run devkit spec proposal new fast-engine --title "Fast Engine" --target-area capabilities/governance/
uv run devkit spec proposal new fast-engine --milestone "Phase 1" --with-target-docs
uv run devkit spec proposal new rate-limits --namespace api --task-kind bugfix
uv run devkit spec proposal new fast-engine-v2 --supersedes PROP-fast-engine        # close by supersede
uv run devkit spec proposal new fast-engine --summary "Replaces the regex rule engine with an AST parser."
uv run devkit spec proposal padr fast-engine "Use AST parser"        # decisions/PADR-use-ast-parser.md
uv run devkit spec proposal padr fast-engine "2024 roadmap" --slug roadmap-2024
uv run devkit spec proposal handoff fast-engine                      # status: accepted (plan-accept given)
uv run devkit spec proposal prune [<slug>]                           # base checkout; finish's extension does it per slug
```

| Option | Command | Meaning |
| --- | --- | --- |
| `--title/-t` | `new` | Title (default: the slug). |
| `--target-area/-a` | `new` | Capability area the proposal targets (default `capabilities/<area>/`); also the owned boundary. |
| `--milestone/-m` | `new` | Milestone, phase or release; carried to `spec.md`. |
| `--task-kind` | `new` | Write `task_kind: feature\|bugfix` (default `feature`); anything else is `ARGUMENT_INVALID`. |
| `--supersedes` | `new` | Write `supersedes: PROP-<old>`; a value that is not another proposal's ID is `ARGUMENT_INVALID`. |
| `--needs-decompose` | `new` | Write `needs_decompose: true`. |
| `--namespace` | `new` | Write `namespace: <name>`: `global` or registered in `[[tool.spec.namespaces]]`, else `ARGUMENT_INVALID` with the valid names in `[FIX]`. Omitted: the namespace the current directory lies in (`CAP-DOCS-namespaces`), else no field and the bundle is global. |
| `--slug` | `padr` | The PADR slug for its ID and file name (default: the title's slug); refused when its first segment has no letter. |
| `--summary` | `new`, `padr` | Write `summary: <text>`. Empty, or with a letter outside the Latin script: `ARGUMENT_INVALID` (`[TARGET] --summary`), nothing written. A promoted ADR keeps its PADR's summary. |
| `--with-target-docs` | `new` | Also write `target-docs.md`. |

### 4.10 Output

```text
[PROPOSAL: PROP-fast-engine path=docs/proposals/PROP-fast-engine/proposal.md dir=docs/proposals/PROP-fast-engine target_docs=- workflow=sdd-proposal]
[NEXT_CMD: devkit workflow next --unit docs/proposals/PROP-fast-engine]
[PADR: PADR-use-ast-parser path=docs/proposals/PROP-fast-engine/decisions/PADR-use-ast-parser.md proposal=PROP-fast-engine]
[HANDOFF: PROP-fast-engine spec=SPEC-fast-engine dir=specs/2026-10/20261013-fast-engine workflow=sdd-spec-feature]
[TARGET_DOCS: specs/2026-10/20261013-fast-engine/target-docs.md]
[MATERIALS: docs/materials/2026-10/20261013-fast-engine]
[PROMOTED_ADR: ADR-use-ast-parser path=docs/decisions/2026-10/20261013-use-ast-parser.md padr=PADR-use-ast-parser]
[DROPPED_RECORD: docs/proposals/PROP-fast-engine/decisions/01-gate-plan-intent.yaml]
[DROPPED_RECORD: docs/proposals/PROP-fast-engine/decisions/02-gate-plan-accept.yaml]
[CARRIED_GATE: gate:plan-intent decision=specs/2026-10/20261013-fast-engine/decisions/01-gate-plan-intent.yaml]
[CARRIED_GATE: gate:plan-accept decision=specs/2026-10/20261013-fast-engine/decisions/02-gate-plan-accept.yaml]
[REWRITTEN: docs/stories/core/US-x.md:5 kind=id from=PROP-fast-engine to=SPEC-fast-engine]
[REWRITTEN: docs/stories/core/US-x.md:9 kind=link from=../../proposals/PROP-fast-engine/proposal.md to=../../../specs/2026-10/20261013-fast-engine/spec.md]
[UNRESOLVED_LINK: docs/stories/core/US-x.md:9 kind=link target=../../proposals/PROP-fast-engine/decisions/ reason=unmapped]
[SCOPE: SPEC-fast-engine namespace=3f2a... revision=1 scopes=6 unresolved=2 shared_path=/repo/.git/devkit-spec-scope token=...]
[NEXT_CMD: devkit workflow next --unit specs/2026-10/20261013-fast-engine]
[PRUNED: docs/proposals/PROP-fast-engine]
[OK: nothing to prune]
```

- `new`: one `[PROPOSAL: ...]` line (`target_docs=-` without `--with-target-docs`, `workflow=-` when unbound), ending
  with `namespace=<name>` when the bundle reports a namespace: the field written, else `global` in a workspace that
  registers namespaces (none for a global bundle in a workspace without them); then `[NEXT_CMD: ...]` when
  `proposal.md` is bound to `sdd-proposal`. JSON: `id`, `dir`, `path`, `target_docs`, `workflow`, `namespace`
  (`null` when none is reported), `next_command`, `notices`.
- `padr`: one `[PADR: ...]` line. JSON: `id`, `path`, `proposal`.
- `handoff`: `[HANDOFF: ...]` (`workflow=-`: unbound), `[TARGET_DOCS: ...]` and `[MATERIALS: ...]` when the bundle had
  them, one `[PROMOTED_ADR: ...]` per PADR, one `[DROPPED_RECORD: <path>]` per workflow record of the proposal
  unit, one `[CARRIED_GATE: <request> decision=<path>]` per approval carried by name (rule 12),
  one `[REWRITTEN: <path>:<line> kind=link|id from= to=]` per rewrite, one
  `[UNRESOLVED_LINK: <path>:<line> kind= target= reason=]` per link or reference left as it was, `[SCOPE: ...]` when
  it registered the bundle, and `[NEXT_CMD: ...]` when `spec.md` is bound. JSON: `proposal`, `spec`, `dir`,
  `workflow`, `target_docs`, `materials`, `decisions` (`id`, `path`, `padr`), `dropped_records` (paths),
  `carried_gates` (`request`, `decision`), `rewritten_files`, `rewritten`
  (`path`, `line`, `kind`, `from`, `to`), `unresolved` (`path`, `line`, `kind`, `target`, `reason`), `next_command`,
  `notices`, `scope` (`record`, `token`, `namespace`, `shared_path`, or `null`).
- `prune`: `[PRUNED: <dir>]` per directory removed, else `[OK: nothing to prune]`. JSON: `{"pruned": [...]}`.

### 4.11 Library

```python
from devkit_spec.proposals import create_padr, create_proposal, handoff_proposal, prune_proposals

created = create_proposal(root, "fast-engine", title="Fast Engine", with_target_docs=True)  # CreatedProposal
create_padr(root, "fast-engine", "Use AST parser", summary="Parses rules with an AST.")  # CreatedDecision
create_padr(root, "fast-engine", "2024 roadmap", padr_slug="roadmap-2024")  # PADR-roadmap-2024
result = handoff_proposal(root, "fast-engine")  # HandoffResult
result.dir, result.workflow, result.decisions, result.rewritten, result.unresolved, result.notices
prune_proposals(root, "fast-engine")  # list of removed dirs
```

`create_proposal` also takes `target_area`, `milestone`, `task_kind`, `namespace`, `summary`, `supersedes`,
`needs_decompose` and `cwd` (the
directory whose namespace applies when `namespace` is omitted);
`carry_proposal_body` and `ensure_ac_ids` implement 4.6, `RelocationPlan`, `Rewritten` and `Unresolved` 4.7.

### 4.12 Codes

`0` success; `2` refused or failed (nothing was handed off). Warnings exit `0` (`1` under `--strict`).

| Code | Level | Class | Condition |
| --- | --- | --- | --- |
| `SPEC_PROPOSAL_SLUG_INVALID` | `ERROR` (`INPUT_ERROR`) | `ProposalSlugError` | The slug, or a PADR title or `--slug`, keeps no letter or digit after normalization; a new proposal's or PADR's slug, or at handoff a legacy proposal's or PADR's, has no letter in its first segment (`[FIX]`: rename it, or pass `--slug` to `padr`). |
| `SPEC_PROPOSAL_EXISTS` | `ERROR` (`INPUT_ERROR`) | `ProposalExistsError` | `new`: the bundle or `PROP-<slug>.md` exists. `padr`: a document already declares the PADR ID; `[TARGET]` lists it. |
| `SPEC_PROPOSAL_SLUG_CONFLICT` | `ERROR` (`INTERACTION`) | `ProposalSlugConflictError` | `SPEC-<slug>` exists (`[TARGET]`); the user picks another slug or drops the duplicate. |
| `SPEC_PROPOSAL_NOT_FOUND` | `ERROR` (`INPUT_ERROR`) | `ProposalNotFoundError` | No bundle or single-file proposal has the slug (`padr`: no bundle). |
| `SPEC_PROPOSAL_INVALID` | `ERROR` (`MAINTENANCE`) | `ProposalInvalidError` | The proposal, its blueprint or a PADR cannot be read or its frontmatter does not parse; or, at handoff, `namespace` is not a string naming `global` or a registered namespace, `summary` is not a string, or `task_kind` is not `feature` or `bugfix`. |
| `SPEC_PROPOSAL_NOT_APPROVED` | `ERROR` (`INTERACTION`) | `ProposalNotApprovedError` | Status is not `accepted`: `plan-accept` was not given. |
| `SPEC_PROPOSAL_NEEDS_DECOMPOSE` | `ERROR` (`INTERACTION`) | `ProposalNeedsDecomposeError` | The proposal carries `needs_decompose: true`; Backlog splits it into new drafts. |
| `SPEC_PROPOSAL_WRONG_WORKTREE` | `ERROR` (`INPUT_ERROR`) | `ProposalWrongWorktreeError` | `handoff` in a linked worktree on another branch than the slug, at either `[tool.spec] worktree` level (rule 11); `[FIX]` starts the slug's worktree and reruns the handoff there. |
| `SPEC_PROPOSAL_WORKFLOW_INVALID` | `ERROR` (`MAINTENANCE`) | `ProposalWorkflowError` | `task_kind: bugfix` and `sdd-spec-bugfix` does not resolve or validate; `[DETAIL]` carries devkit's code. |
| `SPEC_PROPOSAL_TARGET_EXISTS` | `ERROR` (`BLOCKED`) | `ProposalTargetExistsError` | The spec bundle, an ADR file or the materials directory exists, two PADRs map to one ADR, another document declares a promoted ADR's ID, a carried bundle file clashes with a file or symbolic link of `materials/` (or `materials/` is itself a symbolic link), or the directory of the spec bundle, an ADR, the materials directory or a carried file resolves outside the workspace. |
| `SPEC_PROPOSAL_HANDOFF_FAILED` | `ERROR` (`MAINTENANCE`) | `ProposalHandoffError` | A write failed; what was written is removed, the materials and carried files moved back, the proposal kept. When the roll-back was incomplete, `[DETAIL]` lists what could not be moved back or removed (kept, never deleted). |
| `SPEC_PROPOSAL_CLEANUP_FAILED` | `WARNING` | `ProposalCleanupWarning` | The handoff completed but the proposal could not be removed, or the post-finish prune of the slug's empty proposal directories failed (`CAP-COLL-work-scope-registry`). |
| `SPEC_PROPOSAL_LINK_UNRESOLVED` | `WARNING` | `ProposalLinkUnresolvedWarning` | Links or references into the proposal were left as they were; the `[UNRESOLVED_LINK]` lines list them. |
| `SPEC_PROPOSAL_REFS_REWRITTEN` | `NOTICE` | `ProposalReferencesRewrittenNotice` | ID references now name the spec or the ADRs; reread each `[REWRITTEN ... kind=id]` sentence. |
| `SPEC_PROPOSAL_UNBOUND` | `NOTICE` | `ProposalUnboundNotice` | `new`: `sdd-proposal` is not available, `proposal.md` is unbound. `handoff`: `task_kind` is `feature` (or absent) and `sdd-spec-feature` is not available, `spec.md` is unbound. The `[FIX]` is `devkit workflow bind --unit <dir> --workflow <id>`. |
| `ARGUMENT_INVALID` | `ERROR` (`INPUT_ERROR`) | devkit's `ArgumentError` | `new`: `--namespace` is neither `global` nor registered, `--task-kind` is not `feature` or `bugfix`, `--supersedes` names no other proposal. `new`, `padr`: `--summary` is empty or not English. |
| `SPEC_CONFIG_INVALID` | `ERROR` (`INPUT_ERROR`) | `SpecConfigError` | `[tool.spec]` is malformed and it must be read: `new` without `--namespace global`, a proposal's `namespace` other than `global` at handoff, or a handoff in a linked worktree. |
| `SPEC_SCOPE_REGISTER_FAILED` | `WARNING` | `ScopeRegisterFailedWarning` | A handoff in a task worktree could not register its bundle (`CAP-COLL-work-scope-registry`). |
