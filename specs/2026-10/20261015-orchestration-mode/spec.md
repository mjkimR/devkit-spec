---
id: SPEC-orchestration-mode
title: Orchestration mode for delegated implementation
summary: "A user-invoked orchestration mode skill in which the host coordinates worker subagents implementing independent tasks in their own devkit worktrees, with a worker role contract and spec-delegate support for code-writing workers."
status: completed
created: 2026-10-15
related_capabilities:
  - CAP-DLV-delivery-workflows
  - CAP-HARN-agent-guidance
related_stories: []
workflow: direct-delivery
workflow_hash: sha256:6fe2644b9464ea860e6d6928748778b4ffd7a255e92ddea5fe10eba59138f287
---
# [SPEC-orchestration-mode] Orchestration mode for delegated implementation

## 1. Problem Statement & Motivation

Every task starts in direct mode: the host implements in the current checkout or the task's worktree. Larger or
parallel work needs the host to switch, for the rest of the session, to coordinating workers that implement in their
own worktrees. The bundle has no write-capable implementation role, `spec-delegate` allows only four read-only or
docs-only roles and compares diffs in the current checkout, and nothing tells the host how to run several units.
Strategy is not configured in advance; the user switches modes, and a thin skill saves retyping the instruction.

Handed off from the orchestration-mode proposal; spike findings are kept in section 5.

## 2. User Stories

- As a developer, I want to switch the session into orchestration mode with one skill call and back with a plain
  instruction, so the host coordinates workers only when the work warrants it.
- As the host agent, I want a worker contract and delegation procedure for code-writing workers in their own
  worktrees, so I can validate and commit each worker's result without giving the worker Git authority.

## 3. Non-Goals

1. **Scope Excluded**: worker support on Codex and Antigravity beyond the contract's host statuses, and any change
   to where worktrees live or how hosts grant directory access; `PROP-worktree-host-compatibility` investigates them.
2. **Scope Excluded**: task-level fan-out inside one spec bundle; one parallel item is one unit with its own bundle
   and worktree.
3. **Scope Excluded**: workflow stage changes; implementation stages keep `role: developer`, so direct mode never
   receives a worker `[DELEGATE]`.
4. **Scope Excluded**: a recorded live orchestrated run with two units. The first orchestrated task validates the
   procedure; this change is checked by its contracts and tests.

## 4. Acceptance Criteria & Behavioral Contracts

### [AC-01] User-invoked mode skill

- **Given** the spec bundle after `devkit sync`
- **When** an agent lists the bundle's skills and reads `spec-orchestrate`
- **Then** the skill is declared with `invocation = "user"` in the core preset, its `SKILL.md` is at most 8192 bytes
  with every relative link resolving, and it states: when the host proposes the switch, the per-unit loop (worktree
  and bundle, host-owned gates and planning, worker build, host validation and commit, review and sync, integration
  in overlap order), and that a plain instruction returns the session to direct mode.

### [AC-02] Worker role contract

- **Given** `subagents/worker.md` in the bundle
- **When** the contract is parsed and `devkit sync` projects the roles
- **Then** its role is `worker` with `x-git-actions: [read]`, Claude Code status `native` with Read, Grep, Glob,
  Write, Edit and Bash, Codex `unsupported`, Antigravity `unverified`; `.claude/agents/worker.md` and
  `.agents/agents/worker.md` exist and no `.codex/agents/worker.toml` is written; the body requires absolute paths
  and `git -C <worktree>`, writes only inside the injected write scope and forbids staging and committing.

### [AC-03] Delegating to a worker

- **Given** the `spec-delegate` skill and its references
- **When** the host delegates a unit's build to a worker in orchestration mode
- **Then** the role list includes `worker`; the payload reference has a `worker` row (worktree path, write scope,
  `tasks.md`, checks to run); Step 1 allows the worker on any route in orchestration mode only; Step 5 compares the
  diff with `git -C <worktree>` in the worker's worktree, reverts any path outside the write scope and rejects the
  whole result; the host stages, checks and commits; `spec-delegate/SKILL.md` stays at most 7680 bytes.

### [AC-04] Guidance and Living Spec

- **Given** the constitution and the Living Spec after the change
- **When** an agent reads `devkit get-context spec` or the delivery and guidance capabilities
- **Then** the constitution names the user-invoked `spec-orchestrate` mode; `CAP-DLV-delivery-workflows` lists the
  worker in its role table and keeps the rule that a role never stages or commits; `CAP-HARN-agent-guidance` and
  `ARCH-05-1-containers` count 13 skills and five role contracts.

### [AC-05] Checks

- **Given** the change
- **When** `just ci` runs
- **Then** it passes, including the role-contract tests extended to `worker` and the bundle budget and link tests.

## 5. Spike Findings

- No host gives a subagent its own working directory. On Claude Code the worker shares the session's directory,
  so it uses absolute paths and `git -C <worktree>`, and the session must already allow the worktree path. Codex
  `workspace-write` confines writes to the project root, which excludes a sibling worktree, so the main session
  substitutes there. Antigravity has no documented working-directory control (inference). The post-run diff in the
  worker's worktree is the guarantee.
- Before committing a worker's result the host checks the diff in the worktree against the write scope with the
  index and HEAD unchanged, runs the task's checks there, stages only the agreed paths, runs `devkit rules check
  --staged`, commits with `git -C <worktree> commit`, and updates the scope registry; overlaps decide integration
  order.
- `spec` and `spec-delegate` have no byte headroom: the router gets no new row (the constitution names the mode),
  and `spec-delegate` moves its per-role payload table to a reference.
