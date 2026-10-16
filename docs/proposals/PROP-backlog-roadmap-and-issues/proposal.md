---
id: PROP-backlog-roadmap-and-issues
title: 'Backlog: goals, roadmap and issue tracking'
summary: Defines how Backlog keeps long-term goals and a roadmap of milestones, tracks requests as GitHub issues and links them to proposal and spec Units, so that the next work is chosen against goals rather than one Unit at a time.
status: draft                         # draft | reviewing | accepted | rejected
created_at: 2026-10-16
target_area: capabilities/delivery/
priority: high                        # critical | high | medium | low
size: L                               # S | M | L | XL
boundaries:
  owns:
    - capabilities/delivery/
  excludes:
    - docs/decisions/
task_kind: feature                    # feature | bugfix: the spec follows sdd-spec-<task_kind>
workflow: sdd-proposal
workflow_hash: sha256:90918c632715461d07f99f683b8381bdbe6381ad6689a7575a72c002c18c1399
---

# [PROP-backlog-roadmap-and-issues] Backlog: goals, roadmap and issue tracking

- **Parent design**: the strategy layer's master flow (workbench `docs/strategy-layer/01-master-flow.md`, §5 Backlog),
  which is the source of truth for the activity model. Its §5 lists as TODO: the issue management procedure, the
  Backlog subagent set (scout, challenger, triage, decomposer) and the issue ↔ Unit link rule.
- **Related**: `ADR-task-kind-and-planning-depth` (Backlog classifies), `CAP-DLV-proposal-incubation` (the `priority`,
  `size` and `milestone` fields), `ARCH-01-introduction-and-goals` (mission and goals).

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
  of the current drafts sets it. The strategy layer's glossary says a Phase is one GitHub milestone, which nothing in
  the package uses.
- **`priority` and `size` are recorded, not used.** `devkit spec list proposal` neither sorts nor groups by them, and
  the `spec-next` decision matrix ends at "Idle: ready for a new request". Choosing the next work is left to whoever
  remembers the context.
- **Goals and work are not linked.** `ARCH-01-introduction-and-goals` lists five goals with success criteria, but no
  proposal or spec says which goal it serves, so "how far is goal 4" cannot be answered from the repository.
- **The link to the original request is undefined.** Decomposition (01 §5.2) and close by supersede (01 §7.4) rely on
  "the GitHub issue's parent/child relation" to keep the link to the original request, while the issue ↔ Unit rule is
  still TODO.

### 1.2 Hypothesis

- Splitting the plan by stability gives each fact one owner: slow-moving **goals** stay in the repository next to the
  contract they shape, the changing **roadmap** (milestones, their order and the open requests) lives in GitHub issues
  and milestones, and each **Unit** points to its issue and milestone.
- With that link in place, Backlog becomes a procedure an agent can run: triage new requests into issues, place them
  in a milestone, classify, and recommend the next work by milestone and priority instead of waiting idle.
- The repository stays the agent's starting point: every link an agent needs to orient is in frontmatter it can read
  offline; GitHub is consulted only when Backlog work runs.

## 2. Technical Spike Questions

- **Q1. Where the roadmap lives.** Compare (a) a roadmap document in the Living Spec, (b) GitHub milestones only, as
  the strategy layer's glossary implies, and (c) the split of 1.2 (goals in the repository, milestones and issues in
  GitHub). The Living Spec describes the current state (`living-spec-writing`); a roadmap is future intent, which
  argues against (a). Against (b) and (c): consumers without GitHub, and agents working offline. Decide the owner of
  each fact (goal, milestone, its order and exit condition, issue, priority).
- **Q2. Goal records.** Whether `ARCH-01-introduction-and-goals` §1.2 stays the goal list with stable goal IDs, or goals
  become their own document kind, and whether a proposal or milestone references a goal.
- **Q3. Issue ↔ Unit link.** The field (for example `issue: <number>` in `proposal.md`, carried to `spec.md` on
  handoff), the link for `session` depth (the PR body only, no Unit), when an issue is required (every request, or
  only Unit depths), and how parent/child issues express a decomposition and a supersede.
