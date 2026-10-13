---
name: spec-tasks
description: Decompose the technical plan into independently verifiable tasks in tasks.md, each with its expected file scope (_Boundary:) and the acceptance criteria it serves (_Requirements:).
---

# spec-tasks: Task Breakdown Workflow

Use this skill once `spec.md` and `plan.md` exist (the `specify` stage of workflow `direct-delivery`, the `plan-tasks` stage of workflow `bugfix`). The goal is a short list of tasks that each produce a verifiable result, so progress and coverage are visible without re-reading the whole plan.

---

## 1. Prerequisites & Inputs

- The specification at `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/spec.md`.
- The technical plan at `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/plan.md`.
- The skeleton `tasks.md` beside them (written by `devkit spec new` or `devkit spec proposal handoff`).

---

## 2. Work Breakdown Principles

- **One verifiable result per task**: a task is a unit that can be implemented and checked on its own. Keep the code and its tests in the same task when they change together; split when one part can be verified without the other.
- **Expected scope (`_Boundary:`)**: every task names the paths it is expected to touch. A long list may wrap onto lines indented deeper than the label line, its entries still separated by commas; a blank line, a list item or any line not indented deeper ends it. It is a scope estimate, not a lock: a change that turns out to need another path goes ahead and is explained in the report. It is strict for a delegated task through the `spec-delegate` write scope.
- **Acceptance links (`_Requirements:`)**: every task links the scenarios it serves on a direct child line indented two spaces, `- _Requirements: AC-01, AC-02_` (`RULE-task-coverage`); every `[AC-NN]` in `spec.md` is covered by at least one task, and a task cites only IDs the spec defines. A `_Requirements:_` line in a table, prose or under a non-task item covers nothing.
- **Optional markers, when they help**: a `**Verification**` command when the check is not obvious from the boundary and phase headings when the list is long enough to need grouping.

Progress is computed from the checkboxes (`devkit spec list spec` shows `tasks=<checked>/<total>`, `devkit workflow next --unit <dir>` evaluates `tasks-all-checked`); do not write task counts.

Tasks hold implementation and verification work only. Review (`spec-review`) and Living Spec sync (`spec-sync`) are workflow stages judged by envelopes and `reconcile.md`; a task for them would have to be checked before it happens, because `tasks-all-checked` opens the `review-refine` stage. Likewise the Red and Green envelopes of a bugfix are stage evidence, not tasks; the reproduction test itself is a task.

---

## 3. Tasks Output Standard

Rewrite `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/tasks.md`, keeping its `id`, `spec` and `plan` frontmatter:

```markdown
---
id: TASKS-<feature-slug>
spec: SPEC-<feature-slug>
plan: PLAN-<feature-slug>
---

# Task Breakdown: `SPEC-<feature-slug>` <Feature Title>

- [ ] **Task 1**: Domain types and validation, with unit tests
  - **_Boundary**: `src/app/domain/types.py`, `tests/domain/test_types.py`
  - _Requirements: AC-01_
- [ ] **Task 2**: CLI command wiring and its error output
  - **_Boundary**: `src/app/cli/run.py`, `tests/cli/test_run.py`
  - _Requirements: AC-01, AC-02_
  - **Verification**: `just test tests/cli/test_run.py`
```

---

## 4. Definition of Done (DoD) for Task Breakdown
- [ ] Every task produces a result that can be checked on its own.
- [ ] Every task has a `_Boundary:` line and a `_Requirements:` line; every acceptance scenario is covered (`devkit rules check <dir>` reports no `RULE-task-coverage` violation).
- [ ] No review or sync task: those are workflow stages, not tasks.
- [ ] The skeleton marker line `<!-- devkit:skeleton -->` is removed from `tasks.md`.
- [ ] In a registered task worktree, `devkit spec scope update --spec <dir>` gave the registry the task boundaries (`SPEC_SCOPE_TOKEN_MISSING`: not registered, skip). `[SCOPE_ACK]` overlaps inform the orchestrator; they are not a gate.
- [ ] `devkit workflow next --unit <dir>` shows the exit of `specify` (or `plan-tasks`) met: no skeleton marker left in the planning files and `lint-clean`; otherwise it names what is still unmet.
