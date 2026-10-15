---
id: s-lane
title: "S-Lane (Route 1: session-contained direct execution)"
status: active
schema_version: 1
# G3 is asked after the change is final: its approval is passed as `--given integration`, never recorded
# (ADR-integration-approval-asserted).
gates:
  integration: { answer: given }
# Executor-neutral stage schema: what a stage is, needs, produces and where it returns.
# Stages shared with other workflows keep the same id and the same exit, gate, role, isolation, skills and
# artifacts (`devkit workflow validate` reports SHARED_STAGE_MISMATCH); returns are this workflow's own.
# No layout: S-Lane creates no work unit.
checks:
  - { name: lint-ci-clean, class: runner, description: "devkit rules check --ci --base <ref> passes on the committed head: the Developer runs it after the commit and CI re-runs it as the final gate" }
  - { name: merged, class: runner, description: "the integration unit is merged into the base branch" }
  - { name: exception-raised, class: human, description: "a retry cap, tool failure or unresolved semantic conflict was raised" }
  - { name: exception-handled, class: human, description: "the cause of the exception was handled by the user" }
stages:
  - id: intent-session
    name: G1 intent
    human_gate: intent
    entry: []
    exit: []
    artifacts: [session note]
    skills: [spec]
    role: developer
    isolation: none
    returns: []
  - id: execute-verify
    name: Execute and verify
    human_gate: false
    entry: []
    exit: []
    artifacts: [code, tests]
    skills: []
    role: developer
    isolation: none
    returns:
      - { to: intent-session, when: the change needs a contract or design decision (reroute to workflow direct-delivery or incubated-delivery) }
  - id: report-session
    name: Report
    human_gate: false
    entry: []
    exit: []
    artifacts: [session report, specs/<YYYY-MM>/feedback/<YYYYMMDD>-<slug>.md]
    skills: [spec-review, spec-sync, spec-feedback]
    role: developer
    isolation: none
    returns:
      - { to: execute-verify, when: defects }
  - id: approval-session
    name: G3 integration approval
    human_gate: integration
    entry: []
    exit: []
    artifacts: [session OK (no file)]
    skills: [spec]
    role: developer
    isolation: none
    returns:
      - { to: report-session, when: the objection is about the change }
      - { to: intent-session, when: the objection is about direction }
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
      - { to: commit-session, when: "the stage that raised it, after the cause is handled" }
---

# S-Lane (Route 1)

Low uncertainty, low risk, session-contained (under 15 minutes): no spec bundle, no planning files, no envelope files, no work unit. Read the stages with `devkit workflow show s-lane`; `devkit workflow next` is not used because there is no unit to evaluate, so the executor follows the stages itself. Completion still requires the relevant checks and a Living Spec impact statement in the session report. A change that turns out to need a contract or design decision leaves this lane: reroute to workflow `direct-delivery` or `incubated-delivery`.

## Stages

The frontmatter is the only stage definition.

- **G1 intent**: expected behavior, scope and verification are agreed in the session.
- **Execute and verify**: the change is made and tests, build and `devkit rules check --staged` pass.
- **Report**: one session report covers the self-review against the agreed scope, the Living Spec impact (docs updated in the same change, or the no-impact reason) and, unless the project switched off `collect-feedback` in `[workflow.stages]`, observations not yet recorded as feedback (`spec-feedback`, month directory, no envelope).
- **Commit**: plain `git commit` after G3; devkit's commit gate runs the staged checks, and repository CI runs the cumulative check (`lint-ci-clean`, locally `devkit rules check --ci --base <ref>`). If integrating the base needed conflict resolution, re-run the checks for what it changed.

## Gate rules

- No G2: an open design choice means the work is not S-Lane. Return to G1 and reroute.
- G3 is the user's OK in session under `integration = "ask"`, or reported policy delegation under `auto` after verification and the Living Spec impact statement. Without a unit there is no decision record: nothing under `specs/` is written for it.
- `merge` and `exception` are the shared stages of the delivery workflows. S-Lane has no `reconcile.md`, so it uses `commit-session` instead of `integrate` and does not run `spec-integrate`.

## Project policy execution

Read `devkit spec policy` before the intent and integration decisions: approvals come from `[workflow.approvals]` and PR and branch policy from `[worktree]` in `.devkit/config.toml`. `integration = "ask"` holds G3 for the user's OK unless already authorized; `auto` delegates that decision only after the checks pass, and the executor reports the delegation, never a fabricated human approval. G1 still needs user intent and E still needs resolution. Explicit user authority, required PR policy, external protections and action permissions remain applicable; local branch cleanup after a confirmed merge follows `[worktree]` and existing deletion authority.
