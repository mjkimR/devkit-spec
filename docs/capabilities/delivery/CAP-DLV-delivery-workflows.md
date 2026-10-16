---
id: CAP-DLV-delivery-workflows
title: Delivery Workflows
summary: The five delivery workflows the spec bundle ships as devkit workflow definitions, one per planning-depth and task-kind, with their stages, the plan-intent, plan-accept and dev-integration gates, exit checks, envelopes and the roles they delegate to.
area: delivery
status: active
created_at: 2026-10-13
stories:
  - US-route-development-intent
  - US-incubate-and-hand-off-a-proposal
entrypoints:
  - src/devkit_spec/bundle/workflows/
  - src/devkit_spec/bundle/subagents/
---

# [CAP-DLV-delivery-workflows] Delivery Workflows

## 1. Summary

The `spec` bundle ships one devkit workflow definition per combination of `planning-depth` and `task-kind`
(`kind = "workflow"` assets in `src/devkit_spec/bundle/workflows/`) and six host-neutral role contracts
(`kind = "subagent"` assets in `src/devkit_spec/bundle/subagents/`), all in the `core` preset. devkit's workflow engine
evaluates the definitions ([Workflow Engine](https://github.com/mjkimR/devkit/blob/main/docs/workflow/overview.md));
`devkit sync` projects the roles into each agent host's subagent directory
([Agent Projections](https://github.com/mjkimR/devkit/blob/main/docs/distribution/agent-projections.md)). The
definitions are the only source of stage order, checks, gates and returns: an executor reads them, never an ad-hoc
sequence.

## 2. Scope & Boundary

- **In-Scope**: the five definitions (layout, anchor, stages, gates, entry and exit checks, returns, declared checks),
  the gate semantics of `plan-intent`, `plan-accept`, `dev-integration` and the `exception` stage, the envelope kinds
  the stages require, the `activity-effort` rules of review and reconcile, and the six role contracts.
- **Out-of-Scope**:
  - Evaluating a definition, recording answers and envelopes, binding units: devkit's `devkit workflow` commands.
  - Creating and binding a spec bundle: `CAP-DLV-spec-bundles`.
  - Creating a proposal and the cross-layout handoff: `CAP-DLV-proposal-incubation`.
  - The effective approval, stage, Git and routing policy: `CAP-DLV-project-policy`.
  - The procedures a stage names (the `spec*` skills), classification, Backlog, depth changes and closes:
    `CAP-HARN-agent-guidance`.
- **Non-Goals**:
  - **Scope Excluded**: conditional stages. Each classification is one workflow; a change of depth adds a Unit or
    closes the work, never a stage switched on by content.
  - **Scope Excluded**: a Development direction gate. Choices inside the agreed intent are the executor's; a problem
    that breaks the agreement stops the work as a problem.
  - **Scope Excluded**: a runner. Dispatching stages, the integration queue, the shared-docs write lock, retry caps,
    executing merges and declaring `lint-ci-clean` and `merged` belong to an external runner, or to the executor
    declaring them with `--given` when none exists.
  - **Scope Excluded**: model selection. Model and reasoning effort are the runtime's settings; `activity-effort`
    sets only how thorough an activity's review and verification are.

## 3. Business Rules & Policies

1. **One definition per classification**: the workflow id is `sdd-<planning-depth>[-<task-kind>]`. `session` uses
   `sdd-session-feature` or `sdd-session-bugfix`, `spec` uses `sdd-spec-feature` or `sdd-spec-bugfix`, `proposal` uses
   `sdd-proposal` until handoff and then `sdd-spec-<task_kind>`. A team review is `proposal` depth plus PR policy, not
   a workflow. The axes are not stored as fields: the Unit's kind and the bound workflow show them.
2. **Definitions are authoritative**: an executor MUST take stage order, checks, gates and returns from
   `devkit workflow show <id>` / `devkit workflow show --unit <dir>` and `devkit workflow next --unit <dir>`. The
   Markdown body of a definition keeps only rules the schema cannot express.
3. **Shared stages are identical**: a stage id used by several definitions MUST have the same exit checks, gate,
   role, isolation, skills and artifacts in each; `devkit workflow validate` with no arguments reports a difference
   as `SHARED_STAGE_MISMATCH`. Returns are each workflow's own.
4. **Gates are named `<activity>-<decision>`**: `plan-intent`, `plan-accept` and `dev-integration`; the `exception`
   stage belongs to no activity. Numbered gate names are not used.
5. **Approval is never inferred**: `plan-intent` and `plan-accept` pass only with a decision recorded by
   `devkit workflow answer --unit <dir> --request gate:<gate> --action accept|decline --by user`, written only after
   the user's explicit answer; their only accepted policy is `ask`. The record names the authority and carries no conversation:
   no quotes, paraphrase or dates of it; a decline note states the reason as a decision. `dev-integration` passes
   only with `--given dev-integration`, passed to each `devkit workflow next` after the user's explicit OK and never
   recorded, or with the PR ready state a runner binds (`ADR-integration-approval-asserted`); under `auto` it passes by
   policy (`[GATE_PASSED: dev-integration ... source=policy]`, JSON `passed_gates`) and the executor MUST report the
   delegation as the authority, never as a human approval.
   None grants new commit, merge, publication or deletion authority. `devkit workflow return --unit <dir> --to
   <stage>` voids the approvals of that stage and later ones, and the envelopes recorded for them before the return.
6. **`plan-intent` opens every task**: goal, scope, verification (for a bugfix, the expected behavior), `task-kind`
   and `planning-depth` are confirmed by the user. For `spec` depth the gate opens once the anchor exists and is
   recorded in inline Planning; for `proposal` depth it is the user's confirmation of the draft in Backlog; a spec
   handed off from a proposal carries the proposal's `gate:plan-intent` and `gate:plan-accept` records under the same
   names (`CAP-DLV-proposal-incubation`).
7. **No Development direction gate**: Development starts from the agreed intent. Implementation choices inside it
   are made with the recommended option and recorded; a non-blocking improvement is reported as feedback (a
   follow-up draft proposal is also allowed); only a problem that cannot be solved without changing the agreed goal,
   scope or contract stops the work. A worker records it and ends; the Host decides recovery or a close. There is no
   return from Development to Planning.
8. **`dev-integration` is per integration unit** (one pull request): it has no exit checks of its own and is asked as
   soon as `integration-approval` is current, that is once the final change report holds. Under `auto` it passes only
   after the path's required review, reconciliation and checks pass, at every `activity-effort`, `low` included.
   Docs reflection and conflict resolution within the approved intent need no re-approval.
9. **Living Spec before `dev-integration`**: the Living Spec reflection, a resolved `reconcile.md` and
   `status: completed` of the anchor MUST be complete before the gate; an optional review feedback breakpoint between
   `review-refine` and `living-spec-draft` adds no stage, check or approval file.
10. **Integration is a stage, not a persona**: its code authority is limited to conflict resolution and the
    verification that needs; its docs authority is the reflection the approved change requires. It re-verifies only
    what conflict resolution and docs reflection changed and does not restart code review.
11. **Exception stage**: every workflow has the out-of-band `exception` stage, entered on `exception-raised` and left
    on `exception-handled`, both `human` checks, without a gate. It distinguishes three failure kinds: retry cap
    exceeded, execution or tool failure, unresolved semantic conflict. A problem the Host handles itself never goes
    through it.
12. **Bugfix evidence order**: a reproduction precedes the fix. In `sdd-spec-bugfix` a `red` envelope
    (`checks.reproduced`) precedes a `green` envelope (`checks.resolved`, `checks.preserved`); in `sdd-session-bugfix`
    a failing reproduction test (`reproduce-session`) precedes the fix and the Red then Green evidence is in the
    session report. A compile, environment or test-setup failure unrelated to the defect is not reproduction evidence.
13. **A session has no unit and no artifacts**: `sdd-session-*` declare no layout and no stage or exit check that
    requires a Unit, envelope, spec, reconcile document or gate record file, at every `activity-effort`. They are not
    evaluated by `devkit workflow next`; the executor follows their stages from `devkit workflow show <id>` and reports
    the change, effort, review result, verification and remaining constraints in the final response or PR body. A
    lasting design record, contract change or Living Spec change raises the depth to `spec`.
14. **Proposal Planning ends at handoff** (`CAP-DLV-proposal-incubation`): `sdd-proposal` declares no `next`
    candidates, because devkit's `devkit workflow handoff` rebinds a unit in place and refuses a candidate with
    another anchor (`HANDOFF_LAYOUT_MISMATCH`). Once `plan-accept` holds, `next` reports the unit complete
    (`[STAGE: - complete=true]`, no `[HANDOFF]` line) and Development starts with `devkit spec proposal handoff <slug>`.
15. **`activity-effort` sets the review, never the floor**: Development of a spec unit reviews at `low` by the author
    (stated as self-review in the envelope), at `medium` with one `reviewer` pass plus reverification of fixes (the
    reviewer also checks the reconcile result), at `high` with a re-review after fixes and a separate `reconciler`
    verification. The implementer always writes the Living Spec reflection and resolves `reconcile.md`; the
    verification at every effort is a `reconcile-check` envelope the `living-spec-draft` exit reads, so its findings
    are fixed in the reconcile and never reopen `review-refine`. A session
    reviews at the same levels but its reviewer returns a message and nothing is written. Gates, exit checks and
    `required` policies hold at every effort.
16. **Only the workers write to Git**: a read-only role never stages or commits (`x-git-actions: [read]`). The two
    workers (`[read, commit]`) commit on their activity branch, write their own records and never push, merge, rebase,
    reset or amend (`ADR-worker-delivers-committed-result`).

## 4. Interfaces & Data Contracts

### 4.1 Workflow Catalog

| Workflow | Classification | Layout (`work_dir` / `unit_path`) | Anchor | Gates |
| --- | --- | --- | --- | --- |
| `sdd-session-feature` | `session` × `feature` | none | none | `plan-intent`, `dev-integration` |
| `sdd-session-bugfix` | `session` × `bugfix` | none | none | `plan-intent`, `dev-integration` |
| `sdd-spec-feature` | `spec` × `feature` | `specs` / `{date:%Y-%m}/{date:%Y%m%d}-{slug}` | `spec.md` | `plan-intent`, `dev-integration` |
| `sdd-spec-bugfix` | `spec` × `bugfix` | `specs` / `{date:%Y-%m}/{date:%Y%m%d}-{slug}` | `spec.md` | `plan-intent`, `dev-integration` |
| `sdd-proposal` | `proposal` (either kind) | `docs/proposals` / `PROP-{slug}` | `proposal.md` | `plan-intent`, `plan-accept` |

Each definition with a unit sets its own `layout`, so spec bundles and proposal bundles live where the document model
expects them and `devkit workflow list` finds both. `schema_version` is `1` in every definition.

### 4.2 Stages

`devkit workflow show <id>` is the authoritative list; in order (gate in parentheses):

- **`sdd-session-feature`**: `intent-session` (`plan-intent`), `execute-verify`, `report-session`, `approval-session`
  (`dev-integration`), `commit-session` (exit `lint-ci-clean`), `merge` (exit `merged`).
- **`sdd-session-bugfix`**: `intent-session`, `reproduce-session`, then the stages of `sdd-session-feature` from
  `execute-verify` on.
- **`sdd-spec-feature`**: `intent` (`plan-intent`), `specify`, `build-verify`, `review-refine`, `living-spec-draft`,
  `collect-feedback`, `final-change-report`, `integration-approval` (`dev-integration`), `integrate`, `merge`.
- **`sdd-spec-bugfix`**: `intent` (`plan-intent`), `characterize`, `plan-tasks`, `reproduce`, `fix-verify`, then the
  stages of `sdd-spec-feature` from `review-refine` on.
- **`sdd-proposal`**: `intent-proposal` (`plan-intent`), `spike` (optional; never current on its own),
  `direction-handoff` (`plan-accept`), `handoff` (no exit check).

Every workflow also has `exception`. Stage details of the spec-bundle workflows:

| Stage | Entry | Exit | Role / isolation | Skills |
| --- | --- | --- | --- | --- |
| `intent` | | `anchor-exists` | developer / none | `spec` |
| `specify` | `anchor-exists` | `file-exists(plan.md)`, `tasks-exists`, `not-skeleton(spec.md)`, `not-skeleton(plan.md)`, `not-skeleton(tasks.md)`, `lint-clean` | developer / none | `spec-specify`, `spec-plan`, `spec-tasks` |
| `characterize` (bugfix) | `anchor-exists` | `not-skeleton(spec.md)`, `lint-clean` | developer / none | `spec-specify` |
| `plan-tasks` (bugfix) | `not-skeleton(spec.md)` | `file-exists(plan.md)`, `tasks-exists`, `not-skeleton(plan.md)`, `not-skeleton(tasks.md)`, `lint-clean` | developer / none | `spec-plan`, `spec-tasks` |
| `reproduce` (bugfix) | `tasks-exists` | `envelope-check-pass(red reproduced)` | developer / none | `spec-specify` |
| `fix-verify` (bugfix) | `envelope-check-pass(red reproduced)` | `tasks-all-checked`, `envelope-check-pass(green resolved)`, `envelope-check-pass(green preserved)`, `lint-clean` | developer / none | |
| `build-verify` | `tasks-exists` | `tasks-all-checked`, `lint-clean` | developer / none | |
| `review-refine` | `tasks-all-checked` | `envelope-review-passed` | reviewer / preferred | `spec-review`, `spec-delegate` |
| `living-spec-draft` | `envelope-review-passed` | `frontmatter(reconcile.md status resolved)`, `envelope-completed(reconcile-check)`, `anchor-status-completed` | reconciler / preferred | `spec-sync`, `spec-delegate` |
| `collect-feedback` | `frontmatter(reconcile.md status resolved)` | `envelope-check-pass(feedback swept)` | developer / none | `spec-feedback` |
| `final-change-report` | `envelope-check-pass(feedback swept)` | `envelope-check-pass(final-report tests)`, `envelope-check-pass(final-report build)`, `envelope-check-pass(final-report lint)` | developer / none | `spec` |
| `integration-approval` | the three final-report checks | none | developer / none | `spec` |
| `integrate` | the three final-report checks | `frontmatter(reconcile.md status resolved)`, `anchor-status-completed`, `lint-ci-clean` | developer / none | `spec-integrate` |
| `merge` | `lint-ci-clean` | `merged` | `-` / none | |
| `exception` | `exception-raised` | `exception-handled` | developer / none | `spec` |

The `spike` stage of `sdd-proposal` delegates to the `scout` role (isolation `preferred`, skill `spec-delegate`) and
writes into the proposal's `materials/`. The `report-session` stage of a session runs `spec-review` and, unless
`collect-feedback` is switched off, `spec-feedback`; it runs no `spec-sync`, because a session has no reconcile record.

### 4.3 Gates

| Gate | Stage(s) | Approval key (`[workflow.approvals]`) |
| --- | --- | --- |
| `plan-intent` | `intent`, `intent-session`, `intent-proposal` | none: always the user's |
| `plan-accept` | `direction-handoff` | none: always the user's |
| `dev-integration` | `integration-approval`, `approval-session` | `dev-integration` (`ask` or `auto`) |

- A gate waiting for the user: `devkit workflow next` prints `[WAITING: human gate:<gate>]` with a
  `[REQUEST: id=gate:<gate> ...]`. A `plan-intent` or `plan-accept` answer is `devkit workflow answer --unit <dir>
  --request gate:<gate> --action accept --by user` (or `--action decline --by user --note "<reason>"`). A
  `dev-integration` OK is `--given dev-integration` on every later `next`, and an objection about the change takes the
  stage's return path; where a runner binds `gate:dev-integration` to PR state, the PR ready state answers it. Every
  definition with that gate declares `gates: {dev-integration: {answer: given}}`, so `next` ends its `[REQUEST]` with
  `answer=given`.
- `dev-integration = "auto"`: the gate passes by policy; its stage never stays current, so `next` lists it as
  `[GATE_PASSED: dev-integration stage=integration-approval policy=auto source=policy]` (JSON `passed_gates`), the basis
  every report cites.
- `--given <gate>` asserts a gate for one run (a runner's binding).
- The workflow definitions fix the policies each gate accepts (`gates.<gate>.policies`): `plan-intent` and
  `plan-accept` take only `ask`, `dev-integration` takes `ask` or `auto`. A configured policy outside them stops every
  devkit command that evaluates the unit with `WORKFLOW_GATE_POLICY`, and `devkit spec policy` reports the same rule
  (`CAP-DLV-project-policy`).
- `plan-accept` is asked only for a proposal in review: the `direction-handoff` exit is
  `frontmatter(proposal.md status reviewing|accepted)`, so a draft or a rejected proposal gets no request.

### 4.4 Checks

| Check | Class | Meaning |
| --- | --- | --- |
| `anchor-exists` | devkit | `file-exists(spec.md)` under the spec layout, `file-exists(proposal.md)` under the proposal layout. |
| `file-exists(plan.md)` | devkit | The bundle has `plan.md`. |
| `tasks-exists`, `tasks-all-checked` | devkit | `tasks.md` exists / every task is checked. |
| `not-skeleton(<file>)` | devkit | The file no longer carries `<!-- devkit:skeleton -->` (`CAP-DLV-spec-bundles`). |
| `lint-clean` | devkit | `devkit rules` (linter phase) passes on the unit's files. |
| `frontmatter(<file> <key> <value>)` | devkit | A frontmatter value, e.g. `frontmatter(reconcile.md status resolved)`. |
| `anchor-status-completed` | devkit | The anchor has `status: completed`. |
| `envelope-review-passed` | devkit | The latest review round passed (review, then reverify). |
| `envelope-check-pass(<kind> <key>)` | devkit | The latest envelope of the kind has `checks.<key>` starting with `PASS`. |
| `lint-ci-clean` | declared `runner` | `devkit rules check --ci --base <ref>` passes on the committed head; the Developer runs it after the commit and CI re-runs it. |
| `merged` | declared `runner` | The integration unit is merged into the base branch. |
| `exception-raised`, `exception-handled` | declared `human` | A retry cap, tool failure or unresolved semantic conflict was raised / its cause was handled by the user. |

Runner checks are never evaluated by `next`; they are declared with `--given lint-ci-clean` / `--given merged` once
CI and the merge (or, without a runner, the local cumulative check) report. `revision-ancestor(red green)` is
available to a project that wants stricter bugfix ordering.

### 4.5 Envelopes

Envelopes are devkit envelope files under a unit's `envelopes/`, written with
`devkit workflow envelope new --unit <dir> --kind <kind> [--stage <id>] --summary "..." [--check <key>="PASS ..."]
[--base <ref>] [--head <sha>] [--assume ...] [--unverified ...]` and validated with
`devkit workflow envelope check --unit <dir>`; a malformed envelope never satisfies a check. A session writes none.

| Kind | File | Written by |
| --- | --- | --- |
| `review`, `reverify` | `envelopes/review-NN.yaml`, `envelopes/reverify-NN.yaml` | the reviewing executor; reverify closes the round |
| `red` | `envelopes/red-NN.yaml` (`checks.reproduced`) | the implementer |
| `green` | `envelopes/green-NN.yaml` (`checks.resolved`, `checks.preserved`) | the implementer |
| `feedback` | `envelopes/feedback-NN.yaml` (`checks.swept`) | the implementer |
| `final-report` | `envelopes/final-report-NN.yaml` (`checks.tests`, `build`, `lint`) | the implementer |
| `challenger`, `scout` | role returns | the caller, from the role's fields |
| `reconcile-check` | the reconcile verification at `living-spec-draft`, read by its exit (`envelope-completed(reconcile-check)`) | the implementer: its self-check at `low`, the reviewer's returned check at `medium`, the reconciler's at `high` |
| `worker` | one run's result, exactly one per run: the applied `activity-effort`, the run's `questions` (status `needs_input`) and its `problem` (`cause`, `attempts`, `recovery`; `failed` requires it) | the run itself: a worker, the Host in `direct`, or the Host for a range it blocks |
| `answer` | the rewritten answers to a run's questions (`answers_to: worker-NN.yaml`), one decision per question | the run that processes them, first, in a commit of its own |
| `resolution` | the fix of a run's problem (`resolves: worker-NN.yaml`, `summary`) | whoever actually fixed it, with the fix |

A unit is held while a `worker` envelope's problem has no `resolution` naming it (blocked) or a question has no
`answer` (waiting): devkit passes no gate, by any source, and `devkit worktree finish --merge` refuses the branch
(`WORKTREE_BLOCKED`); a pull request merges only while `devkit workflow envelope check --format json` reports
`"blocked": false` and no `pending_questions`. Unanswered questions are `choose` requests
(`question:worker-NN.<id>`, `answer=envelope`) that `devkit workflow answer` refuses. Formats and roles:
`ADR-run-records-and-activity-branches`.

A role returns `status` (`completed`, `needs_input`, `failed`), `summary`, `findings` (`issue`, `evidence`,
`failure_condition`, `suggested_action`), `assumptions`, `unverified_areas`, `checks` and `diff_scope`. Docs impact
has no envelope key: it lives in `reconcile.md`.

### 4.6 Role Contracts

One Markdown contract per role in devkit's
[role contract format](https://github.com/mjkimR/devkit/blob/main/docs/distribution/agent-projections.md#role-contract-format):
`role`, `title`, `description`, an optional `skill` and a `hosts` block for `claude-code`, `codex` and `antigravity`.
Extension keys devkit does not interpret: `x-execution` (`isolated`), `x-invocation` (`optional`), `x-model-profile`
(`light-medium`, `general-high`, `high-reasoning`; never a host model name) and `x-git-actions` (`[read]` for every
role but the two workers, `[read, commit]`).

| Role | Skill | Model profile | Writes | Envelope kind |
| --- | --- | --- | --- | --- |
| `challenger` | none: the procedure is in the contract | `high-reasoning` | nothing | `challenger` |
| `reconciler` | `spec-sync` | `light-medium` | nothing: it verifies the implementer's reconcile result at `high` | `reconcile-check` |
| `reviewer` | `spec-review` | `general-high` | nothing | `review`, `reverify`, `reconcile-check` at `medium`, or a message for a session |
| `scout` | none: the procedure is in the contract | `light-medium` | nothing, or the proposal's `materials/` on request | `scout` |
| `planning-worker` | none: the procedure is in the contract | `general-high` | the proposal directory in its `plan-` worktree, committed | `worker` (its own) |
| `development-worker` | none: the procedure is in the contract | `general-high` | the unit's write scope in its `dev-` worktree, committed at every stage boundary | `worker` (its own) and the stage envelopes |

The contract body is the role's prompt and holds only what the role needs: purpose, input fields, return fields,
write boundaries, failure handling and, for a role whose procedure no main session runs (`challenger`, `scout`, the
workers), the procedure itself. Caller guidance (per-role payload, host guarantees, the post-run diff comparison,
envelope recording, range validation) lives in `spec-delegate` (`SPEC-subagent-procedure-in-contract`).

The workers exist for `local-orchestrated` mode (`spec-orchestrate`, user-invoked per activity) and never for
`session` depth. Each is one-shot: it runs one turn of one activity in that activity's devkit worktree, using absolute
paths and `git -C <worktree>` because no host gives a subagent its own working directory, runs its role subagents
nested (Host → worker → role; Claude Code tool `Agent`), writes its own records, commits at every stage boundary and,
when it stops on questions or a problem, makes an emergency commit of the unfinished work with its `worker` envelope.
It never reverts, closes, raises the depth or narrows the scope. The `development-worker` runs from the stage
`devkit workflow next` names up to the final change report; the `planning-worker` takes a draft proposal toward
`plan-accept`, collecting its questions in one round. The Host validates the cumulative committed range from the
unit's last accepted head; a range it rejects is a problem in the Host's own `worker` envelope, which blocks the unit
from review and integration without discarding anything until a resolution names it
(`ADR-worker-delivers-committed-result`, `ADR-run-records-and-activity-branches`). Host statuses: Claude Code
`native`, Codex `unsupported` (the Host runs the unit itself in `direct`), Antigravity `unverified`.

Stages delegate to `reviewer` (`review-refine`), `reconciler` (`living-spec-draft`, as verifier) and `scout`
(`spike`); `challenger` has no stage and is delegated as the Planning effort asks. Implementation stages keep
`role: developer`; the orchestration mode hands their turn to a worker. `[DELEGATE: role=<role> isolation=...]` in
`next` names the role; `spec-delegate` decides between a host subagent and a main-session substitute and records the
choice. A projected role receives only the per-call payload, since the host loads the contract body as its system
prompt.

### 4.7 Executor Commands (devkit)

| Command | Use |
| --- | --- |
| `devkit workflow next --unit <dir> [--given <check>]...` | Current stage, unmet checks, `[NEXT_SKILL]`, `[WAITING]`, `[DELEGATE]`, `[SKIPPED]`. |
| `devkit workflow show <id>` / `--unit <dir>` | Render a definition. |
| `devkit workflow answer --unit <dir> --request gate:<gate> --action accept\|decline --by user` | Record a `plan-intent` or `plan-accept` decision. |
| `devkit workflow return --unit <dir> --to <stage>` | Go back within the activity; voids later approvals and earlier envelopes of those stages. |
| `devkit workflow bind --unit <dir> --workflow <id>` | Bind an unbound unit, or rebind after `WORKFLOW_DRIFT`. |
| `devkit workflow validate` | Validate definitions; `SHARED_STAGE_MISMATCH` across definitions. |
| `devkit workflow list` | List units of every layout. |
| `devkit workflow envelope new --unit <dir> --kind worker\|answer\|resolution ...` | A run's record (`--stage` and `--effort` always; `--questions-file`, `--problem`, `--tried`, `--recovery`), its answers (`--answers-to`, `--answers-file`) or a fix (`--resolves`). |
| `devkit workflow envelope check --unit <dir> [--format json]` | Malformed envelopes and the hold: `[BLOCKED]`, `[PENDING_QUESTION]`; `blocked`, `problems`, `pending_questions` in JSON. |
| `devkit worktree start <branch> [--no-worktree \| --existing-branch <branch> --unit <dir>]` | Start `plan-<slug>` or `dev-<slug>` in a worktree or the current checkout, or continue an existing branch after devkit-spec's attach check. |
| `devkit worktree stale` | Activity branches idle beyond `[worktree] stale_after`; also warned by `devkit rules check -p hygiene`. |
