---
id: PROP-backlog-roadmap-and-issues
title: 'Backlog: goals, roadmap and issue tracking'
summary: Gives Backlog a repository-owned roadmap of milestone documents ordered by depends_on, links proposal and spec Units to their milestone and optionally to a GitHub issue, and lets spec-next recommend the next work by milestone and priority.
status: reviewing                     # draft | reviewing | accepted | rejected
created_at: 2026-10-16
target_area: capabilities/delivery/
priority: high                        # critical | high | medium | low
size: M                               # S | M | L | XL
boundaries:
  owns:
    - capabilities/delivery/
    - capabilities/documents/
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
- **`priority` and `size` are recorded, not used.** `devkit spec list proposal` neither sorts nor groups by them, and
  the `spec-next` decision matrix ends at "Idle: ready for a new request".
- **Goals and work are not linked.** `ARCH-01-introduction-and-goals` lists five goals, but no proposal or spec says
  which goal it serves.
- **The link to the original request is undefined.** Decomposition (01 §5.2) and close by supersede (01 §7.4) rely on
  "the GitHub issue's parent/child relation", while the issue ↔ Unit rule is still TODO.
- **The owners disagree.** The strategy layer makes a Phase one GitHub milestone; autohub's Work Plan contract says
  repository documents own long-term direction and GitHub issues are "not a second backlog".

### 1.2 Hypothesis

- Keeping the roadmap in the repository as documents with IDs lets an agent read, validate and query it offline with
  the tools it already uses (`list`, `resolve`, `refs`, the rules), and settles the ownership conflict in favour of
  the repository.
- With each Unit pointing to its milestone, Backlog becomes a procedure an agent can run, and `spec-next` can
  recommend the next work instead of stopping at "Idle".
- A GitHub issue, when there is one, is linked from the Unit rather than kept in sync, so work without GitHub keeps
  working and no third copy of the plan appears.

## 2. Decisions

Settled in Planning; each links its preliminary decision.

| # | Question | Decision | Record |
| :--- | :--- | :--- | :--- |
| D1 | Where the roadmap lives | The repository. GitHub is an optional intake, autohub is not an owner | `PADR-roadmap-in-repository` |
| D2 | The form of a milestone | A document kind, `MS-<slug>` under `docs/roadmap/`, status `planned`/`active`/`done`/`dropped` | `PADR-milestone-documents` |
| D3 | Goals | Stay as prose in `ARCH-01-introduction-and-goals`; a milestone cites it. No goal IDs | `PADR-roadmap-in-repository` |
| D4 | Order of milestones | `depends_on`, declared by the successor, a start condition enforced by warnings only | `PADR-milestone-documents` |
| D5 | Requests not yet in a Unit | Open feedback for follow-ups found during work; a GitHub issue for requests from outside, never required | `PADR-roadmap-in-repository`, `PADR-issue-link-only` |
| D6 | GitHub link | An optional `issue` number on the Unit, carried on handoff, closed by `Closes #<n>` in the dev PR; no sync | `PADR-issue-link-only` |
| D7 | Choosing the next work | `spec-next` recommends drafts from `active`, then ready `planned` milestones, by `priority` then `size` | `PADR-milestone-documents` |
| D8 | Scope of this proposal | The milestone model, the Unit links and next-work selection; GitHub lookup commands and Backlog subagents are follow-ups | This section |

Details chosen with the recommended option, open to change at `plan-accept`: several milestones may be `active` at
once; a `depends_on` cycle is a rule error while every other milestone check is a hygiene warning; `issue` holds a
number in the repository's own GitHub repository, not a URL; units without a milestone stay valid.

## 3. Proposed Design & Impact

| Fact | Owner | Read by |
| :--- | :--- | :--- |
| Mission, goals, success criteria | `ARCH-01-introduction-and-goals` | Planning, Backlog, milestone documents |
| Milestone: goal, exit condition, status, `depends_on` | `docs/roadmap/MS-<slug>.md` | Backlog, `spec-next` |
| Unit ↔ milestone | `milestone: MS-<slug>` in `proposal.md` and `spec.md`, carried on handoff | Every activity, offline |
| Unit ↔ request | Optional `issue: <n>` in `proposal.md` and `spec.md`, carried on handoff | Backlog, `spec-integrate` |
| Priority, size | Proposal frontmatter (existing fields) | Backlog, `spec-next` |
| Follow-ups found during work | Open feedback (existing) | Backlog hygiene |

- **Document model**: kind `milestone`, prefix `MS`, location `docs/roadmap/` (and per namespace); `milestone` becomes
  a single-ID relation field; `depends_on` a list of `MS-` IDs. Existing rules validate both.
- **Commands**: `devkit spec proposal new` and `devkit spec new` take `--milestone MS-<slug>` and `--issue <n>`;
  `devkit spec list` gains sorting and grouping by frontmatter fields; the handoff carries `issue` as it does
  `milestone`.
- **Checks**: a `depends_on` cycle is a rule error; the milestone status warnings of `PADR-milestone-documents` run
  through the `devkit.hygiene` extension.
- **Guidance**: the `spec` skill's classification reference gains the Backlog procedure (place work in a milestone,
  link the issue, open and close milestones with the user); `spec-next` gains the idle next-work row; `spec-integrate`
  writes `Closes #<n>`; a milestone template joins the bundle's templates.

### 3.1 Non-Goals

- **Scope Excluded**: a project management tool. No dates, estimates, burndown or a roadmap viewer; the primary
  consumer is an agent (`ARCH-01-introduction-and-goals` §1.3, human-oriented rendering).
- **Scope Excluded**: creating, reading or syncing GitHub issues and milestones. Lookup commands, if needed later, are
  considered for devkit.
- **Scope Excluded**: Backlog subagents (triage, decomposer). Added when use of this procedure shows a need.
- **Scope Excluded**: goal IDs or a goal document kind (reopen condition in `PADR-roadmap-in-repository`).
- **Scope Excluded**: autohub screens, runs and Work Plan mapping.
- **Scope Excluded**: retroactively assigning milestones or issues to completed specs.

## 4. Lifecycle & Retirement Criteria

- **Order of change**: the strategy layer's 01 is the source of truth. On acceptance, its §1 table, §5 and the
  glossary entries for Backlog and Phase are updated first in workbench; 02 adds the milestone kind to devkit-spec's
  responsibilities. This package then follows.
- On acceptance (`plan-accept`): record `gate:plan-accept`, set `status: accepted` and merge the Planning branch;
  Development starts with `devkit spec proposal handoff backlog-roadmap-and-issues`.
- On rejection: change only `status: rejected`, with the user's reason in the commit message; a later hygiene pass
  writes the rejection ADR and deletes the proposal directory.
