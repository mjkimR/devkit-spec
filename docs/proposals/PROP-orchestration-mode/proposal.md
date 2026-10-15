---
id: PROP-orchestration-mode
title: Orchestration mode for delegated implementation
summary: "A user-invoked orchestration mode skill in which the host coordinates worker subagents implementing independent tasks in their own devkit worktrees, with a worker role contract and spec-delegate support for code-writing workers."
status: draft                         # draft | reviewing | accepted | rejected
created_at: 2026-10-15
target_area: delivery/
priority: high                        # critical | high | medium | low
size: M                               # S | M | L | XL
boundaries:
  owns:
    - delivery/
  excludes:
    - docs/decisions/
# handoff_workflow: bugfix            # workflow after handoff (default: direct-delivery)
workflow: incubated-delivery
workflow_hash: sha256:c6cf386f9eb37b061d626d4bc701dd4e01f43674666d160179f69da5c391463e
---

# [PROP-orchestration-mode] Orchestration mode for delegated implementation

## 1. Background & Hypothesis

Retained from `SPEC-git-policy-levels`, which introduced the `auto` and `required` worktree and pull request levels
(`ADR-worktree-and-pull-request-levels`). Every task starts in direct mode: the host implements in the current
checkout or the task's worktree. Larger or parallel work needs the host to switch, for the rest of the session, to
coordinating workers that implement in their own worktrees. Hypothesis: a thin mode skill that states the behavior
and points to the existing procedures (`spec-delegate`, `devkit worktree`, the work-scope registry, `spec-integrate`)
is enough, once a worker contract and a `spec-delegate` extension exist. No strategy setting is configured in advance.

Remaining scope:

- A user-invoked mode skill (`spec-orchestrate`, `invocation = "user"`); returning to direct mode is a plain
  instruction.
- One parallel item is one unit: its own spec bundle and devkit worktree. Task-level fan-out inside one spec is out
  of scope.
- A `worker` role contract that implements inside a given write scope and never stages or commits; the host
  validates the diff in the worker's worktree and commits, keeping the rule that roles never commit.
- `spec-delegate` support for the worker: the role list, the diff comparison in the worker's worktree, and the
  Route 1 no-delegation rule relaxed in orchestration mode.
- Worktrees always come from `devkit worktree start`, never a host-native worktree isolation.
- Implementation stages keep `role: developer`; no workflow stage changes.

Deferred because the levels had to land first, and the worker contract and delegation changes carry more
uncertainty than the policy change.

## 2. Technical Spike Questions

- **Q1**: Which host capabilities (subagent tools, working directory per subagent) let a worker operate in another
  worktree, and how is that stated per host in the contract?
- **Q2**: What does the host verify before committing a worker's result: the diff against the write scope, the
  task's checks, and the scope registry overlaps?
- **Q3**: How does the mode skill stay within the skill byte budget while pointing to the procedures it reuses?

## 3. Proposed Design & Impact

- Bundle: `skills/spec-orchestrate/`, `subagents/worker.md`, `bundle.toml` assets and the core preset.
- `spec-delegate`: worker role, payload and Step 5 diff location; the `spec` router names the mode.
- Living Spec: `CAP-DLV-delivery-workflows` (role rules and table), `CAP-HARN-agent-guidance` (skill list).
- Tests: role contract and workflow projection tests for the new role; bundle budget tests.

## 4. Lifecycle & Retirement Criteria

- Restart condition: `SPEC-git-policy-levels` integrated.
- Expected acceptance checks: one direct-mode task completed without the mode; one orchestrated run with two
  independent units in their own worktrees, each worker result validated and committed by the host and integrated
  in order; a worker diff outside its write scope rejected; `just ci` passes.
- On acceptance: set `status: accepted` and run `devkit spec proposal handoff orchestration-mode`. On rejection:
  record a rejection ADR and delete the proposal directory.
