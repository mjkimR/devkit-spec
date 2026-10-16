---
id: PADR-milestone-documents
title: Milestone documents ordered by depends_on
summary: A milestone is an MS-<slug> document under docs/roadmap/ with a status lifecycle and a depends_on list declared by the successor as its start condition; Units join a milestone through a validated milestone ID reference, and hygiene warnings keep milestone status honest.
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
how milestones are ordered, how a Unit joins one, and how the record stays true as work completes.

---

## 2. Decision Drivers

- Reuse the document model: IDs, `RULE-document-reference`, `devkit spec list`, `resolve` and `refs`.
- Each fact has one owner: membership is stated once, on one side.
- Order expresses a real prerequisite, not a ranking that must be renumbered.
- No temporary checklists in `docs/` (`living-spec-writing`).
- The roadmap never blocks work: the user may deliberately start out of order.

---

## 3. Considered Options

### Option 1: One `docs/roadmap.md` with a milestone table
- **Pros**: one file to read.
- **Cons**: a milestone is an anchor, not an ID, so no rule validates a Unit's reference; every change touches the
  same file.

### Option 2: A milestone document kind, `MS-<slug>` (Selected)
- **Pros**: references validated by the existing rule; membership through `devkit spec refs MS-<slug> --direction in`;
  listing and status through `devkit spec list milestone`; one file per milestone.
- **Cons**: a new kind in the document model, its ID convention and a template.

### Option 3: Free-text `milestone` tags only
- **Pros**: no new file.
- **Cons**: a typo creates a new milestone; nowhere to state a goal, an order or an exit condition.

### Ordering: numbers, `after` or `depends_on`
- A numeric order must be renumbered on every insertion.
- `after` reads both ways ("comes after X" or "X may follow").
- **`depends_on`, declared by the successor (Selected)**: the prerequisite is a fact the successor owns, usually
  unknown when the predecessor is written; the reverse direction is a query (`refs --direction in`). It matches
  proposal `supersedes` (the new side declares) and autohub Work Plan dependencies.

---

## 4. Decision Outcome

Option 2 with `depends_on`:

- **Document**: `docs/roadmap/MS-<slug>.md` (`docs/packages/<name>/roadmap/` in a namespace), kind `milestone`, ID
  prefix `MS`. Frontmatter: `id`, `title`, English `summary`, `status`, `created_at`, optional `depends_on` (a list of
  `MS-` IDs). Body: the goal it advances (citing `ARCH-01-introduction-and-goals`), the exit condition, out of scope.
  The body lists no work items.
- **Status**: `planned` → `active` → `done`, or `dropped` from `planned` or `active`. Several milestones may be
  `active` at once. Status changes are Backlog commits; the user decides that an exit condition holds.
- **`depends_on`** is a start condition: a milestone is *ready* when every milestone it depends on is `done`. It is
  enforced by guidance and warnings, never by refusal.
- **Membership**: `milestone` in `proposal.md` and `spec.md` changes from free text to one `MS-` ID, a relation field
  validated by `RULE-document-reference` and carried on handoff. Units without a milestone stay valid.
- **Checks**: a `depends_on` cycle is a rule error. Hygiene warnings: an `active` milestone with a dependency not
  `done`; a `done` milestone with a member Unit not completed; an `active` milestone whose members are all completed
  and with no draft left (a candidate to close).
- **Next work**: when no Unit is in progress, `spec-next` recommends draft proposals from `active` milestones, then
  from ready `planned` ones, each ordered by `priority`, then `size` (smaller first); drafts without a milestone come
  last. `devkit spec list` gains the sorting and grouping this needs.

---

## 5. Consequences

- `CAP-DOCS-document-model` adds the kind and the `milestone` relation field; `RULE-id-convention` adds its location;
  a milestone template joins the bundle's templates; the docs skeleton gains `docs/roadmap/`.
- `devkit spec proposal new --milestone` and `devkit spec new --milestone` take an `MS-` ID.
- The existing free-text values need no migration: no current proposal or active spec sets `milestone`.
- The hygiene warnings run through devkit-spec's `devkit.hygiene` extension, like the rejected-proposal warning.
