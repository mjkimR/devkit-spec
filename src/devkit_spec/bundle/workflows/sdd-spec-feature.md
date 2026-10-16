---
id: sdd-spec-feature
title: "Spec feature (planning-depth spec, task-kind feature: plan-intent and dev-integration gates)"
status: active
schema_version: 1
# dev-integration is asked after the change is final: its approval is passed as `--given dev-integration`, never
# recorded (ADR-integration-approval-asserted).
gates:
  plan-intent: { policies: [ask] }  # always a person (01 §3); configuration cannot pass it
  dev-integration: { answer: given, policies: [ask, auto] }  # off would skip integration
# Executor-neutral stage schema: what a stage is, needs, produces and where it returns.
# Stages shared with other workflows keep the same id and the same exit, gate, role, isolation, skills and
# artifacts (`devkit workflow validate` reports SHARED_STAGE_MISMATCH); returns are this workflow's own.
layout:
  work_dir: specs
  unit_path: "{date:%Y-%m}/{date:%Y%m%d}-{slug}"
  anchor: spec.md
checks:
  - { name: lint-ci-clean, class: runner, description: "devkit rules check --ci --base <ref> passes on the committed head: the Developer runs it after the commit and CI re-runs it as the final gate" }
  - { name: merged, class: runner, description: "the integration unit is merged into the base branch" }
  - { name: exception-raised, class: human, description: "a retry cap, tool failure or unresolved semantic conflict was raised" }
  - { name: exception-handled, class: human, description: "the cause of the exception was handled by the user" }
