---
id: ADR-docs-skeleton-is-opt-in
title: Make the docs skeleton an opt-in preset
summary: The seeded docs/ skeleton (Living Spec directories, arc42 chapters, glossary and search synonyms) ships in its own docs-skeleton preset that a project adds explicitly, so installing devkit-spec never writes files into an existing docs/ tree.
status: accepted
created_at: 2026-10-13
---

# [ADR-docs-skeleton-is-opt-in] Make the docs skeleton an opt-in preset

- **Status**: Accepted
- **Date**: 2026-10-13
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `CAP-HARN-agent-guidance`, `ARCH-05-1-containers`

---

## 1. Context & Problem Statement

specrig wrote a `docs/` skeleton (`template/docs`, plus `glossary.yaml`) when a project was initialized. In devkit, a
`kind = "document"` asset with `seeded = true` is written once where the target file is absent and is project-owned
afterwards. The `spec` bundle declares `auto_select`, so its default preset deploys on the next `devkit sync` after
installation. A skeleton in that preset would drop READMEs, arc42 chapter templates and a glossary into every project
that installs the package, including projects with an established `docs/` tree.

---

## 2. Decision Drivers

- Installing the package never writes documentation a project did not ask for.
- A new project can still start from the arc42 and Living Spec structure in one command.
- Seeded files belong to the project once written.

---

## 3. Considered Options

### Option 1: A separate `docs-skeleton` preset (Selected)
- **Overview**: `[presets.docs-skeleton] assets = ["docs-skeleton"]`, added with `devkit add spec:docs-skeleton`.
- **Pros**: no surprise files; one command for a new project.
- **Cons**: one more step for projects that want it.

### Option 2: The skeleton in the `core` preset
- **Overview**: seed it on every sync.
- **Pros**: zero steps.
- **Cons**: writes into existing `docs/` trees wherever a seeded file is absent.

### Option 3: No skeleton
- **Overview**: templates only.
- **Pros**: nothing seeded.
- **Cons**: new projects rebuild the directory structure, arc42 chapters and glossary by hand.

---

## 4. Decision Outcome

We decided to adopt **Option 1**.

**Rationale**: it keeps installation side-effect free for existing documentation and keeps the one-command start.

---

## 5. Consequences

- **Positive**: the skeleton is written once where absent and never updated by later syncs; `glossary.yaml` lives at
  `docs/glossary.yaml`, the synonym list of `devkit spec search`.
- **Negative / Risks**: improvements to the seed reach existing projects only when they copy them by hand.
- **Follow-ups**: this repository selects the preset (`spec = ["core", "docs-skeleton"]`) and has replaced the seeded
  content with its own Living Spec.
