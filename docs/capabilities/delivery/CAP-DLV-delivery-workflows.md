---
id: CAP-DLV-delivery-workflows
title: Delivery Workflows
summary: The four routed delivery workflows the spec bundle ships as devkit workflow definitions (s-lane, direct-delivery, bugfix, incubated-delivery), with their stages, intent/direction/integration gates, exit checks, envelopes and the optional support roles they delegate to.
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

The `spec` bundle ships one devkit workflow definition per delivery route (`kind = "workflow"` assets in
`src/devkit_spec/bundle/workflows/`) and five host-neutral role contracts (`kind = "subagent"` assets in
`src/devkit_spec/bundle/subagents/`), all in the `core` preset. devkit's workflow engine evaluates the definitions
([Workflow Engine](https://github.com/mjkimR/devkit/blob/main/docs/workflow/overview.md)); `devkit sync` projects the
roles into each agent host's subagent directory
([Agent Projections](https://github.com/mjkimR/devkit/blob/main/docs/distribution/agent-projections.md)). The
definitions are the only source of stage order, checks, gates and returns: an executor reads them, never an ad-hoc
sequence.

## 2. Scope & Boundary

- **In-Scope**: the four definitions (layout, anchor, stages, gates, entry and exit checks, returns, declared checks),
  the gate semantics of G1, G2, G3 and the exception stage E, the envelope kinds the stages require, and the five role
  contracts.
- **Out-of-Scope**:
  - Evaluating a definition, recording answers and envelopes, binding units: devkit's `devkit workflow` commands.
  - Creating and binding a spec bundle: `CAP-DLV-spec-bundles`.
  - Creating a proposal and the cross-layout handoff: `CAP-DLV-proposal-incubation`.
  - The effective approval, stage and Git policy: `CAP-DLV-project-policy`.
  - The procedures a stage names (the `spec*` skills) and route selection: `CAP-HARN-agent-guidance`.
- **Non-Goals**:
  - **Scope Excluded**: conditional stages. Each route is one workflow; a change of route is a reroute to another
    workflow, never a stage switched on by content.
  - **Scope Excluded**: a runner. Dispatching stages, the integration queue, the shared-docs write lock, retry caps,
    executing merges and declaring `lint-ci-clean` and `merged` belong to an external runner, or to the executor
    declaring them with `--given` when none exists.
  - **Scope Excluded**: a development commit mode and commit permission. Commits are plain `git commit` through
    devkit's commit gate; whether to commit is decided outside the workflow.

## 3. Business Rules & Policies

1. **One definition per route**: Route 1 MUST use `s-lane`, Route 2 `direct-delivery` (or `bugfix` for a defect with
   contract impact or uncertainty), Routes 3 and 4 `incubated-delivery` until handoff. The agreement mode of Route 3
   (local session) and Route 4 (team pull request) is the executor's binding, not a stage.
2. **Definitions are authoritative**: an executor MUST take stage order, checks, gates and returns from
   `devkit workflow show <id>` / `devkit workflow show --unit <dir>` and `devkit workflow next --unit <dir>`. The
   Markdown body of a definition keeps only rules the schema cannot express.
3. **Shared stages are identical**: a stage id used by several definitions MUST have the same exit checks, gate,
   role, isolation, skills and artifacts in each; `devkit workflow validate` with no arguments reports a difference
   as `SHARED_STAGE_MISMATCH`. Returns are each workflow's own.
4. **Approval is never inferred**: under `ask`, the `intent` and `direction` gates pass only with a decision
   recorded by `devkit workflow answer --unit <dir> --request gate:<gate> --action accept|decline --by user`, written
   only after the user's explicit answer. The record names the authority (`by: user`) and carries no conversation:
   no quotes, paraphrase or dates of it; a decline note states the reason as a decision. The `integration` gate
   passes only with `--given integration`, passed to each
   `devkit workflow next` after the user's explicit OK and never recorded, or with the PR ready state a runner binds
   (`ADR-integration-approval-asserted`). Under `auto` the gate passes by policy (`source=policy`) and the executor MUST report the
   delegation as the authority, never as a human approval. Neither grants new commit, merge, publication or deletion
   authority. `devkit workflow return --unit <dir> --to <stage>` voids the approvals of that stage and later ones,
   and the envelopes recorded for them before the return: a post-review defect needs a new review round.
5. **G1 always needs the user's intent**: goal, scope and verification are confirmed by the user; the intent gate
   opens once the anchor exists. A spec handed off from a proposal whose direction the user accepted gets its G1
   recorded from that answer (`CAP-DLV-proposal-incubation` rule 12).
6. **G2 is conditional**: it fires for uncertain choices or changes to an existing agreement, never for
   implementation or integration inside an approved scope. Under `direction = "auto"` it passes by policy, and the
   executor MUST still put a direction outside the requested scope to the user.
7. **G3 is per integration unit** (one pull request): it has no exit checks of its own and is asked as soon as
   `integration-approval` is current, that is once the final change report holds. Under `auto` it passes only after
   the required review, reconciliation and checks pass. Docs reflection and conflict resolution within the approved
   intent need no re-approval.
8. **Living Spec before G3**: the Living Spec reflection, a resolved `reconcile.md` and `status: completed` of the
   anchor MUST be complete before G3; an optional review feedback breakpoint between `review-refine` and
   `living-spec-draft` adds no stage, check or approval file.
9. **Integration is a stage, not a persona**: its code authority is limited to conflict resolution and the
   verification that needs; its docs authority is the reflection the approved change requires. It re-verifies only
   what conflict resolution and docs reflection changed and does not restart code review.
10. **Exception stage**: every workflow has the out-of-band `exception` stage (E), entered on `exception-raised` and
    left on `exception-handled`, both `human` checks. It has no gate (an exception stage is never evaluated, and a
    gate would add an `exception` approval key). E distinguishes three failure kinds: retry cap exceeded, execution or
    tool failure, unresolved semantic conflict; creating a new task to bypass a cap is not the default.
11. **Bugfix evidence order**: a `red` envelope (`checks.reproduced`) MUST precede the fix; a `green` envelope
    (`checks.resolved`, `checks.preserved`) follows it. A compile, environment or test-setup failure unrelated to the
    defect is not reproduction evidence; one non-occurrence is not resolution.
12. **S-Lane has no unit**: `s-lane` declares no layout, writes nothing under `specs/` for its decisions and is not
    evaluated by `devkit workflow next`; the executor follows its stages from `devkit workflow show s-lane`. A change
    that needs a contract or design decision MUST leave the lane (return to `intent-session` and reroute to
    `direct-delivery` or `incubated-delivery`).
13. **Incubation ends at handoff** (`CAP-DLV-proposal-incubation`): `incubated-delivery` declares no `next`
    candidates, because devkit's `devkit workflow handoff` rebinds a unit in place and refuses a candidate with
    another anchor (`HANDOFF_LAYOUT_MISMATCH`). Once the direction gate holds, `next` reports the unit complete
    (`[STAGE: - complete=true]`, no `[HANDOFF]` line) and the executor runs `devkit spec proposal handoff <slug>`,
    which records the spec's open G1 and G2 from the user's recorded direction answer and asks nothing again.
14. **Roles are optional; only the worker writes to Git**: every role MAY be replaced by the Developer running the
    procedure in the main session. A role never stages or commits (`x-git-actions: [read]`), except the `worker`
    (`[read, commit]`), which commits its complete build on its unit branch and never pushes, merges, rebases, resets
    or amends (`ADR-worker-delivers-committed-result`).

## 4. Interfaces & Data Contracts

### 4.1 Workflow Catalog

| Workflow | Route | Layout (`work_dir` / `unit_path`) | Anchor | Gates |
| --- | --- | --- | --- | --- |
| `s-lane` | 1: low uncertainty, low risk, session-contained (under 15 minutes) | none | none | `intent`, `integration` |
| `direct-delivery` | 2: low uncertainty, contract impact | `specs` / `{date:%Y-%m}/{date:%Y%m%d}-{slug}` | `spec.md` | `intent`, `direction`, `integration` |
| `bugfix` | 2 for a defect: characterize, reproduce, fix, verify | `specs` / `{date:%Y-%m}/{date:%Y%m%d}-{slug}` | `spec.md` (`kind: bugfix`) | `intent`, `direction`, `integration` |
| `incubated-delivery` | 3 (local review) and 4 (team PR review): high uncertainty | `docs/proposals` / `PROP-{slug}` | `proposal.md` | `intent`, `direction` |

Each definition sets its own `layout`, so spec bundles and proposal bundles live where the document model expects
them and `devkit workflow list` finds both. `schema_version` is `1` in every definition.

### 4.2 Stages

`devkit workflow show <id>` is the authoritative list; in order (gate in parentheses):

- **`s-lane`**: `intent-session` (G1), `execute-verify`, `report-session`, `approval-session` (G3),
  `commit-session` (exit `lint-ci-clean`), `merge` (exit `merged`).
- **`direct-delivery`**: `intent` (G1), `direction` (G2), `specify`, `build-verify`, `review-refine`,
  `living-spec-draft`, `collect-feedback`, `final-change-report`, `integration-approval` (G3), `integrate`, `merge`.
- **`bugfix`**: `intent` (G1), `characterize`, `direction` (G2), `plan-tasks`, `reproduce`, `fix-verify`, then the
  stages of `direct-delivery` from `review-refine` on.
- **`incubated-delivery`**: `intent-proposal` (G1), `spike` (optional; never current on its own),
  `direction-handoff` (G2), `handoff` (no exit check).

Every workflow also has `exception` (E). Stage details of the spec-bundle workflows:

| Stage | Entry | Exit | Role / isolation | Skills |
| --- | --- | --- | --- | --- |
| `intent` | | `anchor-exists` | developer / none | `spec` |
| `direction` | `anchor-exists` | `anchor-exists` | developer / none | `spec` |
| `specify` | `anchor-exists` | `file-exists(plan.md)`, `tasks-exists`, `not-skeleton(spec.md)`, `not-skeleton(plan.md)`, `not-skeleton(tasks.md)`, `lint-clean` | developer / none | `spec-specify`, `spec-plan`, `spec-tasks` |
| `characterize` (bugfix) | `anchor-exists` | `frontmatter(spec.md kind bugfix)`, `not-skeleton(spec.md)`, `lint-clean` | developer / none | `spec-specify` |
| `plan-tasks` (bugfix) | `frontmatter(spec.md kind bugfix)` | `file-exists(plan.md)`, `tasks-exists`, `not-skeleton(plan.md)`, `not-skeleton(tasks.md)`, `lint-clean` | developer / none | `spec-plan`, `spec-tasks` |
| `reproduce` (bugfix) | `tasks-exists` | `envelope-check-pass(red reproduced)` | developer / none | `spec-specify` |
| `fix-verify` (bugfix) | `envelope-check-pass(red reproduced)` | `tasks-all-checked`, `envelope-check-pass(green resolved)`, `envelope-check-pass(green preserved)`, `lint-clean` | developer / none | |
| `build-verify` | `tasks-exists` | `tasks-all-checked`, `lint-clean` | developer / none | |
| `review-refine` | `tasks-all-checked` | `envelope-review-passed` | reviewer / preferred | `spec-review`, `spec-delegate` |
| `living-spec-draft` | `envelope-review-passed` | `frontmatter(reconcile.md status resolved)`, `anchor-status-completed` | reconciler / preferred | `spec-sync`, `spec-delegate` |
| `collect-feedback` | `frontmatter(reconcile.md status resolved)` | `envelope-check-pass(feedback swept)` | developer / none | `spec-feedback` |
| `final-change-report` | `envelope-check-pass(feedback swept)` | `envelope-check-pass(final-report tests)`, `envelope-check-pass(final-report build)`, `envelope-check-pass(final-report lint)` | developer / none | `spec` |
| `integration-approval` | the three final-report checks | none | developer / none | `spec` |
| `integrate` | the three final-report checks | `frontmatter(reconcile.md status resolved)`, `anchor-status-completed`, `lint-ci-clean` | developer / none | `spec-integrate` |
| `merge` | `lint-ci-clean` | `merged` | `-` / none | |
| `exception` | `exception-raised` | `exception-handled` | developer / none | `spec` |

The `spike` stage of `incubated-delivery` delegates to the `scout` role (isolation `preferred`, skill
`spec-delegate`) and writes into the proposal's `materials/`. The `report-session`
stage of `s-lane` runs `spec-review`, `spec-sync` and, unless `collect-feedback` is switched off, `spec-feedback`.

### 4.3 Gates

| Gate | Stage(s) | Approval key (`[workflow.approvals]`) |
| --- | --- | --- |
| G1 intent | `intent`, `intent-session`, `intent-proposal` | `intent` |
| G2 direction | `direction`, `direction-handoff` | `direction` |
| G3 integration | `integration-approval`, `approval-session` | `integration` |

- `ask`: `devkit workflow next` prints `[WAITING: human gate:<gate>]` with a `[REQUEST: id=gate:<gate> ...]`. A G1
  or G2 answer is `devkit workflow answer --unit <dir> --request gate:<gate> --action accept --by user` (or
  `--action decline --by user --note "<reason>"`). A G3 OK is `--given integration` on every later `next`, and a G3 objection takes the stage's return
  path; where a runner binds `gate:integration` to PR state, the PR ready state answers G3. Every definition with an
  integration gate declares `gates: {integration: {answer: given}}`, so `next` ends the G3 `[REQUEST]` with
  `answer=given` and devkit's `devkit-workflow` skill gives the same instruction.
- `auto`: the gate passes by policy; `next` prints `[GATE: <gate> policy=auto ... source=policy]`.
- `off`: the stage is skipped (`[SKIPPED: <id> reason=...]`).
- `--given <gate>` asserts a gate for one run (a runner's binding).
- devkit defaults every gate to `ask`. Reading the effective values: `CAP-DLV-project-policy`.

### 4.4 Checks

| Check | Class | Meaning |
| --- | --- | --- |
| `anchor-exists` | devkit | `file-exists(spec.md)` under the spec layout, `file-exists(proposal.md)` under the proposal layout. |
| `file-exists(plan.md)` | devkit | The bundle has `plan.md`. |
| `tasks-exists`, `tasks-all-checked` | devkit | `tasks.md` exists / every task is checked. |
| `not-skeleton(<file>)` | devkit | The file no longer carries `<!-- devkit:skeleton -->` (`CAP-DLV-spec-bundles`). |
| `lint-clean` | devkit | `devkit rules` (linter phase) passes on the unit's files. |
| `frontmatter(<file> <key> <value>)` | devkit | A frontmatter value, e.g. `frontmatter(reconcile.md status resolved)`, `frontmatter(spec.md kind bugfix)`. |
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

Envelopes are devkit envelope files under the bundle's `envelopes/`, written with
`devkit workflow envelope new --unit <dir> --kind <kind> [--stage <id>] --summary "..." [--check <key>="PASS ..."]
[--base <ref>] [--head <sha>] [--assume ...] [--unverified ...]` and validated with
`devkit workflow envelope check --unit <dir>`; a malformed envelope never satisfies a check.

| Kind | File | Required checks |
| --- | --- | --- |
| `review`, `reverify` | `envelopes/review-NN.yaml`, `envelopes/reverify-NN.yaml` | review findings; reverify closes the round |
| `red` | `envelopes/red-NN.yaml` | `reproduced` |
| `green` | `envelopes/green-NN.yaml` | `resolved`, `preserved` |
| `feedback` | `envelopes/feedback-NN.yaml` | `swept` |
| `final-report` | `envelopes/final-report-NN.yaml` | `tests`, `build`, `lint` |
| `challenger`, `reconciler`, `scout` | role returns | none required by a stage |
| `worker` | the host's validation of a worker's committed range (`completed` accepts, `failed` blocks) | none required by a stage |

A role returns `status` (`completed`, `needs_input`, `failed`), `summary`, `findings` (`issue`, `evidence`,
`failure_condition`, `suggested_action`), `assumptions`, `unverified_areas`, `checks` and `diff_scope`; the Developer
records them. Docs impact has no envelope key: the reconciler writes it into the draft `reconcile.md`.

### 4.6 Role Contracts

One Markdown contract per role in devkit's
[role contract format](https://github.com/mjkimR/devkit/blob/main/docs/distribution/agent-projections.md#role-contract-format):
`role`, `title`, `description`, an optional `skill` and a `hosts` block for `claude-code`, `codex` and `antigravity`. Extension
keys devkit does not interpret: `x-execution` (`isolated`), `x-invocation` (`optional`), `x-model-profile`
(`light-medium`, `general-high`, `high-reasoning`; never a host model name) and `x-git-actions` (`[read]` for every
role but the `worker`, `[read, commit]`).

| Role | Skill | Model profile | Writes | Envelope kind |
| --- | --- | --- | --- | --- |
| `challenger` | none: the procedure is in the contract | `high-reasoning` | nothing | `challenger` |
| `reconciler` | `spec-sync` | `light-medium` | docs drafts and the bundle's `reconcile.md` | `reconciler` |
| `reviewer` | `spec-review` | `general-high` | nothing | `review`, `reverify` |
| `scout` | none: the procedure is in the contract | `light-medium` | nothing, or the proposal's `materials/` on request | `scout` |
| `worker` | none: the procedure is in the contract | `general-high` | the injected write scope inside its unit's worktree, committed on the unit branch | `worker` (validations) |

The contract body is the role's prompt and holds only what the role needs: purpose, input fields, return fields,
write boundaries, failure handling and, for a role whose procedure no main session runs (`challenger`, `scout`), the
procedure itself. `reviewer` and `reconciler` name the skill the main session also runs by default, with its
managed path and the sections the role follows (the reconciler only the impact and drafting steps). Caller guidance
(per-role payload, host guarantees, the post-run diff comparison, envelope recording) lives in `spec-delegate`
(`SPEC-subagent-procedure-in-contract`). Only `reviewer`, `scout` and `worker` have a shell (`Bash`; Antigravity
`run_command` with `commandExecutionPolicy: sandbox`), `scout` for `devkit spec search`, `list`, `resolve` and `refs`,
`worker` for the unit's checks.

`worker` exists for orchestration mode only (`spec-orchestrate`, user-invoked): it builds one unit's tasks in that
unit's devkit worktree, using absolute paths and `git -C <worktree>` because no host gives a subagent its own working
directory, and commits a complete result through the commit gate: tasks checked, the spec's `status` set by
`devkit rules fix`, the `docs/` paths its tasks' `_Boundary:` name, its checks passing; it commits nothing
incomplete. The host validates the cumulative committed range from the unit's last accepted head (write scope,
`spec.md` changed in `status` only, a clean worktree, an unchanged base checkout, passing checks) and records the
validation as a `worker` envelope. A failed validation blocks the unit from review and integration without discarding
anything: the commits stay (a pull request stays open and blocked) and later commits fix them
(`ADR-worker-delivers-committed-result`). Its host statuses are Claude Code `native`,
Codex `unsupported` (the host builds the unit itself) and Antigravity `unverified`
(`SPEC-orchestration-mode`).

Stages delegate to `reviewer` (`review-refine`), `reconciler` (`living-spec-draft`) and `scout` (`spike`);
`challenger` has no stage and is delegated on request, typically during a spike before G2; `worker` has no stage
either: implementation stages keep `role: developer`, and the orchestration mode delegates their tasks. `[DELEGATE: role=<role>
isolation=...]` in `next` names the role; `spec-delegate` decides between a host subagent and a main-session
substitute and records the choice. A projected role receives only the per-call payload, since the host loads the
contract body as its system prompt.

### 4.7 Executor Commands (devkit)

| Command | Use |
| --- | --- |
| `devkit workflow next --unit <dir> [--given <check>]...` | Current stage, unmet checks, `[NEXT_SKILL]`, `[WAITING]`, `[DELEGATE]`, `[SKIPPED]`. |
| `devkit workflow show <id>` / `--unit <dir>` | Render a definition. |
| `devkit workflow answer --unit <dir> --request gate:<gate> --action accept\|decline --by user` | Record a G1 or G2 gate decision. |
| `devkit workflow return --unit <dir> --to <stage>` | Go back; voids later approvals and earlier envelopes of those stages. |
| `devkit workflow bind --unit <dir> --workflow <id>` | Bind an unbound unit, or rebind after `WORKFLOW_DRIFT`. |
| `devkit workflow validate` | Validate definitions; `SHARED_STAGE_MISMATCH` across definitions. |
| `devkit workflow list` | List units of every layout. |
