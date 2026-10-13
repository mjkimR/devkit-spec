---
id: ADR-mount-under-the-devkit-command-line
title: Mount the commands under the devkit command line
summary: devkit-spec ships its commands as the devkit spec group through the devkit.commands entry point instead of a separate devkit-spec executable, so agents, hooks and CI use one executable with devkit's loading, output contract and error boundary.
status: accepted
created_at: 2026-10-13
---

# [ADR-mount-under-the-devkit-command-line] Mount the commands under the devkit command line

- **Status**: Accepted
- **Date**: 2026-10-13
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `ARCH-05-1-containers`, `CAP-HARN-command-mount`

---

## 1. Context & Problem Statement

devkit-spec needs commands of its own (`resolve`, `refs`, `list`, `search`, `new`, `proposal`, `entrypoints`, `scope`,
`policy`). Agents, Git hooks and CI already run `uv run devkit ...` from the project environment. devkit offers the
`devkit.commands` entry-point group: an installed package adds a command group to the `devkit` root group, imported
only when its command runs ([Command Plugins](https://github.com/mjkimR/devkit/blob/main/docs/architecture/command-plugins.md)).

---

## 2. Decision Drivers

- One place for an agent to look for every command.
- devkit's startup path (lazy command loading), output options, Agent Advisory Protocol rendering and exit codes
  without reimplementing them.
- No drift between two root command groups.

---

## 3. Considered Options

### Option 1: `devkit spec` through `devkit.commands` (Selected)
- **Overview**: `[project.entry-points."devkit.commands"] spec = "devkit_spec.cli:cli"`; no console script.
- **Pros**:
  - One executable; `devkit --help` lists `spec`.
  - Commands are built on `devkit.core.cli` and inherit devkit's error boundary.
  - An import failure of the plugin fails only `devkit spec` (`COMMAND_PLUGIN_INVALID`).
- **Cons**:
  - The plugin is visible only in the environment devkit-spec is installed in; a separately installed `devkit` tool
    does not see it.
  - `devkit --version` reports devkit only.

### Option 2: A separate `devkit-spec` console script
- **Overview**: `[project.scripts] devkit-spec = ...` with its own root group.
- **Pros**: independent of devkit's plugin loading.
- **Cons**: duplicates the root group, its options and its boundary; two executables for agents and hooks to find;
  the two groups drift.

### Option 3: `python -m devkit_spec`
- **Overview**: a module entry point only.
- **Pros**: no entry point needed.
- **Cons**: not discoverable from `devkit --help`; agents and hooks would need a second invocation convention.

---

## 4. Decision Outcome

We decided to adopt **Option 1**.

**Rationale**: it satisfies all three drivers with no code of its own beyond the click group, and its only cost (the
plugin is environment-bound) matches how projects already run devkit (`uv run devkit`).

---

## 5. Consequences

- **Positive**: every command keeps devkit's output contract (`ARCH-08-cross-cutting`); `devkit spec` is imported only
  when it runs, so built-in commands never pay for it.
- **Negative / Risks**: the `spec` name is reserved for this plugin by convention; a broken install surfaces as
  `COMMAND_PLUGIN_INVALID` on `devkit spec` only.
- **Follow-ups**: devkit-spec reports its own version under its group: `devkit spec --version` prints
  `[VERSION: devkit-spec <version>]`.
