---
id: sdd-spec-bugfix
title: "Spec bugfix (planning-depth spec, task-kind bugfix: characterize, reproduce, fix, verify)"
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
  - id: characterize
    name: Characterize defect
    human_gate: false
    entry: [anchor-exists]
    exit: [not-skeleton(spec.md), lint-clean]
    artifacts: [spec.md]
    skills: [spec-specify]
    role: developer
    isolation: none
    returns: []
  - id: plan-tasks
    name: Fix design and tasks
    human_gate: false
    entry: [not-skeleton(spec.md)]
    exit: [file-exists(plan.md), tasks-exists, not-skeleton(plan.md), not-skeleton(tasks.md), lint-clean]
    artifacts: [plan.md, tasks.md]
    skills: [spec-plan, spec-tasks]
    role: developer
    isolation: none
    returns:
      - { to: characterize, when: the fix needs a different defect scope within the agreed expected behavior }
  - id: reproduce
    name: Reproduce
    human_gate: false
    entry: [tasks-exists]
    exit: [envelope-check-pass(red reproduced)]
    artifacts: [envelopes/red-NN.yaml]
    skills: [spec-specify]
    role: developer
    isolation: none
    returns:
      - { to: characterize, when: the defect is not what was characterized }
  - id: fix-verify
    name: Fix and verify
    human_gate: false
    entry: [envelope-check-pass(red reproduced)]
    exit: [tasks-all-checked, envelope-check-pass(green resolved), envelope-check-pass(green preserved), lint-clean]
    artifacts: [code, tests, envelopes/green-NN.yaml]
    skills: []
    role: developer
    isolation: none
    returns:
      - { to: characterize, when: the fix changes the characterized scope }
  - id: review-refine
    name: Review-refine loop
    human_gate: false
    entry: [tasks-all-checked]
    exit: [envelope-review-passed]
    artifacts: [envelopes/review-NN.yaml, envelopes/reverify-NN.yaml]
    skills: [spec-review, spec-delegate]
    role: code-reviewer
    isolation: preferred
    returns:
      - { to: fix-verify, when: defects }
  - id: living-spec-draft
    name: Living Spec draft
    human_gate: false
    entry: [envelope-review-passed]
    exit: [frontmatter(reconcile.md status resolved), envelope-completed(reconcile-check), anchor-status-completed]
    artifacts: [docs draft, reconcile.md]
    skills: [spec-sync, spec-delegate]
    role: reconcile-reviewer
    isolation: preferred
    returns:
      - { to: fix-verify, when: implementation contradicts a contract }
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
      - { to: fix-verify, when: defects beyond integration scope }
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

# Spec bugfix (`planning-depth` spec, `task-kind` bugfix)

A defect against an agreed contract whose fix needs a spec bundle: contract impact, or current, expected and preserved behavior that must be written down. The expected behavior is agreed at `plan-intent`; characterizing it is Development's work. The bundle (`devkit spec new <slug> --workflow sdd-spec-bugfix`, or a proposal with `task_kind: bugfix` handed off with `devkit spec proposal handoff`) starts with `spec.md` only (ID `SPEC-<slug>`); the bound workflow is the only record of its `task-kind`. `spec.md` holds the defect characterization (current, expected and preserved behavior, reproduction conditions) instead of a feature specification; procedure: `spec-specify`. Reproduction evidence comes before the fix (`envelopes/red-NN.yaml`, `checks.reproduced`), resolution and preservation evidence after it (`envelopes/green-NN.yaml`, `checks.resolved`, `checks.preserved`). Evidence is judged by `envelope-check-pass`; `diff_scope` is recorded for traceability and `revision-ancestor(red green)` is available when a project wants stricter ordering. A defect a session can reproduce and fix without written documents takes workflow `sdd-session-bugfix` instead. The stages after the fix are those of workflow `sdd-spec-feature`.

## Stages

The frontmatter is the only stage definition. Read it with `devkit workflow show sdd-spec-bugfix` (or `devkit workflow show --unit <dir>`); `devkit workflow next --unit <dir>` names the current stage. This document keeps only the rules the schema cannot express.

## Evidence contract

