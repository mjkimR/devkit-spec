---
id: PLAN-worker-committed-result
spec: SPEC-worker-committed-result
---

# Technical Plan: `SPEC-worker-committed-result` Workers deliver committed, self-contained results

## 1. Constitution & Invariant Review

Two contract statements change, so an ADR comes first (Task 1): `spec-delegate` invariant 5 ("support roles never
touch index or HEAD") and `CAP-DLV-delivery-workflows` business rule 14 ("a role never stages or commits"). The worker
becomes the one role with `commit`; the others keep `[read]`.

## 2. Architecture Overview & Impact

- **Impacted Components**:
  - `docs/decisions/2026-10/20261015-worker-delivers-committed-result.md`: new ADR (accepted).
  - `src/devkit_spec/bundle/subagents/worker.md`: frontmatter (`x-git-actions: [read, commit]`, description, the
    Claude Code host comment), Purpose, Procedure, Return (adds the head commit), Write boundaries (docs paths named in
    `_Boundary:`, spec status through `devkit rules fix`, throwaway data), failure handling.
  - `src/devkit_spec/bundle/skills/spec-delegate/SKILL.md`: invariant 5 names the worker exception; Step 5 worker
    range validation; Step 6 worker fold-back (completed envelope, or failed envelope that blocks).
    `references/payload.md`: the worker row and the recorded heads.
  - `src/devkit_spec/bundle/skills/spec-orchestrate/SKILL.md`: §3 steps 3 and 4, §4 tracking (a worker envelope marks a
    validated or blocked build), §5 return to direct mode (no uncommitted worker changes; blocked units stay blocked).
  - `src/devkit_spec/bundle/skills/spec-tasks/SKILL.md`: boundary bullet for worker tasks.
  - `tests/test_role_contracts.py`: AC-01 to AC-05 assertions.
  - Living Spec (`spec-sync`): `CAP-DLV-delivery-workflows` rule 14, section 4.6 (`x-git-actions`, the worker row and
    paragraph).
- **New Dependencies**: None.

## 3. Error Handling & Edge Cases

- Out-of-scope commit: the range check rejects it; the worker or host adds a commit that reverts it; the next
  validation of the cumulative range passes.
- Commit gate refusal inside the worker: the worker fixes within scope or returns `needs_input`/`failed`; it never
  bypasses the gate (`--no-verify` stays forbidden).
- A worker that leaves uncommitted changes: the clean-worktree check fails the validation.

## 4. Verification & Test Plan

- `just ci` (role contract tests, bundle budgets, skill link checks).
- `devkit rules check --ci --base main`.
