---
id: sdd-session-bugfix
title: "Session bugfix (planning-depth session, task-kind bugfix: reproduce first, no Unit)"
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
# No layout: a session creates no work unit, envelope, gate record file or reconcile document.
checks:
  - { name: lint-ci-clean, class: runner, description: "devkit rules check --ci --base <ref> passes on the committed head: the Developer runs it after the commit and CI re-runs it as the final gate" }
  - { name: merged, class: runner, description: "the integration unit is merged into the base branch" }
  - { name: exception-raised, class: human, description: "a retry cap, tool failure or unresolved semantic conflict was raised" }
  - { name: exception-handled, class: human, description: "the cause of the exception was handled by the user" }
stages:
  - id: intent-session
    name: Plan intent
    human_gate: plan-intent
    entry: []
    exit: []
    artifacts: [agreed intent in the conversation or the Work Plan Item]
    skills: [spec]
    role: developer
    isolation: none
    returns: []
  - id: reproduce-session
    name: Reproduce (Red)
    human_gate: false
    entry: []
    exit: []
    artifacts: [failing reproduction test]
    skills: []
    role: developer
    isolation: none
    returns:
      - { to: intent-session, when: the defect is not what was agreed }
  - id: execute-verify
    name: Execute and verify
    human_gate: false
    entry: []
    exit: []
    artifacts: [code, tests]
    skills: []
    role: developer
    isolation: none
    returns: []
  - id: report-session
    name: Review and report
    human_gate: false
    entry: []
    exit: []
    artifacts: [session report in the final response or the PR body]
    skills: [spec-review, spec-feedback]
    role: developer
    isolation: none
    returns:
      - { to: execute-verify, when: defects }
  - id: commit-session
    name: Commit
    human_gate: false
    entry: []
    exit: [lint-ci-clean]
    artifacts: [commit]
    skills: []
    role: developer
    isolation: none
    returns:
      - { to: execute-verify, when: defects found by CI }
      - { to: exception, when: retry caps }
  - id: approval-session
    name: Dev integration approval
    human_gate: dev-integration
    entry: []
    exit: []
    artifacts: [session OK or PR ready state (no file)]
    skills: [spec]
    role: developer
    isolation: none
    returns:
      - { to: report-session, when: the objection is about the change }
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
      - { to: commit-session, when: "head, base or approval changed" }
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
      - { to: commit-session, when: "the stage that raised it, after the cause is handled" }
---

# Session bugfix (`planning-depth` session, `task-kind` bugfix)

A defect against an agreed contract that the session can reproduce and fix without written documents: workflow `sdd-session-feature` with a reproduction step first. The expected behavior is agreed at `plan-intent`. Before the fix, write a test that reproduces the defect and confirm it fails (Red, `reproduce-session`); then fix it so the test passes (Green, `execute-verify`). The test stays as a regression test. Read the stages with `devkit workflow show sdd-session-bugfix`.

- A compile, environment or test-setup failure unrelated to the defect is not reproduction; a build failure that is the defect is.
- When the defect is hard to reproduce, or the current, expected and preserved behavior must be written down, raise the depth to `spec` (`sdd-spec-bugfix`). When the agreed expected behavior cannot be kept, report it as a problem.

## Completion conditions

A session completes without document artifacts. It creates no spec Unit, no envelope (review, worker, problem or resolution), no gate record file and no reconcile document, at every `activity-effort`.

- The Host (`direct`) or the Cloud Agent (`cloud-pr` general PR path) implements the agreed intent and runs the tests and checks it needs, including the Red then Green reproduction.
- The review follows the `activity-effort` of the activity: `low` the author's self-review; `medium` one `reviewer` subagent pass and reverification of the fixes; `high` a `reviewer` subagent review and a re-review after the fixes. The Host or Cloud Agent starts the reviewer itself and receives its result as a message; the reviewer writes no envelope. Raising the review effort never raises the depth.
- `plan-intent`, the `dev-integration` approval policy and the worktree and PR policy apply. Approvals and checks are never skipped, and no file records them: `plan-intent` is the user's agreement in the conversation (or the Work Plan Item), `dev-integration` the user's OK in the session or the PR ready state under `ask`, policy delegation under `auto` once these conditions hold.
- The final response or the PR body reports the change, the applied effort and review result, the verification result with the Red then Green evidence (the reproduction command, its failure before and its pass after the fix) and the remaining constraints. No final report file is written.
- A problem the session cannot solve is reported in the conversation (or as the problem report of the autohub general run) and the change is not integrated. A lasting design record, a contract change or a Living Spec change raises the depth to `spec`: add a spec Unit in the current work environment (`devkit spec new`), record the agreed intent and the work so far, and continue with that workflow's next stage; no close, no new slug, and the agreement is not asked again unless the goal or scope changes. A direction that must be decided first is a close by depth escalation to a new draft proposal.

## Mode

A session runs in `direct` or through the `cloud-pr` general PR path (a Work Plan Item a Cloud Agent turns into a PR) only, never in `local-orchestrated`: a one-shot worker cannot read a conversation, and a worktree plus a worker cost more than the work. A Host in `local-orchestrated` handles a session-depth task itself in `direct`. With a PR the work runs on `dev-<slug>`; without one on the current branch.

## Gate rules

- `merge` and `exception` are the shared stages of the delivery workflows. A session has no `reconcile.md`, so it uses `commit-session` instead of `integrate` and does not run `spec-integrate` or `spec-sync`.
- `devkit workflow next` is not used: there is no unit to evaluate, so the executor follows the stages itself (`devkit workflow show sdd-session-bugfix`).
- **Commit before approval**: plain `git commit` once the review is done and before `dev-integration`, so the approval (the user's OK, or a PR's ready state) is given on committed work CI has checked; a PR is pushed and opened at this stage. devkit's commit gate runs the staged checks, and repository CI runs the cumulative check (`lint-ci-clean`, locally `devkit rules check --ci --base <ref>`). If integrating the base needed conflict resolution, re-run the checks for what it changed.

## Project policy execution

Read `devkit spec policy` before the integration decision: approvals come from `[workflow.approvals]` (only `dev-integration`, `ask` or `auto`) and PR and branch policy from `[worktree]` in `.devkit/config.toml`. `auto` delegates `dev-integration` only after the completion conditions hold, at every effort, and the executor reports the delegation, never a fabricated human approval. `plan-intent` always needs the user and `exception` always needs resolution. Explicit user authority, required PR policy, external protections and action permissions remain applicable; local branch cleanup after a confirmed merge follows `[worktree]` and existing deletion authority.