- **Red before Green.** Record reproduction with `devkit workflow envelope new --unit <dir> --kind red --stage reproduce --summary "..." --check reproduced="PASS <command>: <observed failure>" --head $(git rev-parse HEAD)` (omit `--head` when there is no revision yet). A compile, environment or test-setup failure unrelated to the defect is not reproduction evidence; a build failure that is the defect is.
- **Green** records the same conditions giving the expected result (`--check resolved="PASS ..."`) and the preserved behavior (`--check preserved="PASS ..."`) with the commands run, in `envelopes/green-NN.yaml`. The added reproduction test stays as a regression test.
- **Alternative evidence** (external outage, environment-dependent or flaky defects): fix the observation conditions and expected results in `spec.md` first; the Green envelope then states resolution confirmed or residual uncertainty. One non-occurrence is not resolution.
- `devkit workflow envelope check --unit <dir>` reports malformed envelope files; a malformed file never satisfies a check.

## Development runs on the agreed intent

There is no Development direction gate. Implementation choices inside the agreed expected behavior are decided with the recommended option and recorded. When the agreed expected behavior cannot be kept (the defect turns out to be a design problem, or the expected behavior itself is disputed), the work stops as a problem: a worker records it and ends, and the Host decides recovery or a close; it is never taken back to Planning.

## Gate rules

- **`plan-intent` records the intent, the expected behavior included.** The gate opens once `spec.md` exists; record the user's confirmation with `devkit workflow answer --unit <dir> --request gate:plan-intent --action accept --by user`. A spec handed off from a proposal carries the proposal's `gate:plan-intent` and `gate:plan-accept` under their own names (`[CARRIED_GATE]`).
- **`dev-integration` is per integration unit** (one PR). Under `ask` it waits for the user's explicit OK, asserted with `--given dev-integration` on every `next` after it and never recorded (`ADR-integration-approval-asserted`), or, where a runner binds it, the PR ready state; under `auto` it passes by policy once the final change report holds, within existing authority, also at `activity-effort` `low`. Docs reflection and code conflict resolution within the approved intent are part of integration and need no re-approval.
- **Integration is a stage, not a persona.** Its code authority is limited to conflict resolution and the verification that needs; its docs authority is the reflection the approved change requires. Adopting a new policy is a separate decision.
- **Approval is never inferred.** After the user's explicit answer, record `plan-intent` with `devkit workflow answer` and assert a `dev-integration` OK with `--given dev-integration`; `--given` also declares runner checks (`lint-ci-clean`, `merged`) for one run. A `dev-integration` objection about the change takes the stage's return path; one about direction is a close. A `devkit workflow return --to <stage>` voids the approvals of that stage and later ones.
- **Trust prior review.** Integration re-verifies only what conflict resolution and docs reflection changed; it does not restart code review.
- **Commits.** Commit at every stage boundary with plain `git commit`; devkit's commit gate runs the staged checks. After the integration commit run `devkit rules check --ci --base <ref>`, and declare `lint-ci-clean` once it and CI pass.

Distinguish the three failure kinds in `exception`: retry cap exceeded, execution or tool failure, unresolved semantic conflict. Creating a new task to bypass a cap is not the default.

## Optional review feedback breakpoint

The boundary after `review-refine` passes and before `living-spec-draft` can be a feedback breakpoint. A runner chooses whether to wait for user feedback or proceed and owns wait and resume state. If feedback changes the fix within the agreed expected behavior, reverify the affected part through the existing return paths; feedback that changes the expected behavior is a close. This adds no stage, check or approval file. Complete the Living Spec reflection and the resolved and completed states before `dev-integration`.

## Project policy execution

Read `devkit spec policy` before integration decisions: approvals come from `[workflow.approvals]` (only `dev-integration` takes a key, `ask` or `auto`), stage switches from `[workflow.stages]`, PR and branch policy from `[worktree]`, and whether a `direct`-mode activity runs in a separate worktree from `[tool.spec] worktree`. `dev-integration = "auto"` delegates the gate only after the required review, reconciliation and checks pass, and `next` lists it as `[GATE_PASSED: dev-integration stage=integration-approval policy=auto source=policy]`, the basis the integration report cites, never as a human approval. `plan-intent` always needs the user and `exception` always needs resolution. Explicit user authority, required worktree and PR policy, external protections and action permissions remain applicable.
