---
id: PLAN-orchestration-mode
spec: SPEC-orchestration-mode
---

# Technical Plan: `SPEC-orchestration-mode` Orchestration mode for delegated implementation

## 1. Constitution & Invariant Review

None. `CAP-DLV-delivery-workflows` rule 14 (a role never stages or commits) holds: the worker writes files only and
the host commits. Implementation stages keep `role: developer`, so no workflow hash or shared-stage contract changes.
`ADR-worktree-and-pull-request-levels` stays as decided; worktrees come from `devkit worktree start`.

## 2. Architecture Overview & Impact

- **Impacted Components**:
  - `src/devkit_spec/bundle/skills/spec-orchestrate/SKILL.md` (new): the mode skill.
  - `src/devkit_spec/bundle/subagents/worker.md` (new): the worker contract.
  - `src/devkit_spec/bundle/skills/spec-delegate/SKILL.md` and `references/payload.md` (new): worker role, payload
    table moved out, Step 1 and Step 5 for the worker.
  - `src/devkit_spec/bundle/bundle.toml`: two assets, the skill with `invocation = "user"`, both in `presets.core`.
  - `src/devkit_spec/bundle/AGENTS.md` §3: one sentence naming the mode skill.
  - Tests: `tests/test_role_contracts.py` (worker contract, payload table in the reference), `tests/test_workflows.py`
    (worker projection without a Codex file).
- **New Dependencies**: None.

## 3. Verification & Test Plan

- Unit: contract frontmatter and body assertions for `worker`; payload rows read from `references/payload.md`.
- Integration: the synced project in `tests/test_workflows.py` projects `worker` for Claude Code and Antigravity
  only; `devkit workflow validate` still reports roles checked.
- Commands: `just ci`; `wc -c` on `spec-delegate/SKILL.md` (at most 7680) and the new skill.
