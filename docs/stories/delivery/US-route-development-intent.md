---
id: US-route-development-intent
title: Route a Development Request to the Right Workflow
summary: An AI coding agent classifies a user's development request by task-kind, planning-depth and activity-effort under the project's policy, plans it inline or as a proposal, and follows the matching workflow's stages and gates.
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
- **I want to**: classify a development request by what it does (`task-kind`) and what must be settled before
  implementation (`planning-depth`), confirm it with the user and drive the matching workflow from intent to
  integration
- **So that**: work that needs nothing settled stays light, contract changes get a spec, open directions get a
  proposal, and every approval the user owns is asked at the right moment instead of being inferred or skipped

---

## 2. Background & Context

The agent loads the constitution with `devkit get-context spec`, enters through the `spec` skill (`/spec <intent>`)
and reads `devkit spec policy` before classifying. A `session` task runs `sdd-session-feature` or
`sdd-session-bugfix` in the session without a work unit; a `spec` task creates a spec bundle with `devkit spec new` in
inline Planning (`--workflow sdd-spec-bugfix` for a defect); a `proposal` task starts as a draft proposal. From then on
`devkit workflow next --unit <dir>` names the stage, its unmet checks and the skill to open; `plan-intent` and
`plan-accept` are always the user's and `dev-integration` follows `[workflow.approvals]`.

---

## 3. Acceptance Criteria (Given / When / Then)

### Scenario 1: A contract change becomes a bound spec bundle
- **Given**: the policy reports `[GIT_POLICY: worktree=auto ...]`, the agent keeps the task in the current checkout,
  and the request changes a documented contract with a clear direction
- **When**: the agent runs `devkit spec new <slug>`
- **Then**: `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` holds skeleton-marked `spec.md`, `plan.md` and `tasks.md`,
  `spec.md` is bound to `sdd-spec-feature` with no `kind` field, and the output ends with
  `[NEXT_CMD: devkit workflow next --unit <dir>]`

### Scenario 2: `plan-intent` always waits for the user
- **Given**: `[GATE_POLICY: plan-intent policy=ask source=fixed]` and a freshly created bundle
- **When**: the agent runs `devkit workflow next --unit <dir>`
- **Then**: the output shows `[WAITING: human gate:plan-intent]`, and the agent records
  `devkit workflow answer --unit <dir> --request gate:plan-intent --action accept` only after the user's explicit
  answer; a `[workflow.approvals]` key for `plan-intent` makes `devkit spec policy` fail with `SPEC_CONFIG_INVALID`

### Scenario 3: A defect with a spec takes the spec bugfix workflow
- **Given**: an observed behavior contradicts an existing contract and its current, expected and preserved behavior
  must be written down
- **When**: the agent runs `devkit spec new <slug> --workflow sdd-spec-bugfix`
- **Then**: the bundle holds only `spec.md`, bound to `sdd-spec-bugfix`, and the `reproduce` stage stays open until a
  `red` envelope records `checks.reproduced`

### Scenario 4: A session that needs a contract change is raised to `spec`
- **Given**: a `session` task turns out to need a contract change or a Living Spec change during Development
- **When**: the agent raises its depth (`[ROUTING_POLICY: depth_escalation=auto]`)
- **Then**: it adds a spec Unit with `devkit spec new <slug>` in the current work environment, records the agreed
  intent and the work so far and continues from the workflow's next stage, keeping the changes made so far
