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
  - **Finding**: no host gives a subagent its own working directory. On Claude Code the worker shares the session's
    directory, so the payload carries the worktree's absolute path and the contract requires absolute paths and
    `git -C <worktree>` for every read, write and command; the host must already allow that path (a sibling
    `<base>-wt-<slug>` can sit outside the session's allowed directories). Codex `workspace-write` confines writes to
    the project root, which excludes a sibling worktree, so the worker is `unsupported` there and the main session
    substitutes. Antigravity is `unverified` (inference: no documented working-directory control). The guarantee is
    the post-run diff in the worker's worktree, as for the reconciler. These statuses are the starting point;
    portable worktree access across hosts is investigated separately in `PROP-worktree-host-compatibility`.
- **Q2**: What does the host verify before committing a worker's result: the diff against the write scope, the
  task's checks, and the scope registry overlaps?
  - **Finding**: in the worker's worktree, `git -C <worktree> status --short` and `diff --name-only` (unstaged and
    cached) stay inside the injected write scope with the index and HEAD unchanged; the host then runs the task's
    checks there, stages only the agreed paths, runs `devkit rules check --staged`, commits with `git -C <worktree>
    commit`, and runs `devkit spec scope update --spec <dir>`; `devkit spec scope query` overlaps decide the
    integration order. A path outside the scope is reverted and the whole result is re-delegated or substituted.
- **Q3**: How does the mode skill stay within the skill byte budget while pointing to the procedures it reuses?
  - **Finding**: the mode skill holds the switch, the per-unit loop and the return to direct mode (about 4 KB) and
    links the existing procedures instead of repeating them. `spec` (7632 of 7680 bytes) and `spec-delegate` (7418 of
    7680) have no room: the router gets no new row (the constitution names the mode skill), and `spec-delegate` moves
    its per-role payload table to a reference before adding the worker row.

## 3. Proposed Design & Impact

- **Division of work**: the host keeps every gate and planning step of each unit (G1, G2, `spec.md`, `plan.md`,
  `tasks.md`, review, Living Spec sync, G3 and integration); a worker implements only the `build-verify` tasks of
  one unit inside its worktree. Planning needs the user's gates, so it stays with the host.
- **Mode skill** `skills/spec-orchestrate/SKILL.md` (`invocation = "user"`): when to propose the switch, the loop
  per unit (start the worktree and bundle, plan, delegate the build, validate and commit, review and sync, integrate
  in overlap order), and the return to direct mode by a plain instruction.
- **Worker contract** `subagents/worker.md`: write scope injected per task (the unit's `_Boundary:` paths inside the
  worktree), `x-git-actions: [read]`, absolute paths and `git -C`; Claude Code `native` with Read, Grep, Glob, Write,
  Edit and Bash; Codex `unsupported`; Antigravity `unverified`.
- **`spec-delegate`**: the worker in the role list and payload (worktree path, write scope, task list, checks to
  run), Step 5 compares the diff in the worker's worktree, and Step 1 allows the worker in orchestration mode on any
  route; the per-role payload table moves to `references/payload.md` for room.
- **Constitution** (`bundle/AGENTS.md` §3): one sentence naming the user-invoked mode skill.
- Bundle: `bundle.toml` assets and the core preset. Implementation stages keep `role: developer`.
- Living Spec: `CAP-DLV-delivery-workflows` (role rules and table, rule 14 unchanged), `CAP-HARN-agent-guidance`
  (skill list), `ARCH-05-1-containers` (skill and role counts).
- Tests: `tests/test_role_contracts.py` and `tests/test_workflows.py` role tuples, bundle budget and link tests.

## 4. Lifecycle & Retirement Criteria

- Restart condition: `SPEC-git-policy-levels` integrated.
- Expected acceptance checks: one direct-mode task completed without the mode; one orchestrated run with two
  independent units in their own worktrees, each worker result validated and committed by the host and integrated
  in order; a worker diff outside its write scope rejected; `just ci` passes.
- On acceptance: set `status: accepted` and run `devkit spec proposal handoff orchestration-mode`. On rejection:
  record a rejection ADR and delete the proposal directory.