stages:
  - id: intent
    name: Plan intent
    human_gate: plan-intent
    entry: []
    exit: [anchor-exists]
    artifacts: [docs/proposals/PROP-<slug>/proposal.md, specs/<YYYY-MM>/<YYYYMMDD>-<slug>/]
    skills: [spec]
    role: developer
    isolation: none
    returns: []
  - id: specify
    name: Specify
    human_gate: false
    entry: [anchor-exists]
    exit: [file-exists(plan.md), tasks-exists, not-skeleton(spec.md), not-skeleton(plan.md), not-skeleton(tasks.md), lint-clean]
    artifacts: [spec.md, plan.md, tasks.md]
    skills: [spec-specify, spec-plan, spec-tasks]
    role: developer
    isolation: none
    returns: []
  - id: build-verify
    name: Build and verify
    human_gate: false
    entry: [tasks-exists]
    exit: [tasks-all-checked, lint-clean]
    artifacts: [code, tests]
    skills: []
    role: developer
    isolation: none
    returns:
      - { to: specify, when: contract drift within the agreed intent }
  - id: review-refine
    name: Review-refine loop
    human_gate: false
    entry: [tasks-all-checked]
    exit: [envelope-review-passed]
    artifacts: [envelopes/review-NN.yaml, envelopes/reverify-NN.yaml]
    skills: [spec-review, spec-delegate]
    role: reviewer
    isolation: preferred
    returns:
      - { to: build-verify, when: defects }
  - id: living-spec-draft
    name: Living Spec draft
    human_gate: false
    entry: [envelope-review-passed]
    exit: [frontmatter(reconcile.md status resolved), anchor-status-completed]
    artifacts: [docs draft, reconcile.md]
    skills: [spec-sync, spec-delegate]
    role: reconciler
    isolation: preferred
    returns:
      - { to: build-verify, when: implementation contradicts a contract }
  - id: collect-feedback
    name: Collect feedback
    human_gate: false
    entry: [frontmatter(reconcile.md status resolved)]
    exit: [envelope-check-pass(feedback swept)]
    artifacts: [feedback/*.md, envelopes/feedback-NN.yaml]
    skills: [spec-feedback]
    role: developer
    isolation: none
    returns: []
  - id: final-change-report
    name: Final change report
    human_gate: false
    entry: [envelope-check-pass(feedback swept)]
    exit: [envelope-check-pass(final-report tests), envelope-check-pass(final-report build), envelope-check-pass(final-report lint)]
    artifacts: [envelopes/final-report-NN.yaml]
    skills: [spec]
    role: developer
    isolation: none
    returns: []
  - id: integration-approval
    name: Dev integration approval
    human_gate: dev-integration
    entry: [envelope-check-pass(final-report tests), envelope-check-pass(final-report build), envelope-check-pass(final-report lint)]
    exit: []
    artifacts: [PR ready state, or the Host's explicit approval passed as --given dev-integration]
    skills: [spec]
    role: developer
    isolation: none
    returns:
      - { to: review-refine, when: the objection is about the change }
  - id: integrate
    name: Integrate
    human_gate: false
    entry: [envelope-check-pass(final-report tests), envelope-check-pass(final-report build), envelope-check-pass(final-report lint)]
    exit: [frontmatter(reconcile.md status resolved), anchor-status-completed, lint-ci-clean]
    artifacts: [integrated head]
    skills: [spec-integrate]
    role: developer
    isolation: none
    returns:
      - { to: build-verify, when: defects beyond integration scope }
      - { to: exception, when: retry caps }
  - id: merge
    name: Merge
    human_gate: false
    entry: [lint-ci-clean]
    exit: [merged]
    artifacts: [merge]
    skills: []
    role: "-"
    isolation: none
    returns:
      - { to: integrate, when: "head, base or approval changed" }
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
      - { to: integrate, when: "the stage that raised it, after the cause is handled" }
---

# Spec feature (`planning-depth` spec, `task-kind` feature)

New or changed behavior whose direction is clear but whose contract (behavior, interface) must be fixed before implementation. The spec bundle `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` is created in inline Planning with `devkit spec new <slug>` on the activity branch `dev-<slug>`, which writes the `SPEC-<slug>`, `PLAN-<slug>` and `TASKS-<slug>` skeletons and binds `spec.md` to this workflow; `plan-intent` is recorded there and that state is the input of Development. A `proposal`-depth task reaches this workflow through workflow `sdd-proposal` and `devkit spec proposal handoff` (proposal `task_kind: feature`). Role contracts ship with the `spec` bundle (`.devkit/managed/spec/subagents/`); envelopes follow devkit's envelope contract; invocation guidance is `spec-delegate`. Living Spec changes land in the same integration unit before merge.

## Stages

The frontmatter is the only stage definition. Read it with `devkit workflow show sdd-spec-feature` (or `devkit workflow show --unit <dir>` for a bound bundle); `devkit workflow next --unit <dir>` names the current stage, what is unmet and the skill to open. This document keeps only the rules the schema cannot express.

## Development runs on the agreed intent

There is no Development direction gate. Within the agreed goal, scope and contract the executor decides implementation choices with its recommended option and records the reason (in `plan.md`, an envelope's assumptions or the final report). An improvement that does not block the current work is reported as feedback by default; a follow-up draft proposal (`devkit spec proposal new`) is also allowed. Only a problem that cannot be solved without changing the agreed goal, scope or contract stops the work: a worker records it as the problem of its `worker` envelope and ends, and the gates from its stage on (and the handoff) are held until a `resolution` names it, while `next` keeps naming the current stage for the recovery; the Host decides recovery, a revert, finishing it itself, or a close (depth escalation, supersede, abandon). There is no return from Development to Planning.

## Role invocation

Developer, `spec-review` and `spec-sync` by default; the `reviewer` and `reconciler` roles follow the `activity-effort` of the Development activity (`low`: self-review and self-checked reconcile; `medium`: one reviewer pass plus reverification of fixes, the reviewer also checks the reconcile result; `high`: reviewer with re-review after fixes and an independent `reconciler` verification). Effort never lowers the floor: gates, this workflow's exit checks and `required` policies hold at every effort, and the review envelope is recorded before `dev-integration` even at `low`. `[DELEGATE]` in `next` names the role and its contract when a stage prefers isolation; `spec-delegate` decides how it runs.

## Gate rules

- **`plan-intent` is always a person's decision.** It opens once `spec.md` exists and passes with the user's recorded answer (`devkit workflow answer --unit <dir> --request gate:plan-intent --action accept --by user`), recorded only after the user confirmed goal, scope, verification, `task-kind` and `planning-depth`. A spec handed off from a proposal carries the proposal's `gate:plan-intent` and `gate:plan-accept` records under their own names (`[CARRIED_GATE]`); `plan-intent` is not asked again.
- **`dev-integration` is per integration unit** (one PR). Under `ask` it waits for the user's explicit OK, asserted with `--given dev-integration` on every `next` after it and never recorded (`ADR-integration-approval-asserted`), or, where a runner binds it, the PR ready state; under `auto` it passes by policy once the review, reconcile and final change report hold, also at `activity-effort` `low`. Docs reflection and code conflict resolution within the approved intent are part of integration and need no re-approval.
- **Integration is a stage, not a persona.** Its code authority is limited to conflict resolution and the verification that needs; its docs authority is the reflection the approved change requires. Adopting a new policy is a separate decision.
- **Approval is never inferred.** `devkit workflow next` reports `[WAITING: human gate:<gate>]` with a `[REQUEST]`; record `plan-intent` with `devkit workflow answer` after the user's explicit answer, and assert a `dev-integration` OK with `--given dev-integration`. `--given lint-ci-clean` and `--given merged` declare runner evidence. A `dev-integration` objection about the change takes the stage's return path; one about direction is a close (`spec` skill). A `devkit workflow return --to <stage>` voids the approvals of that stage and later ones.
- **Trust prior review.** Integration re-verifies only what conflict resolution and docs reflection changed; it does not restart code review and adds no extra approval gate.
- **Final change report.** `envelopes/final-report-NN.yaml` is completed with `checks.tests`, `checks.build` and `checks.lint` starting with `PASS` (`devkit workflow envelope new --unit <dir> --kind final-report --check tests="PASS ..." --check build="PASS ..." --check lint="PASS ..."`).
- **Commits.** Commit at every stage boundary with plain `git commit`; devkit's commit gate runs the staged checks. After the integration commit run `devkit rules check --ci --base <ref>`, and declare `lint-ci-clean` once it and CI pass.

Distinguish the three failure kinds in `exception`: retry cap exceeded, execution or tool failure, unresolved semantic conflict. Creating a new task to bypass a cap is not the default. A problem the Host can handle itself never goes through `exception`.

## Optional review feedback breakpoint

The boundary after `review-refine` passes and before `living-spec-draft` can be a feedback breakpoint. A runner chooses whether to wait for user feedback or proceed and owns wait and resume state. Intermediate commits are independent of waiting. If feedback changes the implementation within the agreed intent, reverify the affected part through the existing return paths; feedback that changes the intent is a close. This adds no stage, check or approval file. Complete the Living Spec reflection and the resolved and completed states before `dev-integration`.

## Runner notes

An external runner dispatches stages from this schema, binds `gate:dev-integration` to PR state, owns the integration queue and the shared-docs write lock, enforces retry caps, executes the merge and declares `lint-ci-clean` and `merged`. The window from docs reflection to merge is serialized per project.

## Project policy execution

Read `devkit spec policy` before integration decisions: approvals come from `[workflow.approvals]` (only `dev-integration` takes a key, `ask` or `auto`), stage switches from `[workflow.stages]` (for example `collect-feedback = "off"`), PR and branch policy from `[worktree]`, and whether a `direct`-mode activity runs in a separate worktree from `[tool.spec] worktree`. `dev-integration = "ask"` holds the gate for the user's OK unless already authorized; `auto` delegates that decision only after the required review, reconciliation and checks pass, and `next` shows it as `[GATE: dev-integration policy=auto ... source=policy]`, never as a human approval. `plan-intent` always needs the user and `exception` always needs resolution. Explicit user authority, required worktree and PR policy, external protections and action permissions remain applicable.
