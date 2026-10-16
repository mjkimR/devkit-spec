---
id: PROP-backlog-roadmap-and-issues
title: 'Backlog: goals, roadmap and issue tracking'
summary: Gives Backlog a repository-owned roadmap of milestone documents ordered by depends_on, links Units to their milestone and optionally to an inbound GitHub issue, keeps every request not yet started as a draft, and lets spec-next recommend the next work.
status: accepted                      # draft | reviewing | accepted | rejected
created_at: 2026-10-16
target_area: capabilities/delivery/
priority: high                        # critical | high | medium | low
size: M                               # S | M | L | XL
boundaries:
  owns:
    - capabilities/delivery/
    - capabilities/documents/
    - capabilities/governance/
    - capabilities/harness/
    - stories/delivery/
    - architecture/ARCH-01-introduction-and-goals.md
  excludes:
    - docs/decisions/
task_kind: feature                    # feature | bugfix: the spec follows sdd-spec-<task_kind>
workflow: sdd-proposal
workflow_hash: sha256:90918c632715461d07f99f683b8381bdbe6381ad6689a7575a72c002c18c1399
---

# [PROP-backlog-roadmap-and-issues] Backlog: goals, roadmap and issue tracking

- **Parent design**: the strategy layer's master flow (workbench `docs/strategy-layer/01-master-flow.md`, §5 Backlog),
  the source of truth for the activity model. Its §5 lists as TODO: the issue management procedure, the Backlog
  subagent set (scout, challenger, triage, decomposer) and the issue ↔ Unit link rule.
- **Related**: `ADR-task-kind-and-planning-depth` (Backlog classifies), `CAP-DLV-proposal-incubation` (the `priority`,
  `size` and `milestone` fields), `ARCH-01-introduction-and-goals` (mission and goals).
- **Preliminary decisions**: `PADR-roadmap-in-repository`, `PADR-milestone-documents`, `PADR-issue-link-only`.

## 1. Background & Hypothesis

### 1.1 Problem

The delivery model is detailed below the Unit and thin above it. A single proposal or spec is tracked from draft to
merge; what the Units add up to is not tracked anywhere.

- **Backlog has a name but no procedure.** The strategy layer defines Backlog as "collect requests, manage issues and
  milestones, classify, write draft proposals", and the `spec` skill's classification reference says "Manage the
  GitHub issue and milestone". Only classification and the draft proposal are specified. This repository has no
  GitHub milestone and no issue (checked 2026-10-16).
- **`milestone` is a free-text field nothing reads.** `devkit spec proposal new --milestone` writes it and handoff
  copies it to `spec.md`; no document defines what a milestone name means, its order or its exit condition, and none
  of the current drafts sets it.
- **`priority` and `size` are recorded, not used.** The `spec-next` decision matrix ends at "Idle: ready for a new
  request".
- **Goals and work are not linked.** `ARCH-01-introduction-and-goals` lists five goals, but no proposal or spec says
  which goal it serves.
- **The link to the original request is undefined.** Decomposition (01 §5.2) splits a draft into drafts or
  "`session` · `spec` depth issues" and keeps the link in "the GitHub issue's parent/child relation", while the
  issue ↔ Unit rule is still TODO; without GitHub the split items and their origin are lost.
- **The owners disagree.** The strategy layer makes a Phase one GitHub milestone; autohub's Work Plan contract says
  repository documents own long-term direction and GitHub issues are "not a second backlog".

### 1.2 Hypothesis

- Keeping the roadmap in the repository as documents with IDs lets an agent read, validate and query it offline with
  the tools it already uses (`list`, `resolve`, `refs`, the rules), and settles the ownership conflict in favour of
  the repository.
- With each Unit pointing to its milestone and every request not yet started kept as a draft, Backlog becomes a
  procedure an agent can run, and `spec-next` can recommend the next work instead of stopping at "Idle".
- A GitHub issue, when there is one, is linked from the Unit rather than kept in sync, so work without GitHub keeps
  working and no third copy of the plan appears.
- **Test**: the review signal of `PADR-milestone-documents` (three milestones closed or 2027-01-31) checks whether
  milestones were used and the recommendation helped; unused parts are proposed for removal.

## 2. Decisions

Settled in Planning; each links its preliminary decision. Planning ran at `high` effort from the challenger review on
(`envelopes/challenger-01.yaml`).

