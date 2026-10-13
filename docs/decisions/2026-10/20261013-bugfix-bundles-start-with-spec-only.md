---
id: ADR-bugfix-bundles-start-with-spec-only
title: Start bugfix spec bundles with spec.md only
summary: A spec bundle bound to the bugfix workflow, from devkit spec new or a proposal handoff, is created with spec.md alone (kind bugfix); plan.md and tasks.md are written in the workflow's plan-tasks stage, so no skeleton has to match criteria that characterization has not produced yet.
status: accepted
created_at: 2026-10-13
---

# [ADR-bugfix-bundles-start-with-spec-only] Start bugfix spec bundles with spec.md only

- **Status**: Accepted
- **Date**: 2026-10-13
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `CAP-DLV-spec-bundles`, `CAP-DLV-proposal-incubation`, `CAP-DLV-delivery-workflows`

---

## 1. Context & Problem Statement

`devkit spec new` and a proposal handoff write skeleton `spec.md`, `plan.md` and `tasks.md` for a feature. The
`bugfix` workflow orders its stages differently: `intent`, `characterize`, `direction`, `plan-tasks`, `reproduce`,
`fix-verify`, then the stages of `direct-delivery`. `characterize` exits on `frontmatter(spec.md kind bugfix)`,
`not-skeleton(spec.md)` and `lint-clean`, and `plan-tasks` writes `plan.md` and `tasks.md`. A skeleton `tasks.md`
present at `characterize` would have to cover the acceptance criteria the characterization produces
(`RULE-task-coverage`, run by `lint-clean`) before anyone has planned the tasks.

---

## 2. Decision Drivers

- Every stage's exit checks can be met by doing that stage's work, in order.
- The bundle exists from the start, so the unit has its anchor and binding.
- What the proposal knew about the target area and boundaries is not lost.

---

## 3. Considered Options

### Option 1: `spec.md` only for `bugfix` (Selected)
- **Overview**: a bundle bound to `bugfix` gets `spec.md` with `kind: bugfix`; a handoff puts the proposal's target
  area and boundaries into a `### Target Area & Boundaries` section of the carried notes.
- **Pros**: `characterize` exits on its own work; `RULE-task-coverage` skips a spec without `tasks.md`.
- **Cons**: bugfix and feature bundles start with different file sets.

### Option 2: All three skeletons, as for features
- **Overview**: the same writer for every workflow.
- **Pros**: one bundle shape.
- **Cons**: `characterize`'s `lint-clean` fails on a placeholder `tasks.md` that cannot match the characterized
  criteria.

### Option 3: No bundle until `plan-tasks`
- **Overview**: characterize in conversation, create files later.
- **Pros**: nothing to skip.
- **Cons**: no anchor, so no binding, no gates and no `devkit workflow next` during the first stages.

---

## 4. Decision Outcome

We decided to adopt **Option 1**.

**Rationale**: it is the only option where the bundle exists from the first stage and every exit check is reachable in
stage order.

---

## 5. Consequences

- **Positive**: `devkit spec new <slug> --workflow bugfix` and a handoff with `handoff_workflow: bugfix` create a
  bundle the `bugfix` stages can drive from `characterize` on.
- **Negative / Risks**: a tool or agent expecting `plan.md` in every new bundle must check the bound workflow.
- **Follow-ups**: none.
