---
id: ADR-worktree-and-pull-request-levels
title: Worktree and pull request policy as auto or required levels
summary: "[tool.spec] worktree and devkit's [worktree] pull_request are auto or required levels instead of booleans, defaulting to auto; booleans are rejected, a pull-request-bound task runs in a worktree, and the handoff guard and scope registration apply in any linked worktree."
status: accepted
created_at: 2026-10-15
---

# [ADR-worktree-and-pull-request-levels] Worktree and pull request policy as auto or required levels

- **Status**: Accepted
- **Date**: 2026-10-15
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `CAP-DLV-project-policy`, `CAP-DLV-proposal-incubation`,
  `CAP-COLL-work-scope-registry`, `ARCH-08-cross-cutting`

---

## 1. Context & Problem Statement

`[tool.spec] worktree` (default `true`) and devkit's `[worktree] pull_request` (default `false`) were switches. A
switch forces one behavior on every task: either every formal task pays for a worktree and every change for a pull
request, or none can be required as a management rule. Agents need to use them when a task needs them, and projects
need to require them when they manage work that way. The location of both keys is settled by
`ADR-policy-in-the-tool-spec-table` and does not change.

---

## 2. Decision Drivers

- Isolation and review overhead follow the task, not a fixed switch.
- A project can still make either one a rule that no agent judgment lowers.
- No external consumers exist, so the format changes in place without a compatibility mapping.

---

## 3. Considered Options

### Option 1: `auto` and `required` levels (Selected)
- **Overview**: two values; `auto` leaves the choice to the agent with stated needs, `required` always applies.
- **Pros**: no value means "never", so a needed worktree or pull request is never blocked by configuration; the
  required case stays a hard policy.
- **Cons**: agents must judge and report `auto` choices.

### Option 2: Keep booleans
- **Overview**: `true` always, `false` never.
- **Pros**: no agent judgment.
- **Cons**: `false` forbids isolation a task needs; `true` charges every task.

### Option 3: Three levels with `off`
- **Overview**: `off`, `auto`, `required`.
- **Pros**: a project can forbid worktrees or pull requests.
- **Cons**: forbidding has no use case found; an unavailable capability (no remote) is a diagnostic, not a policy.

---

## 4. Decision Outcome

We decided to adopt **Option 1**.

- Both keys accept `"auto"` (default) or `"required"`. A boolean is rejected: `SPEC_CONFIG_INVALID` for
  `[tool.spec] worktree`, `WORKTREE_CONFIG_INVALID` for devkit's `pull_request`.
- `worktree = "required"` runs every Route 2, Route 3, Route 4 and bugfix task in a task worktree; S-Lane is never
  required to. `pull_request = "required"` integrates every route, S-Lane included, through a pull request and makes
  devkit refuse `devkit worktree finish --merge`; devkit never opens a pull request itself.
- Under `auto` the agent decides with the needs the `spec` skill's completion reference names and reports each
  choice and its reason in the final change report's assumptions.
- A task that integrates through a pull request runs in a worktree at either worktree level, because the pull
  request path ends with `devkit worktree finish`.
- The handoff branch guard (`SPEC_PROPOSAL_WRONG_WORKTREE`) and the handoff scope registration apply in every linked
  worktree, keyed on where the handoff runs rather than on the level, so worktrees chosen under `auto` stay guarded
  and registered.

**Rationale**: Option 1 lets the default follow the work while keeping a hard rule available, and removing `never`
avoids configuration that blocks a needed worktree or pull request.

---

## 5. Consequences

- **Positive**: small tasks stay in the current checkout by default; projects that manage every change through
  worktrees or pull requests state it explicitly; parallel work chosen under `auto` keeps the registry and guard.
- **Negative / Risks**: a project that relied on the old default `true` changes behavior until it sets
  `worktree = "required"`; this repository sets it.
- **Follow-ups**: the orchestration mode that delegates implementation to workers in per-task worktrees builds on
  these levels.
