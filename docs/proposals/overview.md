# Proposals: Overview

A proposal incubates an idea (a feature, a technical spike, an architectural change) before it becomes a feature spec. `devkit_spec.proposals` implements the lifecycle and `devkit spec proposal new|padr|handoff` ([reference](reference.md)) exposes it; `devkit spec new` creates a spec bundle without a proposal ([section 6](#6-spec-bundles-without-a-proposal)). Ported from specrig's `proposal` commands; [section 7](#7-differences-from-specrig) lists what changed.

## 1. Bundle Layout

```text
docs/proposals/PROP-<slug>/
├── proposal.md       # required: background, hypothesis, spike questions, design
├── target-docs.md    # optional: blueprint of the Living Spec changes once accepted (--with-target-docs)
├── decisions/        # preliminary decision records, PADR-<slug>.md
└── materials/        # research, benchmarks, surveys
```

A single-file proposal `docs/proposals/PROP-<slug>.md` can be handed off too; it has no PADRs, materials or blueprint, and its body is not carried (the spec gets the plain skeleton).

- **Slugs** are normalized: a leading `PROP-` and a trailing `.md` are dropped, every run of characters other than letters, digits, `_` and `-` becomes `-`, outer dashes are trimmed, and the result is lower-cased (`"PROP-Fast Engine"` is `fast-engine`). A slug with no letter or digit left is `SPEC_PROPOSAL_SLUG_INVALID`.
- **A proposal and a spec never share a slug**, so a handed-off `PROP-<slug>` maps to exactly one `SPEC-<slug>`. `new` and `handoff` refuse a slug whose `SPEC-<slug>` exists (`SPEC_PROPOSAL_SLUG_CONFLICT`); a document that cannot be indexed never blocks them.
- **`proposal.md` frontmatter**: `id`, `title`, `status` (`draft`, `reviewing`, `accepted`, `rejected`), `created_at`, `target_area`, `priority`, `size`, optional `milestone` (carried to `spec.md`), `boundaries` (`owns`, `excludes`: carried to `plan.md` and `tasks.md`), and optional `handoff_workflow` (the workflow id the spec follows after handoff, without a prefix; default `direct-delivery`; `new --handoff-workflow` writes it). `workflow` and `workflow_hash` are devkit's binding of the proposal unit itself, never the follow-up workflow.
- **Binding**: `proposal.md` is the anchor of a devkit workflow unit. `new` binds it to workflow `incubated-delivery` when that definition resolves and validates in the workspace, and prints `[NEXT_CMD: devkit workflow next --unit docs/proposals/PROP-<slug>]`; otherwise the proposal stays unbound with a `SPEC_PROPOSAL_UNBOUND` notice.
- **PADRs**: `padr <slug> <title>` writes `decisions/PADR-<title slug>.md` with `proposal: PROP-<slug>` and `status: draft`, shaped like the decision template. PADR IDs are unique across the repository (`SPEC_PROPOSAL_EXISTS`).
- **`target-docs.md`** declares `PROP-<slug>-target` and `proposal: PROP-<slug>`; it covers the capability ledger, stories, architecture and decisions, conventions and a before/after comparison.

## 2. Approval

Handoff needs the user's approval, never an inferred one: `status: accepted`, or `draft`/`reviewing` with `--direction-chosen`, which the agent passes only when the user explicitly chose the proposal's direction. Anything else is `SPEC_PROPOSAL_NOT_APPROVED` (`INTERACTION`: stop and ask the user).

## 3. Handoff

`handoff_proposal` validates everything before it writes: the slug, the proposal file and its frontmatter, the approval, the slug conflict, the workflow binding and every path it would create. A path that already exists, two PADRs that would become the same ADR, or an ADR ID another document already declares is `SPEC_PROPOSAL_TARGET_EXISTS`. Then, with `<YYYY-MM>` and `<YYYYMMDD>` today's date:

1. **Spec bundle** `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/`:
   - `spec.md` (`SPEC-<slug>`, `status: planned`, `created`, the proposal's `milestone`): the problem statement starts with `Handed off from proposal PROP-<slug> on <date>.` and the preserved materials and blueprint, then the carried body ([section 4](#4-carrying-the-proposal-body)).
   - `plan.md` (`PLAN-<slug>`, `spec: SPEC-<slug>`; not for `bugfix`, see step 2): target area, blueprint reference, planned and excluded boundaries.
   - `tasks.md` (`TASKS-<slug>`): one implementation task whose boundary is `boundaries.owns` (else `target_area`) and whose `_Requirements:` line lists every acceptance criterion ID, so `RULE-task-coverage` holds.
   - Each file carries the skeleton marker `<!-- devkit:skeleton -->` as its first body line: devkit's `not-skeleton` check keeps a workflow stage open until the file is written for real and the line removed. Only `spec.md` has a status.
2. **Workflow binding**: `spec.md` records `workflow` and `workflow_hash` (devkit's binding, `devkit.workflow.write_binding`). A proposal whose `handoff_workflow` names a workflow must name a definition that resolves and validates, or the handoff fails before writing anything (`SPEC_PROPOSAL_WORKFLOW_INVALID`). Without one, `direct-delivery` is bound when the project has it; otherwise the spec stays unbound and a `SPEC_PROPOSAL_UNBOUND` notice says so. A spec bound to `bugfix` carries `kind: bugfix` (that workflow's exit checks `frontmatter(spec.md kind bugfix)`), and its bundle gets `spec.md` only: the bugfix workflow writes `plan.md` and `tasks.md` in its `plan-tasks` stage, and skeletons would have to match the characterized criteria at the `characterize` stage's `lint-clean` exit. The proposal's target area and boundaries, which `plan.md` and `tasks.md` would hold, go into a `### Target Area & Boundaries` section of the carried notes instead.
3. **Blueprint**: `target-docs.md` is copied into the spec bundle as written; only its provenance is rewritten (step 6).
4. **PADR promotion**: each `decisions/PADR-<slug>.md` becomes `docs/decisions/<YYYY-MM>/<YYYYMMDD>-<slug>.md`. Every `PADR-<slug>` in it becomes `ADR-<slug>`, a frontmatter `status: draft` (or `proposed`) becomes `status: accepted`, and a body line `- **Status**: Draft` (or `Proposed`) becomes `- **Status**: Accepted`: a promoted decision is accepted by definition. Other files under `decisions/` are not promoted.
5. **Materials**: a non-empty `materials/` moves to `docs/materials/<YYYY-MM>/<YYYYMMDD>-<slug>/`.
6. **Rewriting** what pointed into the proposal ([section 5](#5-rewriting-links-and-references)).
7. **Removal** of the proposal, last. If it cannot be removed, the handoff still succeeded and `SPEC_PROPOSAL_CLEANUP_FAILED` names what to delete.

A file system error in steps 1 to 5 removes what they wrote, moves the materials back and keeps the proposal (`SPEC_PROPOSAL_HANDOFF_FAILED`). Other files in the bundle (outside `proposal.md`, `target-docs.md`, `PADR-*.md` and `materials/`) are removed with it; Git history keeps them.

## 4. Carrying the Proposal Body

The body of a bundle's `proposal.md` after the frontmatter and the first H1 is split into H2 sections (fenced code is never a heading), each classified by its heading, case-insensitively:

| Heading contains | Lands in | How |
| --- | --- | --- |
| (text before the first H2), `background`, `hypothesis`, `problem`, `motivation`, `origin` | 1. Problem Statement & Motivation | heading kept as H3, inner headings demoted one level |
| `non-goal`, `non goal`, `scope excluded`, `out of scope` | 3. Non-Goals | body only; a placeholder item when none |
| `acceptance` | 4. Acceptance Criteria & Behavioral Contracts | body only, with acceptance criterion IDs (below) |
| anything else | 5. Carried Proposal Notes | heading kept as H3, inner headings demoted; not contracts |

Bodies are verbatim apart from heading levels; leading and trailing blank lines and trailing horizontal rules are trimmed.

Acceptance criteria get IDs so the spec satisfies `RULE-task-coverage`: an H3 with exactly one `[AC-NN]` keeps it; another H3 becomes `### Scenario <n> [AC-NN]: <text>`; a body without H3 gets a `### Scenario <n> [AC-NN]: Carried from proposal` heading before each top-level list item (or one before everything when it has no list); an empty section gives one placeholder `### [AC-01] <scenario>` with Given/When/Then lines. New IDs are numbered `AC-<count + 1>` in order.

## 5. Rewriting Links and References

After the writes, every Markdown file under `docs/` and `specs/` is scanned, except the proposal itself, directories starting with `.`, symbolic links and the files of completed spec bundles (`spec.md` with `status: completed`), which record the proposal as it was.

**Relative Markdown links** (inline links and images outside code, `devkit.rules.extract_links`) that resolve into the proposal are pointed at the new locations: `proposal.md` (or the single file) to `spec.md`, `target-docs.md` to its copy, each PADR to its ADR, anything under `materials/` to the same path under the moved directory (whether or not the file exists), and the bundle directory itself to the spec bundle. URLs, root-relative and fragment-only links are left alone; the `#fragment` or `?query` is kept. Files written for the bundle's location (the carried `spec.md`, the copied blueprint, the moved materials) have their links resolved from where they were written, so a link to something outside the bundle keeps its target and one that still resolves to the same file keeps its spelling.

**Document ID references** (frontmatter reference fields, `` `ID` `` and `[ID]` in prose, and the `proposal` provenance field; `devkit_spec.documents`) are rewritten from the IDs of the documents actually written: `PROP-<slug>` to `SPEC-<slug>`, each `PADR-<slug>` to its `ADR-<slug>`, and `PROP-<slug>-target` to itself (a `[ID]` becomes `` `ID` ``). Bare text, inline code other than a lone ID and fenced code are not references and do not change. Each rewritten reference is reported with its line, because whether a sentence named the proposal as its origin or as the work to do cannot be decided mechanically: a `SPEC_PROPOSAL_REFS_REWRITTEN` notice asks the agent to reread them.

What cannot be mapped stays as it was and is reported (`SPEC_PROPOSAL_LINK_UNRESOLVED` warning) with a reason:

| Reason | Meaning |
| --- | --- |
| `unmapped` | A link into the proposal with no new location (`decisions/`, a file that was not promoted). |
| `removed` | A reference to an ID declared inside the proposal that nothing replaced (a non-`PADR-*` file under `decisions/`). |
| `ambiguous` | Another document declares the same ID, so it is not rewritten. |
| `unreadable`, `unwritable` | The file could not be read, parsed or written (line `0`). |

## 6. Spec Bundles Without a Proposal

`devkit spec new <slug> [--title] [--workflow <id>] [--date YYYY-MM-DD]` (`create_spec`) creates `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` for Route 2 work, where `devkit workflow new` would write an `id` the rules reject. It writes the same skeletons as a handoff with nothing carried: `SPEC-<slug>` (`status: planned`, `created` the bundle date), `PLAN-<slug>` and `TASKS-<slug>`, each with the skeleton marker, one placeholder acceptance criterion and its task. A leading `SPEC-` is dropped from the slug before the proposal normalization.

- It refuses (`SPEC_EXISTS`, nothing written) a slug whose `SPEC-<slug>` or `PROP-<slug>` a document declares, a proposal bundle or file of the slug, and an existing bundle directory; a slug with no letter or digit is `SPEC_SLUG_INVALID`.
- `spec.md` is bound to `--workflow`, default `direct-delivery`, as in a handoff: an explicit workflow that does not resolve or validate fails before writing (`SPEC_WORKFLOW_INVALID`), a missing default leaves it unbound with a `SPEC_UNBOUND` notice, and `bugfix` adds `kind: bugfix`.
- A `bugfix` bundle gets `spec.md` only, as in a handoff: that workflow writes `plan.md` and `tasks.md` in its `plan-tasks` stage, and its `characterize` stage exits on `lint-clean`, where a skeleton `tasks.md` would have to match the characterized criteria (`RULE-task-coverage` skips a spec without `tasks.md`).
- A file system error removes what was written (`SPEC_WRITE_FAILED`).

## 7. Differences from specrig

- **No namespaces**: the `namespace` frontmatter field, the `--namespace` option and namespace validation are not ported.
- **No worktree routing**: specrig's handoff moved into the slug's Git worktree under `git.worktree=on` and registered the scope there. Here the handoff runs in the workspace it is given; worktrees are devkit's (`devkit worktree`).
- **`--direction-chosen`** replaces `--given direction-chosen` and is honoured whatever the worktree policy (specrig accepted it only with `git.worktree=on`).
- **The follow-up workflow is `handoff_workflow`** (specrig: `workflow`), because `workflow` is devkit's binding of the proposal unit; ids have no `WF-` prefix (`handoff_workflow: bugfix`, default `direct-delivery`). New proposals are bound to `incubated-delivery`, and a spec bound to `bugfix` gets `kind: bugfix`.
- **English only**: section keywords and the PADR body are English; the promoted status line is `- **Status**: Accepted`.
- **Stricter before writing**: unreadable PADRs, an existing target path, colliding ADRs and duplicate ADR IDs refuse the handoff instead of being skipped or overwritten, and a failed write is rolled back.
- **Generated text follows the bundle templates** (`proposal.md`, `decision.md`); verification lines in `plan.md` and `tasks.md` are placeholders rather than `just test`.
