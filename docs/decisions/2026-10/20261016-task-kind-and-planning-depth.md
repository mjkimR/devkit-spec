---
id: ADR-task-kind-and-planning-depth
title: Classify work by task-kind and planning-depth instead of routes
summary: Work is classified on task-kind, planning-depth and activity-effort instead of Routes 1 to 4; workflows are named sdd-<planning-depth>[-<task-kind>], gates plan-intent, plan-accept and dev-integration, and Development has no direction gate.
status: accepted
created_at: 2026-10-16
---

# [ADR-task-kind-and-planning-depth] Classify work by task-kind and planning-depth instead of routes

- **Status**: Accepted
- **Date**: 2026-10-16
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `CAP-DLV-delivery-workflows`, `CAP-DLV-proposal-incubation`,
  `CAP-DLV-spec-bundles`, `CAP-DLV-project-policy`, `CAP-HARN-agent-guidance`

---

## 1. Context & Problem Statement

Routes 1 to 4 mixed two questions in one name: what the work does (only `bugfix` said that) and what must be settled
before implementation (the rest). Proposals already combined them through `handoff_workflow`. The gates were numbered
(G1, G2, G3) while the engine and the UI used names, and Development carried a direction gate that stopped work for
choices the agreed intent already covered. The strategy layer's master flow (workbench `docs/strategy-layer/01-master-flow.md`)
settles the replacement; this record keeps the decision in devkit-spec's Living Spec.

---

## 2. Decision Drivers

- One axis per question, so each combination maps to exactly one workflow without conditional stages.
- Fewer stops: inside the agreed goal, scope and contract the executor decides; only a problem that breaks the
  agreement stops the work.
- Approvals keep their meaning across a handoff: a proposal's acceptance is never re-labelled as another decision.
- Structure is the record: the Unit's kind and its bound workflow show the axes, so no field can disagree with them.

---

## 3. Considered Options

### Option 1: Three axes and named gates (Selected)
- **Overview**: `task-kind` (`feature`, `bugfix`), `planning-depth` (`session`, `spec`, `proposal`) and
  `activity-effort` (`low`, `medium`, `high`); workflows `sdd-session-feature`, `sdd-session-bugfix`,
  `sdd-spec-feature`, `sdd-spec-bugfix`, `sdd-proposal`; gates `plan-intent`, `plan-accept` (always the user's, no
  policy key) and `dev-integration` (`ask` or `auto`); no Development direction gate. The handoff target is
  `sdd-spec-<task_kind>`, read from the proposal's `task_kind`, the only axis value stored as a field because a
  proposal is not yet bound to its spec workflow; `spec.md` has no `kind` field. The handoff carries
  `gate:plan-intent` and `gate:plan-accept` under their own names.
- **Pros**: each axis answers one question; the gate names match the engine's request ids; a `session` task needs no
  Unit at any effort.
- **Cons**: every workflow id, gate name and skill text changes at once.

### Option 2: Keep the routes and rename only the gates
- **Overview**: Routes 1 to 4 stay, G1/G2/G3 become names.
- **Pros**: smaller change.
- **Cons**: the mixed axis stays, and the Development direction gate keeps stopping work.

---

## 4. Decision Outcome

Option 1. `ADR-handoff-workflow-key` is superseded: `handoff_workflow` is replaced by `task_kind`. The approval-gate
semantics of `ADR-integration-approval-asserted` stay, under the name `dev-integration`. Planning's question rounds,
the structured question, answer, problem and resolution envelopes and the blocked state rest on devkit envelope
contracts that are adopted separately.

---

## 5. Consequences

- `devkit spec new --workflow` takes `sdd-spec-feature` (default) or `sdd-spec-bugfix`; `devkit spec proposal new`
  takes `--task-kind`, `--supersedes` and `--needs-decompose`; `devkit spec proposal handoff` requires
  `status: accepted` and refuses `needs_decompose: true`.
- `devkit spec policy` refuses a policy key for `plan-intent` or `plan-accept` and `dev-integration = "off"`, and
  reports `[tool.spec] depth_escalation`.
- The worker role splits into a `planning-worker` and a `development-worker` that write their own records and commit
  at stage boundaries; the reconciler verifies the implementer's reconcile at `activity-effort` `high` instead of
  drafting it.
- Completed specs bound to the retired workflow ids keep their binding as history.
