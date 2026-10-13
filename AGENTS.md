# devkit-spec: Agent Guide

Spec-driven development on devkit: the `spec` bundle and the `devkit spec` command group, in one Python package.

## Architecture and Boundaries

- One package (`src/devkit_spec/`) managed with `uv` and `just`; tests live in `tests/`, never under `src/`. Keep `justfile` recipes thin; shared shell logic belongs in `scripts/`.
- devkit is the SDD-agnostic foundation; this package owns everything spec-driven: the document model (Living Spec, feature specs, IDs, references), its rules, workflows, skills and commands. A capability that is not specific to spec-driven development belongs in devkit (`../devkit`), not here.
- Use devkit only through its public surface: each module's `__init__` exports and `devkit.core.cli`. Never import devkit's private helpers or copy them.
- Commands are mounted under `devkit` through the `devkit.commands` entry point ([Command Plugins](https://github.com/mjkimR/devkit/blob/main/docs/architecture/command-plugins.md)); bundle assets are declared in `src/devkit_spec/bundle/bundle.toml`.
- specrig (the Go predecessor, private repository `mjkimR/specrig`) is the reference for behavior being ported; [`MAT-specrig-port-map`](docs/materials/2026-10/20261013-specrig-port-map.md) records where each of its components went. Port semantics, not code structure, and drop what devkit already covers.
- Write all documentation, guide material and bundle assets in English.
- Do not commit `.env`, log secrets/PII, or commit/push without explicit instructions.

## Agent-First Design

Every command follows devkit's output contract, because an AI coding agent is its primary consumer: one-line `[KIND: ...]` sentinels or one JSON object on stdout, Agent Advisory Protocol blocks on stderr, stable `SPEC_`-prefixed codes with deterministic `[ACTION]` directives, exit codes `0`/`1`/`2`, warnings and notices returned under `notices`. Specifications: [Agent-First Output](https://github.com/mjkimR/devkit/blob/main/docs/architecture/agent-output.md) and [Agent Advisory Protocol](https://github.com/mjkimR/devkit/blob/main/docs/advisory/protocol.md).

## Compatibility

No external consumers exist yet. Breaking changes to the bundle, the commands and the APIs may be made in place, without migrations or deprecation shims. devkit is pinned to a minor range (`devkit>=0.1,<0.2`) and moves with it.

## Verification

Run lint, type checks and relevant tests before completing code changes:

| Target | Command |
| --- | --- |
| Lint & format | `just lint` |
| Lint & format check (CI) | `just lint-check` |
| Type check (Pyright) | `just check` |
| Tests | `just test` |
| Test Coverage | `just test-cov` |
| Governance Rules | `just rules-check` |
| Everything CI runs | `just ci` |

<!-- DEVKIT:START -->
## devkit

This repository installs agent assets with `devkit`. `.devkit/config.toml` selects
bundles; `.devkit/installation.json` records what is deployed.

- Before work that touches a bundle's assets, run `uv run devkit get-context <bundle>` once per bundle in the current agent context. Installed bundles: `advisory`, `devkit`, `spec`.
- Entry skill `devkit-playbook`: find and run an operational playbook (explicit user invocation only).
- Entry skill `devkit-workflow`: diagnose and follow the delivery workflow stage of a work unit.
- Never edit `.devkit/managed/` or projected agent files; change the source bundle or use `devkit override`.
- Before any development work, run `uv run devkit get-context spec` once per agent context and follow it. Start work with `/spec <intent>`; `/spec-next` orients. `docs/` is the current-state Living Spec, `specs/` holds feature specs.

This block is managed by `devkit sync`; edit outside the markers only.
<!-- DEVKIT:END -->
