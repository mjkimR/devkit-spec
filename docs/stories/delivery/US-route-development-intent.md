---
id: US-route-development-intent
title: Route a Development Request to the Right Workflow
summary: An AI coding agent turns a user's development request into the right delivery route (S-Lane, direct delivery, bugfix or incubated proposal) under the project's policy, creates and binds the work unit, and follows the workflow's stages and gates.
area: delivery
actor: AI coding agent
status: active
created_at: 2026-10-13
capabilities:
  - CAP-HARN-agent-guidance
  - CAP-DLV-delivery-workflows
  - CAP-DLV-spec-bundles
  - CAP-DLV-project-policy
---

# [US-route-development-intent] Route a Development Request to the Right Workflow

## 1. User Story Narrative

- **As a**: AI coding agent working in a project that installed devkit-spec
- **I want to**: classify a development request by uncertainty, contract impact and risk, pick its route and drive
  the matching workflow from intent to integration
- **So that**: small changes stay light, contract changes get a spec, and every approval the user owns is asked at the
  right moment instead of being inferred or skipped

---

## 2. Background & Context

The agent loads the constitution with `devkit get-context spec`, enters through the `spec` skill (`/spec <intent>`)
and reads `devkit spec policy` before routing. Route 1 runs `s-lane` in the session without a work unit; Route 2
creates a spec bundle with `devkit spec new` (`--workflow bugfix` for a defect); Routes 3 and 4 incubate a proposal
first. From then on `devkit workflow next --unit <dir>` names the stage, its unmet checks and the skill to open, and
the gates follow the project's `[workflow.approvals]`.

---

## 3. Acceptance Criteria (Given / When / Then)

### Scenario 1: A contract change becomes a bound spec bundle
- **Given**: the policy reports `[GIT_POLICY: worktree=auto ...]`, the agent keeps the task in the current checkout,
  and the request changes a documented contract with low uncertainty
- **When**: the agent runs `devkit spec new <slug>`
- **Then**: `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` holds skeleton-marked `spec.md`, `plan.md` and `tasks.md`,
  `spec.md` is bound to `direct-delivery`, and the output ends with
  `[NEXT_CMD: devkit workflow next --unit <dir>]`

### Scenario 2: The intent gate waits for the user under `ask`
- **Given**: `[GATE_POLICY: intent policy=ask ...]` and a freshly created bundle
- **When**: the agent runs `devkit workflow next --unit <dir>`
- **Then**: the output shows `[WAITING: human gate:intent]`, and the agent records
  `devkit workflow answer --unit <dir> --request gate:intent --action accept` only after the user's explicit answer

### Scenario 3: A defect with contract impact takes the bugfix workflow
- **Given**: an observed behavior contradicts an existing contract and the fix is larger than an S-Lane change
- **When**: the agent runs `devkit spec new <slug> --workflow bugfix`
- **Then**: the bundle holds only `spec.md` with `kind: bugfix`, bound to `bugfix`, and the `reproduce` stage stays
  open until a `red` envelope records `checks.reproduced`

### Scenario 4: An S-Lane change that needs a decision is rerouted
- **Given**: a request routed to `s-lane` turns out to need a contract or design decision
- **When**: the agent reaches that decision in `execute-verify`
- **Then**: it returns to `intent-session` and reroutes to `direct-delivery` or `incubated-delivery` instead of
  deciding inside the lane