- **Q4. Milestone validity.** Whether `milestone` must name an existing GitHub milestone, and where that is checked:
  rules run offline and deterministically, so a GitHub lookup fits a hygiene warning or a Backlog command better than
  a rule.
- **Q5. Choosing the next work.** What `spec-next` recommends when idle (open milestone, then priority, then size?),
  and what `devkit spec list proposal` needs for it (sort and group by `priority` and `milestone`).
- **Q6. Backlog roles.** Which of the 01 §5 TODO subagents (triage, decomposer; scout and challenger exist) are needed,
  and which work stays with the Host in `direct`.
- **Q7. Package boundary.** GitHub issue and milestone access is not specific to spec-driven development: decide what
  belongs in devkit (a generic tracker interface?) and what in devkit-spec (the Unit links, the Backlog procedure), and
  how autohub's Work Item relates to an issue.
- **Q8. Decomposition of this proposal.** The scope above may not fit one spec (one proposal hands off to exactly one
  spec, 01 §5.2). If Planning finds it too large, it returns to Backlog with `needs_decompose: true`; likely parts are
  the link model (Q1–Q4), next-work selection (Q5) and the Backlog procedure (Q6).

## 3. Proposed Design & Impact

A working direction for Planning to test, assuming option (c) of Q1:

| Fact | Owner | Read by |
| :--- | :--- | :--- |
| Mission, goals, success criteria | Repository (`ARCH-01-introduction-and-goals` or a goal document, Q2) | Planning, Backlog |
| Milestone: name, order, exit condition | GitHub milestone (title and description) | Backlog, `spec-next` |
| Request | GitHub issue (parent/child for decomposition) | Backlog |
| Unit ↔ issue, Unit ↔ milestone | Unit frontmatter (`issue`, `milestone`), carried on handoff | Every activity, offline |
| Priority, size | Proposal frontmatter (existing fields) | Backlog, `spec-next` |

- **Backlog procedure** (in the `spec` skill's classification reference, after the strategy layer's §5 is updated):
  register or find the issue, place it in a milestone, classify, add the draft with `--issue` and `--milestone`, and
  for a split create child issues and drafts.
- **Next-work selection**: `spec-next` adds an idle row that recommends a draft from the earliest open milestone by
  priority; `devkit spec list proposal` gains sorting and grouping on frontmatter fields.
- **Closing the loop**: merging the dev PR closes the issue (`Closes #<n>` in the PR body written by `spec-integrate`);
  a milestone whose issues are all closed is reported to the user, who decides whether its exit condition holds. The
  periodic reconciliation sweep (`PROP-periodic-drift-reconciliation`) is a candidate milestone-close activity.

### 3.1 Non-Goals

- **Scope Excluded**: a project management tool. No dates, estimates, burndown or a roadmap viewer; the primary
  consumer is an agent (`ARCH-01-introduction-and-goals` §1.3, human-oriented rendering).
- **Scope Excluded**: issue trackers other than GitHub. The design keeps the tracker behind one boundary (Q7) but
  implements GitHub only.
- **Scope Excluded**: autohub screens and runs. autohub follows once the contract is settled.
- **Scope Excluded**: retroactively creating issues for completed specs.

## 4. Lifecycle & Retirement Criteria

- **Order of change**: the strategy layer's 01 is the source of truth. On acceptance, its §5 (and the glossary entries
  for Backlog and Phase) is updated first in workbench; this package then follows.
- Preliminary decisions: a PADR for the owner of each planning fact (Q1) and one for the issue ↔ Unit link (Q3).
- Research: a short survey of how comparable spec-driven toolkits keep roadmaps goes to `materials/` if Q1 needs it.
- On acceptance (`plan-accept`): record `gate:plan-accept`, set `status: accepted` and merge the Planning branch;
  Development starts with `devkit spec proposal handoff backlog-roadmap-and-issues`.
- On rejection: change only `status: rejected`, with the user's reason in the commit message; a later hygiene pass
  writes the rejection ADR and deletes the proposal directory.