| # | Question | Decision | Record |
| :--- | :--- | :--- | :--- |
| D1 | Where the roadmap lives | The repository. GitHub is an optional intake, autohub is not an owner | `PADR-roadmap-in-repository` |
| D2 | The form of a milestone | A document kind, `MS-<slug>` under `docs/roadmap/`, status `planned`/`active`/`done`/`dropped`; finished ones stay as hidden history; global only | `PADR-milestone-documents` |
| D3 | Goals | Stay as prose in `ARCH-01-introduction-and-goals`; a milestone cites it. No goal IDs | `PADR-roadmap-in-repository` |
| D4 | Order of milestones | `depends_on`, declared by the successor, a start condition checked at the Backlog decision points (activate, close, drop), never refused | `PADR-milestone-documents` |
| D5 | Requests not yet started | Always a draft proposal; a decomposition yields drafts only, linked by `decomposed_from` and carried to `spec.md` with `supersedes`; small drafts run Planning at `low` | `PADR-roadmap-in-repository` |
| D6 | GitHub link | Optional `issue` number of an inbound request, carried on handoff; closed when its last linked Unit merges; never an autohub record issue; no sync | `PADR-issue-link-only` |
| D7 | Choosing the next work | When no Unit is in progress, `spec-next` recommends Planning-eligible drafts: `critical` first, then by milestone rank, `priority`, `size`, `created_at`, ID; no CLI sorting | `PADR-milestone-documents` |
| D8 | Scope | Milestone kind and checks, Unit links, the Backlog procedure, next-work recommendation; see 3.1 for what is left out | This section |

## 3. Proposed Design & Impact

| Fact | Owner | Read by |
| :--- | :--- | :--- |
| Mission, goals, success criteria | `ARCH-01-introduction-and-goals` | Planning, Backlog, milestone documents |
| Milestone: goal, exit condition, status, `depends_on` | `docs/roadmap/MS-<slug>.md` | Backlog, `spec-next` |
| Request not yet started | Draft proposal (`decomposed_from` when split) | Backlog, `spec-next` |
| Unit ↔ milestone | `milestone: MS-<slug>` in `proposal.md` and `spec.md`, carried on handoff | Every activity, offline |
| Unit ↔ inbound request | Optional `issue: <n>` in `proposal.md` and `spec.md`, carried on handoff | Backlog, `spec-integrate` |
| Priority, size | Proposal frontmatter (existing fields) | Backlog, `spec-next` |
| Follow-ups found during work | Open feedback (existing), promoted to drafts by Backlog | Backlog hygiene |

- **Document model**: kind `milestone`, prefix `MS`, location `docs/roadmap/`; `milestone` becomes a single-ID
  relation field; `depends_on` a list of `MS-` IDs on milestones only; `done` and `dropped` milestones are historical.
- **Commands**: `devkit spec proposal new` and `devkit spec new` take `--milestone MS-<slug>` and `--issue <n>`;
  `proposal new` takes `--decomposed-from PROP-<slug>`; the handoff carries `issue` as it does `milestone`, and
  `decomposed_from` and `supersedes` as provenance fields.
  `devkit spec list` is unchanged apart from listing the new kind.
- **Checks**: `RULE-spec-format` and `RULE-document-summary` cover milestones; a `depends_on` cycle is a
  `RULE-document-reference` error; two hygiene warnings (unsettled members of a `done` or `dropped` milestone)
  through the `devkit.hygiene` extension; dependencies and members are otherwise checked at the Backlog decision
  points (`PADR-milestone-documents`).
- **Guidance**: the `spec` skill's classification reference gains the Backlog procedure (drain open issues no Unit links,
  place work in a milestone, decompose into drafts, activate, close and drop milestones with the user);
  `spec-next` gains the idle next-work recommendation and the roadmap review signal; `spec-integrate` writes `Closes` or `Refs`; a milestone
  template joins the bundle's templates.

### 3.1 Non-Goals

- **Scope Excluded**: a project management tool. No dates, estimates, burndown or a roadmap viewer; the primary
  consumer is an agent (`ARCH-01-introduction-and-goals` §1.3, human-oriented rendering).
- **Scope Excluded**: creating, reading or syncing GitHub issues and milestones through devkit-spec commands; the
  Backlog procedure uses `gh` directly when available.
- **Scope Excluded**: sorting or grouping in `devkit spec list` (`CAP-DOCS-document-lookup` keeps its non-goal).
- **Scope Excluded**: a direct-acceptance path for drafts that need no Planning (a draft proposal of its own), and
  the Backlog subagents (triage, decomposer).
- **Scope Excluded**: goal IDs, per-namespace roadmaps and the "candidate to close" warning (reopen conditions in the
  PADRs).
- **Scope Excluded**: autohub screens, runs and Work Plan mapping.
- **Scope Excluded**: retroactively assigning milestones or issues to completed specs.

## 4. Lifecycle & Retirement Criteria

- **Precondition of the handoff**: after `plan-accept` and before `devkit spec proposal handoff`, the Host updates
  the strategy layer (workbench): 01 §1, §5, §5.1, §5.2, §7.4, §10 and the glossary, and 02. 01 is the source of
  truth, so the package follows it, not the reverse.
- On acceptance (`plan-accept`): record `gate:plan-accept`, set `status: accepted` and merge the Planning branch;
  Development starts with `devkit spec proposal handoff backlog-roadmap-and-issues`.
- On rejection: change only `status: rejected`, with the user's reason in the commit message; a later hygiene pass
  writes the rejection ADR and deletes the proposal directory.
