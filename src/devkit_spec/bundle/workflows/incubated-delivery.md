---
id: incubated-delivery
title: "Incubated delivery (Routes 3 and 4: proposal, spike, direction, handoff)"
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
    name: G1 intent
    human_gate: intent
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
    skills: [spec-delegate, spec-scout, spec-challenge]
    role: scout
    isolation: preferred
    returns:
      - { to: intent-proposal, when: the goal itself is unclear }
  - id: direction-handoff
    name: G2 direction
    human_gate: direction
    entry: [anchor-exists]
    exit: []
    artifacts: ["proposal.md with status accepted, or the recorded direction decision"]
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
    artifacts: [specs/<YYYY-MM>/<YYYYMMDD>-<slug>/ bound to the workflow the proposal names]
    skills: [spec, spec-next]
    role: developer
    isolation: none
    returns:
      - { to: direction-handoff, when: the proposal must change before it can be handed off }
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
      - { to: handoff, when: "the stage that raised it, after the cause is handled" }
---

# Incubated delivery (Route 3 local review, Route 4 team PR review)

High uncertainty: the problem is shaped in a proposal bundle `docs/proposals/PROP-<slug>/` (anchor `proposal.md`, created with `devkit spec proposal new <slug>`, which binds it to this workflow) before any spec exists. `devkit workflow next --unit docs/proposals/PROP-<slug>` names the current stage. The workflow ends at handoff: `devkit spec proposal handoff <slug>` moves the proposal into a new spec bundle `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` and binds it to the delivery workflow the proposal names in `handoff_workflow` (`bugfix`, default `direct-delivery`; `workflow` in `proposal.md` is this workflow's own binding), after which that workflow's stages and gates apply from its first stage. Route 4 differs only in where the review happens (a PR on the proposal bundle).

## Stages

The frontmatter is the only stage definition. Read it with `devkit workflow show incubated-delivery` (or `devkit workflow show --unit <dir>`). This document keeps only the rules the schema cannot express.

- **Spike** is optional and never becomes the current stage on its own: run it when the direction needs evidence, delegating to the `scout` role (and `challenger` through `spec-challenge`). Its materials go under the proposal's `materials/`.
- **Handoff** has no exit check: once the direction gate holds, `next` reports the unit complete (`[STAGE: - complete=true]`, no `[HANDOFF]` line). That is the cue to run `devkit spec proposal handoff <slug>`. The definition declares no `next` candidates, because devkit's `devkit workflow handoff` rebinds a unit in place and cannot move it into another layout.

## Gate rules

- G1 and G2 are the only decisions before handoff; everything after handoff belongs to the bound workflow and its gates (G1 there is the intent of the spec bundle, normally confirmed by the accepted proposal).
- G2 is the direction choice. The chosen direction is written into the proposal (`status: accepted` on acceptance). Under `direction = "ask"` the gate passes with the recorded decision `devkit workflow answer --unit <dir> --request gate:direction --action accept`, written only after the user's choice. Under `direction = "auto"` it passes by policy; the executor still puts a direction outside the requested scope to the user before handoff.
- Routes 3 and 4 share this definition. The agreement mode (local session or team PR) is the executor's binding, not a stage.
- Scout and Challenger are optional support roles; zero findings is a valid spike result.

## Project policy execution

Read `devkit spec policy` before direction decisions: approvals come from `[workflow.approvals]`, stage switches from `[workflow.stages]`, and whether proposal work runs in a task worktree (`devkit worktree start <slug>`) from `[tool.spec]` in `.devkit/config.toml`. `direction = "auto"` allows choices within the requested scope with reported assumptions; `ask` confirms concrete new direction choices, reusing existing approval. G1 still needs user intent and E still needs resolution. Explicit user authority, required worktree and PR policy, external protections and action permissions remain applicable.
