---
id: PADR-milestone-documents
title: Milestone documents ordered by depends_on
summary: A milestone is an MS-<slug> document under docs/roadmap/ with a status lifecycle and a depends_on list declared by the successor as its start condition; Units join it by a validated ID, and spec-next recommends Planning-eligible drafts in a fully defined order.
proposal: PROP-backlog-roadmap-and-issues
status: draft
created_at: 2026-10-16
---

# [PADR-milestone-documents] Milestone documents ordered by depends_on

- **Status**: Draft
- **Date**: 2026-10-16
- **Involved Components/Capabilities**: `CAP-DOCS-document-model`, `CAP-DOCS-document-lookup`, `CAP-GOV-spec-rules`,
  `CAP-DLV-proposal-incubation`, `CAP-DLV-spec-bundles`, `CAP-HARN-agent-guidance`
- **Parent**: `PADR-roadmap-in-repository`

---

## 1. Context & Problem Statement

`PADR-roadmap-in-repository` puts the roadmap in the repository. It still has to choose the form: what a milestone is,
how milestones are ordered, how a Unit joins one, how the next work is chosen, and how the record stays true as work
completes, given that Units in progress live on `plan-` and `dev-` branches while the base shows only merged state
(01 §4.7).

---

## 2. Decision Drivers

- Reuse the document model: IDs, `RULE-document-reference`, `devkit spec list`, `resolve` and `refs`.
- Each fact has one owner: membership is stated once, on one side.
- Order expresses a real prerequisite, not a ranking that must be renumbered.
- No temporary checklists in `docs/` (`living-spec-writing`).
- The roadmap never blocks work: the user may deliberately start out of order.
- Checks that read only the base never claim facts that live on branches.
- Build for the use there is: no milestone exists yet.

---

## 3. Considered Options

### Option 1: One `docs/roadmap.md` with a milestone table
- **Pros**: one file to read.
- **Cons**: a milestone is an anchor, not an ID, so no rule validates a Unit's reference; every change touches the
  same file.

### Option 2: A milestone document kind, `MS-<slug>` (Selected)
- **Pros**: references validated by the existing rule; membership through `devkit spec refs MS-<slug> --direction in`;
  listing and status through `devkit spec list milestone`; one file per milestone.
- **Cons**: a new kind in the document model, its ID convention, its format checks and a template.

### Option 3: Free-text `milestone` tags only
- **Pros**: no new file.
- **Cons**: a typo creates a new milestone; nowhere to state a goal, an order or an exit condition.

### Ordering: numbers, `after` or `depends_on`
- A numeric order must be renumbered on every insertion.
- `after` reads both ways ("comes after X" or "X may follow").
- **`depends_on`, declared by the successor (Selected)**: the prerequisite is a fact the successor owns, usually
  unknown when the predecessor is written; the reverse direction is a query (`refs --direction in`). It matches
  proposal `supersedes` (the new side declares) and autohub Work Plan dependencies.

### Next-work ordering: in the CLI or in the skill
- `devkit spec list --sort`: reverses `CAP-DOCS-document-lookup`'s non-goal (priority and size are `--where` fields)
  and would sort the enum values as text (`low` before `medium`, `L` before `M`).
- **In `spec-next` over `--where` queries (Selected)**: no CLI change; the order is documented once in the skill.

---

## 4. Decision Outcome

Option 2 with `depends_on`, ordered by the skill:

- **Document**: `docs/roadmap/MS-<slug>.md`, kind `milestone`, ID prefix `MS`. Frontmatter: `id`, `title`, English
  `summary`, `status`, `created_at`, optional `depends_on` (a list of `MS-` IDs). Body: the goal it advances (citing
  `ARCH-01-introduction-and-goals`), the exit condition, out of scope; no work items. The slug starts with a word:
  release-style names read `MS-release-1-0`, not `MS-1-0`. Milestones are global; per-namespace roadmaps are deferred
  until a repository needs them.
