---
id: ARCH-01-introduction-and-goals
title: Introduction & Goals
summary: Mission, goals, non-goals, quality goals and stakeholders of devkit-spec, the spec-driven development layer for AI coding agents built on devkit.
status: active
created_at: 2026-10-13
---

# [ARCH-01-introduction-and-goals] Introduction and Goals

- **arc42**: §1 Introduction and Goals
- System context: `ARCH-03-context`. Building blocks: `ARCH-05-1-containers`, `ARCH-05-2-components`.

---

## 1. Mission

devkit-spec adds spec-driven development to [devkit](https://github.com/mjkimR/devkit). An AI coding agent working in
a project that installs it develops through one model:

- `docs/` is the durable **Living Spec**: capabilities, stories, architecture and decisions describing the current
  contract (`CAP-DOCS-document-model`);
- `specs/` holds **feature specs** (spec bundles) that carry each change (`CAP-DLV-spec-bundles`), and
  `docs/proposals/` holds **proposals** that incubate uncertain work (`CAP-DLV-proposal-incubation`);
- every change follows a **routed delivery workflow** with approval gates (`CAP-DLV-delivery-workflows`) and is
  **reconciled** into `docs/` before it is reported done.

devkit-spec is one Python package with two halves: the `spec` bundle of agent assets, deployed by `devkit sync`, and
the `devkit spec` command group, mounted into devkit's command line (`ARCH-05-1-containers`). Everything that is not
specific to spec-driven development (distribution, rule, workflow and gate engines, ranking, task worktrees, the Agent
Advisory Protocol) is devkit's (`ADR-rebuild-specrig-on-devkit`).

### 1.1 Problem and Hypothesis

- **Situation**: AI coding agents start each session without memory of earlier decisions, read documents literally
  and work in parallel worktrees.
- **Problem**: documentation drifts from code, decisions are re-litigated, references break silently, and parallel
  tasks collide late.
- **Hypothesis**: a document model with stable IDs, deterministic rules, routed workflows with explicit gates and a
  reconciliation step keeps the written contract current enough that an agent can trust it as its starting point.
- **Success criteria**: `devkit rules check` reports no violation on a reconciled repository; an agent finds the
  governing document of a question through `devkit spec search` or `devkit spec resolve` without reading the tree;
  every completed spec bundle has a resolved `reconcile.md`.

### 1.2 Goals

1. **Findable, trustworthy Living Spec**: documents identified by full IDs, resolvable references, English summaries
   for search, namespaces for monorepos (`US-find-the-right-documents`).
2. **Mechanically kept consistency**: spec rules run locally, in the commit gate and in CI
   (`US-keep-the-living-spec-consistent`).
3. **Routed delivery**: the agent chooses a route by uncertainty, contract impact and risk and follows the workflow's
   stages and gates (`US-route-development-intent`, `US-incubate-and-hand-off-a-proposal`).
4. **Safe parallel work**: declared work scopes are compared and shared between worktrees before overlapping work
   runs (`US-run-parallel-work-safely`).
5. **Adoption through sync**: installing the package and running `devkit sync` is the whole setup
   (`US-adopt-in-an-existing-repository`).

### 1.3 Non-Goals

| Non-Goal Item | Scope Excluded | Rationale |
| :--- | :--- | :--- |
| Generic engines | Asset distribution, rule evaluation, workflow state, commit hooks, ranking, worktree management | devkit owns them; devkit-spec uses its public surface (`ADR-rebuild-specrig-on-devkit`). |
| A second executable | A `devkit-spec` console script or a platform binary | `ADR-mount-under-the-devkit-command-line`. |
| Exclusive ownership of work | Claims, write blocking, heartbeats, automatic expiry of scope records | The registry detects overlaps; it never grants or blocks a write (`CAP-COLL-work-scope-registry`). |
| Windows and network file systems | Running on Windows; a scope registry on NFS or SMB | The registry relies on `flock` and atomic rename. |
| Human-oriented rendering | Colour, tables, progress output, a web viewer or a derived-data cache | The primary consumer is an agent (`ARCH-08-cross-cutting`). |
| Semantic proof | Proving that code implements a document, or that two tasks will not conflict | Entrypoints and scope overlaps are joins of declarations, not proofs. |

---

## 2. Quality Goals

| Priority | Quality Attribute | Motivation & Scenario |
| :--- | :--- | :--- |
| 1 | **Agent-first output** | Every command prints one-line sentinels or one JSON object on stdout, advisories with stable `SPEC_` codes on stderr, exit codes `0`/`1`/`2`. An agent branches on codes, never on message text (`ARCH-08-cross-cutting`). |
| 2 | **Determinism** | The document index is rebuilt from the files on every load; rules evaluate exactly the staged or CI snapshot; the same tree gives the same verdict locally, in the commit gate and in CI. |
| 3 | **Safety of writes** | `spec new` and `proposal handoff` validate before the first write and roll back on failure; `entrypoints derive --apply` changes only the `entrypoints` block; scope records are published atomically; nothing deletes more than it owns (`proposal prune` removes only empty directories). |
| 4 | **No binary** | One pure Python wheel (`py3-none-any`): no platform builds, no Go toolchain in consumer projects, no macOS CI minutes (`ADR-rebuild-specrig-on-devkit`). |
| 5 | **One executable** | Agents, hooks and CI reach every command through the project environment's `devkit` (`uv run devkit spec ...`), with devkit's lazy loading, output contract and error boundary (`ADR-mount-under-the-devkit-command-line`). |

---

## 3. Key Stakeholders & Users

| Stakeholder / User Group | Role & Concerns | Key System Interactions |
| :--- | :--- | :--- |
| **AI coding agent** (primary) | Executes routed work; needs deterministic output, stable codes and the governing documents of a change | `devkit get-context spec`, the `spec*` skills, `devkit spec ...`, `devkit workflow next`, `devkit rules check` |
| **Developer (user)** | States intent, answers `ask` gates, authorizes commits, merges and deletions | `/spec <intent>`, `devkit workflow answer`, the final change report |
| **Consumer project / team** | Adopts the bundle, sets policy, owns its Living Spec | `uv add --dev devkit devkit-spec`, `devkit sync`, `.devkit/config.toml` (`CAP-DLV-project-policy`) |
| **devkit-spec maintainer** | Evolves the bundle, the commands and this Living Spec; dogfoods the bundle in this repository | [Development workflow](../development/workflow.md) |
| **devkit maintainers** | Own the foundation; receive the generic capabilities devkit-spec needs | devkit's public surface and command plugin contract (`ARCH-03-context`) |
| **CI runner** | Re-runs the checks as the final gate of an integration | `just ci`, `devkit rules check --ci --base <ref>` ([CI](../development/ci-cd.md)) |
