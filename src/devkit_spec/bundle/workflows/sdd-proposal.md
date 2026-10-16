---
id: sdd-proposal
title: "Proposal (planning-depth proposal: plan-intent, review, plan-accept, handoff)"
status: active
schema_version: 1
gates:
  plan-intent: { policies: [ask] }  # always a person (01 §3); configuration cannot pass it
  plan-accept: { policies: [ask] }  # always a person (01 §3)
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
  - id: collect-feedback
    name: Collect feedback
    human_gate: false
    entry: [anchor-exists]
    exit: [envelope-check-pass(feedback swept)]
    artifacts: [feedback/*.md, envelopes/feedback-NN.yaml]
    skills: [spec-feedback]
    role: developer
    isolation: none
    returns: []
  - id: direction-handoff
    name: Plan accept
    human_gate: plan-accept
    entry: [anchor-exists]
    # Asked only for a proposal in review: never for a draft, nor again for a rejected one (01 §4.4, §6.2). For a
    # rejected proposal this exit stays unmet for good: Planning has ended, and the proposal waits for hygiene.
    exit: [frontmatter(proposal.md status reviewing|accepted)]
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
    # No return to direction-handoff: Development never returns to Planning (01 §4.7). A premise of the accepted
    # proposal that no longer holds is a problem, then a close (01 §7.3, §7.4), never a change of the proposal.
    returns: []
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
| `reviewing` | `spike`, `collect-feedback`, `direction-handoff` | the executor that starts Planning, on the `plan-<slug>` branch |
| `accepted` | `plan-accept` passed | after the user's acceptance (Host locally, autohub in `cloud-pr`) |
| `rejected` | Planning ends | the Host or autohub that received the rejection, status only |

- **Planning starts** only from a draft with `plan-intent` recorded and without `needs_decompose: true`, on its own branch `plan-<slug>`. A draft found to need splitting during Planning goes back to Backlog: set `status: draft` and `needs_decompose: true`, keep what the review learned in `materials/`, close every question still open with an `answer` envelope (`choice: null`, the return to Backlog as the decision), and merge the Planning branch.
- **Spike** never becomes the current stage on its own: run it whenever the `activity-effort` of Planning requires a `challenger` and when the direction needs evidence (the `scout` role). The effort decides the `challenger` (`low`: questions only; `medium`: one `challenger` pass always; `high`: two or more options compared, `challenger` required, re-review after changes). The Planning effort is proposed with `plan-intent`. Its materials go under the proposal's `materials/` and move to `docs/materials/` at handoff.
- **Handoff** has no exit check: once `plan-accept` holds, `next` reports the unit complete (`[STAGE: - complete=true]`, no `[HANDOFF]` line). That is the cue to merge the Planning branch and, in Development on `dev-<slug>` (a worktree or the base checkout switched with `--no-worktree`; anywhere else the handoff is refused, `SPEC_PROPOSAL_WRONG_WORKTREE`), run `devkit spec proposal handoff <slug>` as its first step. The definition declares no `next` candidates, because devkit's `devkit workflow handoff` rebinds a unit in place and cannot move it into another layout.

## Gate rules

- `plan-intent` and `plan-accept` are the only decisions before handoff and are always a person's; their only accepted policy is `ask` (`gates.<gate>.policies`). Everything after handoff belongs to the bound workflow, which carries both records under their own names.
- **Questions are collected in one round.** The review continues past the first question; only the parts that depend on an answer stay open. A question carries a recommended option when one is clear, else several options with one recommended. The questions go into the run's `worker` envelope (`questions`, status `needs_input`); the gates from that run's stage on (here `plan-accept`) and the Planning branch's merge wait until an `answer` envelope answers each (`[PENDING_QUESTION]`); `plan-intent`, passed before, stays passed. Answers are rewritten to one choice and one decision sentence per question, never the raw conversation, recorded first as an `answer` envelope naming that `worker` envelope (the `spec` skill's `references/worker-records.md`), and an answer that leaves something ambiguous is asked again rather than guessed.
- **`plan-accept` is the acceptance of the direction** and also the approval to merge the Planning branch. Ask and record it only for a proposal in review (`status: reviewing`): never for a `draft` (Planning has not started) or a `rejected` one (its Planning has ended). Record it on the proposal's `plan-<slug>` branch, in the Planning's own checkout, never on the base. The acceptance request shows the proposal's change summary, the list of decisions made in this Planning, and the effort record: the `activity-effort` of each Planning run (its `worker` envelope) and the support-role envelopes present (`challenger`, `scout`, or none, from `devkit workflow envelope check --unit <dir>`). When a run's effort required a `challenger` that left no envelope, the request names the gap; the user may send the proposal back to `spike`. Under `ask` (the only value) the gate passes with `devkit workflow answer --unit <dir> --request gate:plan-accept --action accept --by user`, written only after the user's explicit acceptance, together with `status: accepted` in the same commit.
- **Rejection changes the status only.** The executor that received it sets `status: rejected` and puts the user's reason, unrewritten, in the commit message (and in the final merge commit when commits are squashed), then merges per policy. Questions still open from the last run are closed in the same commit with an `answer` envelope giving each `choice: null` and the rejection as its decision, so they do not hold the merge. No worker runs, no ADR is written and the proposal is not deleted at that point; a later hygiene pass by the Host writes the rejection ADR outside the proposal directory, referencing the proposal and the rejection commit, and deletes the proposal in the same commit. A `rejected` proposal is never resumed, accepted or started: never answer its `plan-accept`, the attach check refuses to continue its branches, and `devkit rules check -p hygiene` lists it (`SPEC_PROPOSAL_REJECTED_PENDING`) until the cleanup. `devkit workflow next` may show unmet `collect-feedback` or `direction-handoff` checks for `status=rejected`: Planning has ended; never start another sweep or set it back to `reviewing`.
- Scout is an optional support role; Challenger is optional only at `low` effort. Zero findings is a valid spike result.

## Project policy execution

Read `devkit spec policy` before Planning: stage switches come from `[workflow.stages]`, and whether a `direct`-mode Planning branch runs in a separate worktree from `[tool.spec] worktree`; `local-orchestrated` always uses one, `cloud-pr` uses the runner's checkout. `plan-intent` and `plan-accept` always need the user and `exception` always needs resolution. Explicit user authority, required worktree and PR policy, external protections and action permissions remain applicable.


## Planning feedback

Each Planning run records concrete observations under its own proposal's `feedback/` before its last work commit
when `capture=observed`, including runs ending with questions or a problem. Before every return to the user, run
the enabled `collect-feedback` sweep for this run and committed accumulated records, then write the single
`worker` envelope. Each run writes new sweep evidence; an older PASS is not coverage of a later run. A gap is
recorded as FAIL and remains visible. Stage-off skips only sweep/evidence, not observed capture; requested-only writes
policy-skip PASS without observations. Explicit requested sweeps retain their no-envelope override.

Rejection uses the last run's recorded coverage or declared skip/gap, starts no worker or Cloud Agent, and claims no
fresh sweep of a later conversation. Before any run there are no run observations. Keep rejected/decomposition-return
feedback with its proposal; before deleting it, the Host follows the `spec` skill's
`references/feedback-retirement.md`. At handoff open files move into the spec feedback directory, settled files
follow preserved materials, and Planning envelopes are dropped. Development supplies its own sweep.
