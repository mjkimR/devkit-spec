---
id: US-adopt-in-an-existing-repository
title: Adopt Spec-Driven Delivery in an Existing Repository
summary: A developer installs devkit-spec into a repository that already has code and documentation, gets the spec bundle and the devkit spec commands through devkit sync, and brings the spec rules to a passing baseline without rewriting legacy documents first.
area: harness
actor: Developer (maintainer of a consumer project)
status: active
created_at: 2026-10-13
capabilities:
  - CAP-HARN-agent-guidance
  - CAP-GOV-spec-rules
  - CAP-HARN-command-mount
---

# [US-adopt-in-an-existing-repository] Adopt Spec-Driven Delivery in an Existing Repository

## 1. User Story Narrative

- **As a**: developer maintaining a repository that already has code, docs and agent instructions
- **I want to**: install devkit-spec, have every agent session pick up spec-driven delivery, and get
  `devkit rules check` passing before migrating legacy content
- **So that**: new work follows the Living Spec immediately while legacy documents move over through normal work,
  not a big-bang rewrite

---

## 2. Background & Context

devkit-spec is one Python package: the `spec` bundle reaches the project through `devkit sync` (`devkit.bundles`,
`auto_select`) and the commands through devkit's own executable (`devkit.commands`). `devkit sync` writes nothing
under `docs/` or `specs/` unless the opt-in `docs-skeleton` preset is added; the spec rules nevertheless check the
Markdown already there. The `brownfield-adoption` playbook contains that debt and migrates it as work touches it.

---

## 3. Acceptance Criteria (Given / When / Then)

### Scenario 1: Installation exposes the bundle and the commands
- **Given**: a repository managed with `uv` and devkit
- **When**: the developer runs `uv add --dev devkit devkit-spec` and `uv run devkit sync`
- **Then**: `.devkit/managed/spec/` holds the `core` preset, the root `AGENTS.md` block gains the `spec-pointer`
  line, and `uv run devkit spec --version` prints `[VERSION: devkit-spec <version>]`

### Scenario 2: Existing docs are left alone by default
- **Given**: a repository with its own `docs/` tree
- **When**: `devkit sync` deploys the `spec` bundle without the `docs-skeleton` preset
- **Then**: no file under `docs/` is created or changed; `devkit add spec:docs-skeleton` seeds only the skeleton files
  that do not exist yet

### Scenario 3: Legacy documents are contained, not rewritten
- **Given**: the user asked for the `brownfield-adoption` playbook and `devkit rules check` reports violations in
  legacy Markdown under `docs/`
- **When**: the agent follows the playbook
- **Then**: the legacy files move under `docs/materials/_legacy/`, any remaining deferral is a commented
  `.devkit/config.toml` entry the user decided, no rule is edited, and `devkit rules check` passes

### Scenario 4: Opting out of the bundle
- **Given**: a project that wants the `devkit spec` commands but not the bundle
- **When**: it sets `[presets] spec = false` in `.devkit/config.toml` and runs `devkit sync`
- **Then**: the `spec` bundle's managed files and projections are not deployed
