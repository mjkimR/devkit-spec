---
id: bugfix
title: "Bugfix (formal: characterize, reproduce, fix, verify)"
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
  - id: characterize
    name: Characterize defect
    human_gate: false
    entry: [anchor-exists]
    exit: [frontmatter(spec.md kind bugfix), not-skeleton(spec.md), lint-clean]
    artifacts: [spec.md]
    skills: [spec-specify]
    role: developer
    isolation: none
    returns:
      - { to: direction, when: the expected behavior itself is not agreed }
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
  - id: plan-tasks
    name: Fix design and tasks
    human_gate: false
    entry: [frontmatter(spec.md kind bugfix)]
    exit: [file-exists(plan.md), tasks-exists, not-skeleton(plan.md), not-skeleton(tasks.md), lint-clean]
    artifacts: [plan.md, tasks.md]
    skills: [spec-plan, spec-tasks]
    role: developer
    isolation: none
    returns:
      - { to: direction, when: a new policy or design choice appears }
      - { to: characterize, when: the fix needs a different defect scope }
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
      - { to: direction, when: the expected behavior is not agreed }
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
      - { to: direction, when: a contract change is needed }
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
      - { to: fix-verify, when: defects }
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

# Bugfix (formal)

A defect whose fix has contract impact or enough uncertainty to need a spec bundle. The bundle (`devkit spec new <slug> --workflow bugfix`, or a proposal handed off with `handoff_workflow: bugfix`) keeps `spec.md` (ID `SPEC-<slug>`, written with `kind: bugfix` by either command) and the defect characterization (current, expected and preserved behavior, reproduction conditions) instead of a feature specification; procedure: `spec-specify`. Reproduction evidence comes before the fix (`envelopes/red-NN.yaml`, `checks.reproduced`), resolution and preservation evidence after it (`envelopes/green-NN.yaml`, `checks.resolved`, `checks.preserved`). Evidence is judged by `envelope-check-pass`; `diff_scope` is recorded for traceability and `revision-ancestor(red green)` is available when a project wants stricter ordering. A small, low-risk defect takes workflow `s-lane` instead. The stages after the fix are those of workflow `direct-delivery`.

## Stages

The frontmatter is the only stage definition. Read it with `devkit workflow show bugfix` (or `devkit workflow show --unit <dir>`); `devkit workflow next --unit <dir>` names the current stage. This document keeps only the rules the schema cannot express.

## Evidence contract

- **Red before Green.** Record reproduction with `devkit workflow envelope new --unit <dir> --kind red --stage reproduce --summary "..." --check reproduced="PASS <command>: <observed failure>" --head $(git rev-parse HEAD)` (omit `--head` when there is no revision yet). A compile, environment or test-setup failure unrelated to the defect is not reproduction evidence; a build failure that is the defect is.
- **Green** records the same conditions giving the expected result (`--check resolved="PASS ..."`) and the preserved behavior (`--check preserved="PASS ..."`) with the commands run, in `envelopes/green-NN.yaml`. The added reproduction test stays as a regression test.
- **Alternative evidence** (external outage, environment-dependent or flaky defects): fix the observation conditions and expected results in `spec.md` first; the Green envelope then states resolution confirmed or residual uncertainty. One non-occurrence is not resolution.
- `devkit workflow envelope check --unit <dir>` reports malformed envelope files; a malformed file never satisfies a check.

## Gate rules

- **G1 records intent.** The gate opens once `spec.md` exists; under `ask` record the user's confirmation with `devkit workflow answer --unit <dir> --request gate:intent --action accept`.
- **G2 is conditional.** It fires for uncertain choices or changes to an existing agreement (including an expected behavior that is not agreed), never for implementation or integration inside an approved scope. Its exit is the mechanical proxy `anchor-exists`; with `direction = "auto"` it passes by policy unless a stage returns to it with a choice outside the requested scope, which the executor then puts to the user.
- **G3 is per integration unit** (one PR). Under `ask` it waits for the user's explicit OK, asserted with `--given integration` on every `next` after it and never recorded (`ADR-integration-approval-asserted`), or, where a runner binds it, the PR ready state; under `auto` it passes by policy once the final change report holds, within existing authority. Docs reflection and code conflict resolution within the approved intent are part of integration and need no re-approval.
- **Integration is a stage, not a persona.** Its code authority is limited to conflict resolution and the verification that needs; its docs authority is the reflection the approved change requires. Adopting a new policy is a separate decision.
- **Approval is never inferred.** After the user's explicit answer, record a G1 or G2 answer with `devkit workflow answer` and assert a G3 OK with `--given integration`; `--given` also declares runner checks (`lint-ci-clean`, `merged`) for one run. A G3 objection takes the stage's return path. A `devkit workflow return --to <stage>` voids the approvals of that stage and later ones.
- **Trust prior review.** Integration re-verifies only what conflict resolution and docs reflection changed; it does not restart code review.
- **Commits.** Commit with plain `git commit`; devkit's commit gate runs the staged checks. After the integration commit run `devkit rules check --ci --base <ref>`, and declare `lint-ci-clean` once it and CI pass.

Distinguish the three failure kinds in E: retry cap exceeded, execution or tool failure, unresolved semantic conflict. Creating a new task to bypass a cap is not the default.

## Optional review feedback breakpoint

The boundary after `review-refine` passes and before `living-spec-draft` can be a feedback breakpoint. A runner chooses whether to wait for user feedback or proceed and owns wait and resume state. If feedback changes the fix, reverify the affected part through the existing return paths; direction changes return to `direction`. This adds no stage, check or approval file. Complete the Living Spec reflection and the resolved and completed states before G3.

## Project policy execution

Read `devkit spec policy` before direction and integration decisions: approvals come from `[workflow.approvals]`, stage switches from `[workflow.stages]`, PR and branch policy from `[worktree]`, and whether this route runs in a task worktree from `[tool.spec]` in `.devkit/config.toml`. `direction = "auto"` allows choices within the requested scope with reported assumptions; `ask` confirms concrete new direction choices, reusing existing approval. G1 still needs user intent and E still needs resolution. `integration = "auto"` delegates G3 only after the required review, reconciliation and checks pass, and `next` shows it as `source=policy`, never as a human approval. Explicit user authority, required worktree and PR policy, external protections and action permissions remain applicable.