- **Status**: `planned` → `active` → `done`, or `dropped` from `planned` or `active`. The user activates, closes and
  drops a milestone through Backlog (base commits, like drafts). Several may be `active` at once. `done` and `dropped`
  milestones stay as historical documents: `devkit spec list` hides them by default as it hides completed spec
  bundles, and `refs --direction in` keeps their membership history.
- **`depends_on`** is a start condition: a milestone is *ready* when every milestone it depends on is `done` or
  `dropped`. Enforced at the decision points, never by refusal; `depends_on` is valid on milestones only.
- **Membership**: `milestone` in `proposal.md` and `spec.md` changes from free text to one `MS-` ID, validated by
  `RULE-document-reference` and carried on handoff. A member is *settled* when it is a completed spec; a rejected
  proposal is not a member; `session` work has no Unit and is never a member. Units without a milestone stay valid.
- **Decision points** (Backlog steps, each with the user):
  - *Activate*: the Host lists the dependencies not yet `done` or `dropped`; the user may activate anyway.
  - *Close* (`done`): the Host first checks the members on the base and the `plan-` and `dev-` branches of their
    slugs (as the proposal listing does); open members are re-pointed to another milestone or the close waits.
  - *Drop*: each unsettled member is re-pointed, has its `milestone` cleared, or is rejected; each successor that
    depends on the milestone is shown, and the user keeps or edits its `depends_on`.
- **Checks**:
  - Rules: `RULE-spec-format` covers `docs/roadmap/` (required keys, the status vocabulary); its fix fills
    `status: planned` and derives `MS-<stem>` for a milestone. `RULE-document-summary` requires a milestone `summary`;
    a `depends_on` cycle is a `RULE-document-reference` error.
  - Two hygiene warnings, which read the base only and settle when the members are fixed: a `done` or `dropped`
    milestone with a member on the base that is neither settled nor rejected. Out-of-order activation raises no
    warning: the user decided it at activation.
  - No "candidate to close" warning: membership on branches is invisible to the base. Reconsider it once two or more
    milestones are `active` at once in practice.
- **Next work**: a Unit is *in progress* when it has a `plan-` or `dev-` branch, is a `reviewing` or `accepted`
  proposal, or is a spec not completed. While one is, `spec-next` follows the stage matrix for it. Queued drafts are not
  in progress: when nothing is, `spec-next` considers drafts whose displayed status is `draft` and that carry no
  `needs_decompose`, in this order:
  1. `critical` drafts, whatever their milestone;
  2. drafts of `active` milestones, then of ready `planned` milestones, then drafts without a milestone; milestones of
     one rank by `created_at`, then ID;
  3. within a group, `priority` (`critical`, `high`, `medium`, `low`), then `size` (`S`, `M`, `L`, `XL`), then
     `created_at`, then ID.

  A draft without `plan-intent` is recommended as "confirm the intent". Drafts in milestones that are not ready or are
  `done` or `dropped`, and `needs_decompose` drafts, are reported as Backlog actions. Open feedback adds a suggestion of
  a hygiene pass.
- **Review**: when three milestones are `done` or on 2027-01-31, whichever comes first, Backlog reviews whether
  milestones were used and whether the warnings fired usefully, and records the result as a decision
  (a roadmap-review ADR); unused machinery is proposed for removal. The carrier is `spec-next`'s idle
  step: it counts `done` milestones, compares the date and, until that decision exists, reports the review as due.

---

## 5. Consequences

- `CAP-DOCS-document-model` adds the kind, the `milestone` relation field and the `depends_on` field (milestones only),
  and extends the historical-document rule to `done` and `dropped` milestones; `RULE-id-convention` adds the location;
  a milestone template joins the bundle's templates; the docs skeleton gains `docs/roadmap/`.
- `devkit spec proposal new --milestone` and `devkit spec new --milestone` take an `MS-` ID.
- The existing free-text values need no migration: no current proposal or active spec sets `milestone`.
- The hygiene warnings run through devkit-spec's `devkit.hygiene` extension, like the rejected-proposal warning.
