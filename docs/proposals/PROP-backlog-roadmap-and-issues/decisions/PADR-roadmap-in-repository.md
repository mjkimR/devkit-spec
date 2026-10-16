---
id: PADR-roadmap-in-repository
title: Roadmap owned by the repository
summary: 'The repository, not GitHub or autohub, owns goals and the roadmap: goals stay in ARCH-01-introduction-and-goals, milestones become documents, every request not yet started is a draft proposal, and GitHub issues are an optional intake that Backlog drains into drafts, never a second backlog.'
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
  makes Backlog "manage GitHub issues and milestones" and defines a Phase as one GitHub milestone. Its decomposition
  rule (§5.2) splits a draft into drafts "or `session` · `spec` depth issues" and keeps the link to the original
  request in the issue's parent/child relation.
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
- Consumer projects need not host on GitHub: no request, and no link to its origin, may exist only in GitHub.
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
  every request not yet started is a draft proposal; Units link to their milestone by ID and optionally to a GitHub
  issue (`PADR-issue-link-only`).
- **Pros**: offline, validated by existing rules, reachable through `devkit spec list`, `resolve` and `refs`; history
  in Git; agrees with autohub that repository documents own direction.
- **Cons**: changing a milestone is a commit; no human-facing roadmap screen until a viewer renders it; small requests
  carry the weight of a draft proposal.

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
- **Requests not yet started are draft proposals**, whatever their eventual depth. A decomposition splits a draft into
  drafts only, each naming the original in `decomposed_from: PROP-<slug>` (a plain field like `supersedes`, not a
  validated reference, since the original is deleted in the same commit; `--decomposed-from` checks at creation that
  the original exists and is a draft). The handoff carries `decomposed_from` and `supersedes` to `spec.md` as
  provenance fields, like `proposal`, so a spec keeps the link to the request it came from. Until a direct-acceptance
  path exists (the draft proposal `draft-direct-acceptance` on the base), a small draft runs Planning at `low` effort.
- **Follow-ups found during work** stay feedback; Backlog promotes a `repo`-scope feedback item it accepts into a
  draft placed in a milestone.
- **GitHub issues are intake, not backlog.** An open issue that no Unit links is a request not yet triaged; a linked
  one is tracked by its Unit. When `gh` is available, Backlog lists open issues, skips those a Unit links (`issue` on a
  draft, proposal or spec on the base, or on the `plan-`/`dev-` branch of a linked slug) and drains each of the rest:
  into a draft linked by `issue`; into feedback, closing the issue with a comment naming the feedback ID; or closed as
  declined, with the reason. Issues autohub creates as Work Plan records are skipped, recognized by the record-keeping
  notice autohub writes into them; the exact marker is agreed with autohub before the procedure ships
  (`PADR-issue-link-only`).
- **Backlog** keeps its role (classify, add drafts, decompose) and adds placing work in a milestone and draining open
  issues; it does not create or manage GitHub milestones.

---

## 5. Consequences

- **Precondition of the handoff**: the strategy layer is updated first, by the Host after `plan-accept` and before
  `devkit spec proposal handoff`: 01 §1 table, §5 (diagram, text and TODO), §5.1 (the policy exemption now covers
  milestone documents: Backlog files that are not code), §5.2 (drafts only, `decomposed_from`), §7.4 (supersede link),
  §10 change list and the glossary; 02 adds the milestone kind to devkit-spec's responsibilities.
- `ARCH-01-introduction-and-goals` states where the roadmap lives.
- autohub may later map a Work Plan's `group_key` to a milestone ID and render milestones in the repository viewer;
  neither is part of this proposal.
- Follow-ups outside this proposal: a direct-acceptance path for drafts that need no Planning (a draft proposal of its
  own), GitHub lookup commands, and the Backlog subagents listed as TODO in 01 §5 (triage, decomposer).
