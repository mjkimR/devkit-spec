---
id: ADR-rebuild-spec-on-devkit
title: Rebuild spec-driven development as a Python layer on devkit
summary: Build devkit-spec as a pure Python package on devkit that keeps only the spec-driven document model and methodology, while devkit stays SDD-agnostic and owns every generic engine.
status: accepted
created_at: 2026-10-13
---

# [ADR-rebuild-spec-on-devkit] Rebuild spec-driven development as a Python layer on devkit

- **Status**: Accepted
- **Date**: 2026-10-13
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `ARCH-03-context`, `ARCH-05-1-containers`, `CAP-HARN-agent-guidance`, `CAP-GOV-spec-rules`

---

## 1. Context & Problem Statement

Spec-driven development was originally delivered as a standalone Go CLI: its own installer and managed directory,
its own rule runner, workflow engine, commit command, worktree commands, search and a web viewer, shipped as one
executable per platform. devkit has since become the foundation for agent tooling with the same generic engines:
asset distribution, rules, workflows, commit gates, search, worktrees and the Agent Advisory Protocol. Keeping both
meant two implementations of every engine, two output contracts, platform builds and macOS runner minutes in CI.

---

## 2. Decision Drivers

- No second implementation of a generic engine devkit already has.
- devkit stays SDD-agnostic: the document model and its rules never move into devkit.
- No platform binaries and no Go toolchain in consumer projects.
- One agent-first output contract and one advisory format across all commands.
- CI cost of private runners (no macOS builds).

---

## 3. Considered Options

### Option 1: Python layer on devkit (Selected)
- **Overview**: a Python package that ships the methodology as a devkit bundle and the SDD commands as a devkit command
  group; everything generic comes from devkit's public surface.
- **Pros**:
  - One pure wheel (`py3-none-any`); no platform builds.
  - devkit's distribution, rule engine, workflow engine, gate, search and worktrees are reused as they are.
  - One output contract and error boundary.
- **Cons**:
  - devkit-spec follows devkit's minor versions and breaking changes.
  - Behaviour that depended on the standalone CLI's commands has to be reshaped where devkit cannot call devkit-spec.

### Option 2: Keep standalone Go CLI next to devkit
- **Overview**: keep the Go CLI and let projects install both.
- **Pros**: no porting work.
- **Cons**: every engine twice; two receipts, two hook systems, two output contracts; platform builds remain.

### Option 3: Move spec-driven development into devkit
- **Overview**: add the document model, rules and workflows to devkit itself.
- **Pros**: one package.
- **Cons**: devkit stops being SDD-agnostic; every devkit consumer receives one methodology's rules and commands.

### Option 4: Port to Python as a standalone tool
- **Overview**: a one-to-one Python rewrite with its own distribution and engines.
- **Pros**: no dependency on devkit.
- **Cons**: duplicates devkit as Option 2 does, only in another language.

---

## 4. Decision Outcome

We decided to adopt **Option 1**.

**Rationale**: it removes the duplicate engines and the platform builds while keeping devkit SDD-agnostic. devkit-spec
keeps only what is spec-driven: the document model (kinds, directories, ID grammar, frontmatter, references,
namespaces), the methodology (routes, workflow definitions, stage skills, role contracts, templates, docs skeleton,
reconciliation) and the policy that turns devkit's engines into SDD behaviour (which rules run, which checks gate a
stage, how search scopes and pins documents, which routes run in a worktree).

---

## 5. Consequences

- **Positive**: one wheel and one executable (`ADR-mount-under-the-devkit-command-line`); devkit's targeting and
  snapshot runs apply to the spec rules; a generic improvement made in devkit benefits devkit-spec at once.
- **Negative / Risks**: devkit is pinned to a minor range (`devkit>=0.1,<0.2`) and devkit-spec moves with it; devkit's
  `workflow next` and `worktree finish` cannot call devkit-spec, so the skills run the scope commands
  (`ADR-scope-maintenance-through-skills`); some earlier features were dropped (derived-data cache, web viewer,
  per-kind listing filters).
- **Follow-ups**: a generic capability devkit-spec needs is added to devkit first.

