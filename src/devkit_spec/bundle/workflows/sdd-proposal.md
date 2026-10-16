---
id: sdd-proposal
title: "Proposal (planning-depth proposal: plan-intent, review, plan-accept, handoff)"
status: active
schema_version: 1
# Executor-neutral stage schema: what a stage is, needs, produces and where it returns.
# Stages shared with other workflows keep the same id and the same exit, gate, role, isolation, skills and
# artifacts (`devkit workflow validate` reports SHARED_STAGE_MISMATCH); returns are this workflow's own.
# No `next` list: devkit's handoff cannot move a unit across layouts; `devkit spec proposal handoff` does.
layout:
  work_dir: docs/proposals
  unit_path: "PROP-{slug}"
  anchor: proposal.md
checks:
  - { name: exception-raised, class: human, description: "a retry cap, tool failure or unresolved semantic conflict was raised" }
  - { name: exception-handled, class: human, description: "the cause of the exception was handled by the user" }
stages:
  - id: intent-proposal
    name: Plan intent
    human_gate: plan-intent
    entry: []
    exit: [anchor-exists]
    artifacts: [docs/proposals/PROP-<slug>/proposal.md]
    skills: [spec]
    role: developer
    isolation: none
    returns: []
  - id: spike
    name: Spike (optional)
    optional: true
    human_gate: false
    entry: [anchor-exists]
    exit: []
    artifacts: [docs/proposals/PROP-<slug>/materials/]
    skills: [spec-delegate]
    role: scout
    isolation: preferred
    returns:
      - { to: intent-proposal, when: the goal itself is unclear }
  - id: direction-handoff
    name: Plan accept
    human_gate: plan-accept
    entry: [anchor-exists]
    exit: []
    artifacts: ["proposal.md with status accepted and the recorded gate:plan-accept"]
    skills: [spec]
    role: developer
    isolation: none
    returns:
      - { to: spike, when: the choice needs more evidence }
  - id: handoff
    name: Handoff
    human_gate: false
    entry: [anchor-exists]
    exit: []
    artifacts: [specs/<YYYY-MM>/<YYYYMMDD>-<slug>/ bound to sdd-spec-<task_kind>]
    skills: [spec, spec-next]
    role: developer
    isolation: none
    returns:
      - { to: direction-handoff, when: the proposal must change before it can be handed off }
  - id: exception
    name: Exception
    exception: true
    human_gate: false
    entry: [exception-raised]
    exit: [exception-handled]
    artifacts: [exception report]
    skills: [spec]
    role: developer
    isolation: none
    returns:
      - { to: handoff, when: "the stage that raised it, after the cause is handled" }
---

# Proposal (`planning-depth` proposal)

The direction must be decided first: options are explored and compared in a proposal bundle `docs/proposals/PROP-<slug>/` (anchor `proposal.md`, created in Backlog with `devkit spec proposal new <slug>`, which binds it to this workflow) before any spec exists. The criterion is what must be decided before implementation, not size. `devkit workflow next --unit docs/proposals/PROP-<slug>` names the current stage. The workflow ends at handoff: `devkit spec proposal handoff <slug>` moves the accepted proposal into a new spec bundle `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` bound to `sdd-spec-<task_kind>` (the proposal's `task_kind`, `feature` or `bugfix`, confirmed at `plan-accept`; `workflow` in `proposal.md` is this workflow's own binding), after which that workflow's stages and gates apply. A team review (a PR on the Planning branch with assigned reviewers) is this depth plus PR policy, not a separate workflow.

## Stages

The frontmatter is the only stage definition. Read it with `devkit workflow show sdd-proposal` (or `devkit workflow show --unit <dir>`). This document keeps only the rules the schema cannot express.

| proposal `status` | stage | who changes it |
| --- | --- | --- |
| `draft` | `intent-proposal` | whoever adds the draft, in any activity; `plan-intent` is the user's confirmation of the draft in Backlog |
| `reviewing` | `spike`, `direction-handoff` | the executor that starts Planning, on the `plan-<slug>` branch |
| `accepted` | `plan-accept` passed | after the user's acceptance (Host locally, autohub in `cloud-pr`) |
| `rejected` | Planning ends | the Host or autohub that received the rejection, status only |

- **Planning starts** only from a draft with `plan-intent` recorded and without `needs_decompose: true`, on its own branch `plan-<slug>`. A draft found to need splitting during Planning goes back to Backlog: set `status: draft` and `needs_decompose: true`, keep what the review learned in `materials/`, and merge the Planning branch.
- **Spike** is optional and never becomes the current stage on its own: run it when the direction needs evidence, delegating to the `scout` role (and the `challenger` role when the direction needs criticism) as the `activity-effort` of Planning asks (`low`: questions only; `medium`: when needed; `high`: two or more options compared, `challenger` required, re-review after changes). Its materials go under the proposal's `materials/` and move to `docs/materials/` at handoff.
- **Handoff** has no exit check: once `plan-accept` holds, `next` reports the unit complete (`[STAGE: - complete=true]`, no `[HANDOFF]` line). That is the cue to merge the Planning branch and, in Development on `dev-<slug>`, run `devkit spec proposal handoff <slug>` as its first step. The definition declares no `next` candidates, because devkit's `devkit workflow handoff` rebinds a unit in place and cannot move it into another layout.

## Gate rules

- `plan-intent` and `plan-accept` are the only decisions before handoff and are always a person's; they take no policy key. Everything after handoff belongs to the bound workflow, which carries both records under their own names.
- **Questions are collected in one round.** The review continues past the first question; only the parts that depend on an answer stay open. A question carries a recommended option when one is clear, else several options with one recommended. Answers are rewritten to one choice and one decision sentence per question, never the raw conversation, and an answer that leaves something ambiguous is asked again rather than guessed.
- **`plan-accept` is the acceptance of the direction** and also the approval to merge the Planning branch. The acceptance request shows the proposal's change summary and the list of decisions made in this Planning. Under `ask` (the only value) the gate passes with `devkit workflow answer --unit <dir> --request gate:plan-accept --action accept --by user`, written only after the user's explicit acceptance, together with `status: accepted` in the same commit.
- **Rejection changes the status only.** The executor that received it sets `status: rejected` and puts the user's reason, unrewritten, in the commit message (and in the final merge commit when commits are squashed), then merges per policy. No worker runs, no ADR is written and the proposal is not deleted at that point; a later hygiene pass by the Host writes the rejection ADR outside the proposal directory, referencing the proposal and the rejection commit, and deletes the proposal in the same commit. A `rejected` proposal is never resumed, accepted or started.
- Scout and Challenger are optional support roles; zero findings is a valid spike result.

## Project policy execution

Read `devkit spec policy` before Planning: stage switches come from `[workflow.stages]`, and whether a `direct`-mode Planning branch runs in a separate worktree from `[tool.spec] worktree`; `local-orchestrated` always uses one, `cloud-pr` uses the runner's checkout. `plan-intent` and `plan-accept` always need the user and `exception` always needs resolution. Explicit user authority, required worktree and PR policy, external protections and action permissions remain applicable.
