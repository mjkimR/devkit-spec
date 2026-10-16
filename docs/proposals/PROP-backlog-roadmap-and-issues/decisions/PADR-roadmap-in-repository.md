---
id: PADR-roadmap-in-repository
title: Roadmap owned by the repository
summary: 'The repository, not GitHub or autohub, owns goals and the roadmap: goals stay in ARCH-01-introduction-and-goals, milestones become documents, and GitHub issues are an optional intake linked from Units, never a second backlog.'
proposal: PROP-backlog-roadmap-and-issues
status: draft
created_at: 2026-10-16
---

# [PADR-roadmap-in-repository] Roadmap owned by the repository

- **Status**: Draft
- **Date**: 2026-10-16
- **Involved Components/Capabilities**: `ARCH-01-introduction-and-goals`, `CAP-DOCS-document-model`,
  `CAP-DLV-proposal-incubation`, `CAP-HARN-agent-guidance`
- **Related**: `PADR-milestone-documents` (the form of a milestone), `PADR-issue-link-only` (the GitHub link)

---

## 1. Context & Problem Statement

Three sources disagree on where Backlog keeps its plan:

- The strategy layer's master flow (workbench `docs/strategy-layer/01-master-flow.md`, §1, §5 and its glossary)
  makes Backlog "manage GitHub issues and milestones" and defines a Phase as one GitHub milestone.
- autohub's Work Plan backlog contract states that repository documents own long-term direction, and that GitHub
  issues are outbound execution records, "not a second backlog"; autohub syncs Work Plans to issues one way.
- devkit-spec has no plan above the Unit: `milestone` is free text nothing reads, and `ARCH-01-introduction-and-goals`
  lists goals no work refers to.

Neither GitHub milestones nor issues are in use in this repository (checked 2026-10-16), so the choice costs no
migration.

---

## 2. Decision Drivers

- An agent orients from files it can read offline; `spec-next` must recommend work without network access.
- References are validated deterministically by rules that run offline, in the commit gate and in CI.
- Consumer projects need not host on GitHub.
- One owner per fact: no second backlog beside autohub's Work Plans and the repository's proposals.
- Proportionate cost: no new document kind without a reader that needs it.

---

## 3. Considered Options

### Option 1: GitHub issues and milestones own the roadmap
- **Overview**: the strategy layer's current wording. Backlog creates issues and milestones with `gh`; Units refer to
  them.
- **Pros**: familiar UI for people; the natural intake for requests from outside.
- **Cons**: unreadable offline; references cannot be validated by rules; ties consumers to GitHub; contradicts
  autohub's contract and adds a third copy of the plan.

### Option 2: The repository owns goals and the roadmap (Selected)
- **Overview**: goals stay in `ARCH-01-introduction-and-goals`; milestones are documents (`PADR-milestone-documents`);
  Units link to their milestone by ID and optionally to a GitHub issue (`PADR-issue-link-only`).
- **Pros**: offline, validated by existing rules, reachable through `devkit spec list`, `resolve` and `refs`; history
  in Git; consistent with autohub's ownership statement.
- **Cons**: changing a milestone is a commit (Backlog commits go to the base directly, outside the worktree and pull
  request policies); no human-facing roadmap screen until a viewer renders it.

### Option 3: autohub Work Plans own the roadmap
- **Overview**: plans chained by dependencies express milestone order.
- **Cons**: devkit-spec does not know autohub (one-way dependency); unavailable to local-only projects.

---

## 4. Decision Outcome

Option 2:

- **Goals** stay as prose in `ARCH-01-introduction-and-goals` §1.2. They get no IDs and no document kind; a milestone
  names the goal it advances by citing that document. Reopen condition: a repository needs goals per namespace, or
  more than one milestone must be traced to the same goal mechanically.
- **Milestones** are repository documents (`PADR-milestone-documents`). The strategy layer's glossary entry "Phase =
  one GitHub milestone" becomes "Phase = one milestone document".
- **Requests** not yet in a Unit: open feedback stays the intake for follow-ups found during work; a request from
  outside may arrive as a GitHub issue, which Backlog turns into a draft proposal or a spec Unit that links it
  (`PADR-issue-link-only`). Draft proposals remain the backlog of proposal-depth work.
- **Backlog** keeps its role (classify, add drafts, decompose) and adds placing work in a milestone; it does not create
  or manage GitHub milestones.

---

## 5. Consequences

- The strategy layer's 01 §1 table, §5 diagram and text and the glossary are updated first (workbench), then this
  package follows; 02's devkit-spec responsibilities gain the milestone document kind.
- `ARCH-01-introduction-and-goals` states where the roadmap lives.
- autohub may later map a Work Plan's `group_key` to a milestone ID and render milestones in the repository viewer;
  neither is part of this proposal.
- The Backlog subagents listed as TODO in 01 §5 (triage, decomposer) and GitHub issue lookup commands stay follow-ups,
  added when use shows a need.
