---
id: direct-delivery
title: "Direct delivery (Route 2: intent, direction and integration gates)"
status: active
schema_version: 1
# G3 is asked after the change is final: its approval is passed as `--given integration`, never recorded
# (ADR-integration-approval-asserted).
gates:
  integration: { answer: given }
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
    name: G1 intent
    human_gate: intent
    entry: []
    exit: [anchor-exists]
    artifacts: [docs/proposals/PROP-<slug>/proposal.md, specs/<YYYY-MM>/<YYYYMMDD>-<slug>/]
    skills: [spec]
    role: developer
    isolation: none
    returns: []
  - id: direction
    name: G2 direction
    human_gate: direction
    entry: [anchor-exists]
    exit: [anchor-exists]
    artifacts: [specs/<YYYY-MM>/<YYYYMMDD>-<slug>/]
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
    returns:
      - { to: direction, when: a new policy or design choice appears }
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
      - { to: direction, when: new requirements }
      - { to: specify, when: contract drift }
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
      - { to: direction, when: design choices }
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
    name: G3 integration approval
    human_gate: integration
    entry: [envelope-check-pass(final-report tests), envelope-check-pass(final-report build), envelope-check-pass(final-report lint)]
    exit: []
    artifacts: [decisions/NN-gate-integration.yaml or PR ready state]
    skills: [spec]
    role: developer
    isolation: none
    returns:
      - { to: review-refine, when: the objection is about the change }
      - { to: direction, when: the objection is about direction }
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
      - { to: direction, when: design choices }
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
    name: E exception
    exception: true
    human_gate: false
    entry: [exception-raised]
    exit: [exception-handled]
    artifacts: [exception report envelope]
    skills: [spec]
    role: developer
    isolation: none
    returns:
      - { to: integrate, when: "the stage that raised it, after the cause is handled" }
---

# Direct delivery (Route 2)

Low uncertainty, high contract impact: the spec bundle `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` is created directly with `devkit spec new <slug>`, which writes the `SPEC-<slug>`, `PLAN-<slug>` and `TASKS-<slug>` skeletons and binds `spec.md` to this workflow. Project approval policy applies at three gates (`intent`, `direction`, `integration`) and exceptions are handled by a person; everything between is autonomous work backed by mechanical checks. Routes 3 and 4 reach this workflow through workflow `incubated-delivery` and `devkit spec proposal handoff`. Role contracts ship with the `spec` bundle (`.devkit/managed/spec/subagents/`); envelopes follow devkit's envelope contract and are written with `devkit workflow envelope new`; invocation guidance is `spec-delegate`. Living Spec changes land in the same integration unit before merge.

## Stages

The frontmatter is the only stage definition. Read it with `devkit workflow show direct-delivery` (or `devkit workflow show --unit <dir>` for a bound bundle); `devkit workflow next --unit <dir>` names the current stage, what is unmet and the skill to open. This document keeps only the rules the schema cannot express.

## Role invocation

Developer, `spec-review` and `spec-sync` by default; the `reviewer` and `reconciler` roles are optional. `[DELEGATE]` in `next` names the role and its contract when a stage prefers isolation; `spec-delegate` decides between a host subagent and a main-session substitute and records the choice in the envelope. PR, worktree and approval policy follow the repository and existing authority, independent of the number of roles.

## Gate rules

- **G1 records intent.** The gate opens once `spec.md` exists. Under `ask` it passes with the user's recorded answer (`devkit workflow answer --unit <dir> --request gate:intent --action accept --by user`), recorded only after the user confirmed goal, scope and verification.
- **G2 is conditional.** It fires for uncertain choices or changes to an existing agreement, never for implementation or integration inside an approved scope. Its exit is the mechanical proxy `anchor-exists`; with `direction = "auto"` it passes by policy unless a stage returns to it and the new choice is outside the requested scope, which the executor then puts to the user.
- **G3 is per integration unit** (one PR). Under `ask` it waits for the user's explicit OK, asserted with `--given integration` on every `next` after it and never recorded (`ADR-integration-approval-asserted`), or, where a runner binds it to PR state, the PR ready state; under `auto` it passes by policy once the final change report holds, within existing authority. Docs reflection and code conflict resolution within the approved intent are part of integration and need no re-approval.
- **Integration is a stage, not a persona.** The main-session Developer executes it, or an agent an external runner delegates. Its code authority is limited to conflict resolution and the verification that needs; its docs authority is the reflection the approved change requires. Adopting a new policy is a separate decision.
- **Approval is never inferred.** `devkit workflow next` reports `[WAITING: human gate:<gate>]` with a `[REQUEST]`; after the user's explicit answer, record a G1 or G2 answer with `devkit workflow answer` and assert a G3 OK with `--given integration`. `--given lint-ci-clean` and `--given merged` declare runner evidence. A G3 objection takes the stage's return path. A `devkit workflow return --to <stage>` voids the approvals of that stage and later ones.
- **Trust prior review.** Integration re-verifies only what conflict resolution and docs reflection changed; it does not restart code review and adds no extra approval gate.
- **Final change report.** `envelopes/final-report-NN.yaml` is completed with `checks.tests`, `checks.build` and `checks.lint` starting with `PASS` (`devkit workflow envelope new --unit <dir> --kind final-report --check tests="PASS ..." --check build="PASS ..." --check lint="PASS ..."`).
- **Commits.** Commit with plain `git commit`; devkit's commit gate runs the staged checks. After the integration commit run `devkit rules check --ci --base <ref>`, and declare `lint-ci-clean` once it and CI pass.

Distinguish the three failure kinds in E: retry cap exceeded, execution or tool failure, unresolved semantic conflict. Creating a new task to bypass a cap is not the default.

## Optional review feedback breakpoint

The boundary after `review-refine` passes and before `living-spec-draft` can be a feedback breakpoint. A runner chooses whether to wait for user feedback or proceed and owns wait and resume state. Intermediate commits are independent of waiting. If feedback changes the implementation, reverify the affected part through the existing return paths; direction changes return to `direction`. This adds no stage, check or approval file. Complete the Living Spec reflection and the resolved and completed states before G3.

## Runner notes

An external runner dispatches stages from this schema, binds `gate:integration` to PR state, owns the integration queue and the shared-docs write lock, enforces retry caps, executes the merge and declares `lint-ci-clean` and `merged`. The window from docs reflection to merge is serialized per project.

## Project policy execution

Read `devkit spec policy` before direction and integration decisions: approvals come from `[workflow.approvals]`, stage switches from `[workflow.stages]` (for example `collect-feedback = "off"`), PR and branch policy from `[worktree]`, and whether this route runs in a task worktree (`devkit worktree start <slug>`, `devkit worktree finish <slug>`) from `[tool.spec]` in `.devkit/config.toml`. `direction = "auto"` allows choices within the requested scope with reported assumptions; `ask` confirms concrete new direction choices, reusing existing approval. G1 still needs user intent and E still needs resolution. `integration = "ask"` holds G3 for the user's OK unless already authorized; `auto` delegates that decision only after the required review, reconciliation and checks pass, and `next` shows it as `[GATE: integration policy=auto ... source=policy]`, never as a human approval. Explicit user authority, required worktree and PR policy, external protections and action permissions remain applicable.
