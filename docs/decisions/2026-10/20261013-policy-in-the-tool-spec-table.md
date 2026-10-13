---
id: ADR-policy-in-the-tool-spec-table
title: Keep project policy in devkit's tables and [tool.spec]
summary: Policy devkit already models (approval gates, stage switches, worktree integration) stays in devkit's configuration tables; only spec-driven settings (worktree routing, namespaces, the scope registry) live in [tool.spec], and agents read the effective policy through devkit spec policy.
status: accepted
created_at: 2026-10-13
---

# [ADR-policy-in-the-tool-spec-table] Keep project policy in devkit's tables and [tool.spec]

- **Status**: Accepted
- **Date**: 2026-10-13
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `ARCH-08-cross-cutting`, `CAP-DLV-project-policy`

---

## 1. Context & Problem Statement

specrig read its policy from `.specrig/config.yml`: approvals per gate, the feedback sweep, pull requests, branch
cleanup and `git.worktree` (which routes run in a task worktree). In devkit, `.devkit/config.toml` already models most
of it: `[workflow.approvals]` (gate policy `ask`, `auto`, `off`), `[workflow.stages]` (switching a stage off) and
`[worktree]` (`pull_request`, `delete_branch`, `setup`). devkit passes `[tool.<name>]` tables through unread. Where
does devkit-spec's remaining policy go, and how do agents read the whole?

---

## 2. Decision Drivers

- One source of truth per setting: devkit's engines must act on the same value the agent reads.
- No second configuration file.
- Agents read effective policy (defaults applied) through a command, never by parsing TOML.

---

## 3. Considered Options

### Option 1: devkit's tables for what devkit models, `[tool.spec]` for the rest (Selected)
- **Overview**: approvals, stage switches and worktree integration stay in devkit's tables; `[tool.spec]` holds
  `worktree`, `[[tool.spec.namespaces]]` and `[tool.spec.scope]`; `devkit spec policy` prints the effective values
  of both.
- **Pros**: devkit's workflow and worktree engines read their own settings; no duplicate keys.
- **Cons**: policy spans several tables, which is why the policy command exists.

### Option 2: Everything in `[tool.spec]`
- **Overview**: mirror approvals and worktree settings under `[tool.spec]`.
- **Pros**: one table for devkit-spec users.
- **Cons**: two sources of truth for the same setting; devkit's engines would not see the mirrored values.

### Option 3: A devkit-spec configuration file
- **Overview**: keep a `.specrig/config.yml`-like file.
- **Pros**: closest to specrig.
- **Cons**: a second file to find, validate and keep consistent with devkit's.

---

## 4. Decision Outcome

We decided to adopt **Option 1**.

**Rationale**: it is the only option with one source of truth per setting, and `devkit spec policy` gives agents the
single view Option 2 aimed for.

---

## 5. Consequences

- **Positive**: `[GATE_POLICY ...]`, `[STAGE_POLICY ...]` and `[GIT_POLICY ...]` lines reflect exactly what devkit's
  engines use, with `source=config|default`.
- **Negative / Risks**: a malformed `[tool.spec]` is `SPEC_CONFIG_INVALID`; in a rule run it fails the run (devkit's
  `RULES_EXECUTION_FAILED`, exit `2`) instead of being a violation.
- **Follow-ups**: specrig's mapping: approvals to `[workflow.approvals]` (`ADR-approval-gates-intent-direction-integration`),
  the feedback sweep to `[workflow.stages]` (`collect-feedback`), `pull_request` and branch cleanup to `[worktree]`,
  `git.worktree` to `[tool.spec] worktree`.
