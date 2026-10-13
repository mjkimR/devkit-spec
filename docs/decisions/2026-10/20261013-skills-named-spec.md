---
id: ADR-skills-named-spec
title: Name the skills spec and spec-*
summary: The bundle's skills are named after the spec bundle and command group (spec, spec-next, spec-specify, ...) instead of specrig's sr and sr-* names, and the specify-stage skill is spec-specify rather than spec-spec.
status: accepted
created_at: 2026-10-13
---

# [ADR-skills-named-spec] Name the skills spec and spec-*

- **Status**: Accepted
- **Date**: 2026-10-13
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `CAP-HARN-agent-guidance`, `CAP-DLV-delivery-workflows`

---

## 1. Context & Problem Statement

specrig's skills were `sr` (the router) and `sr-*` (the specify-stage skill was `sr-spec`), named after the product.
devkit-spec ships them in the bundle `spec`, next to the command group `devkit spec` and the constitution returned by
`devkit get-context spec`. Users invoke skills by name (`/<skill> <intent>`), and workflow definitions list them per stage.

---

## 2. Decision Drivers

- One name for the bundle, the commands and the skills.
- Skill names say what the skill does.
- No skill name that reads as a stutter or is confused with the router.

---

## 3. Considered Options

### Option 1: `spec`, `spec-*`, with `sr-spec` renamed `spec-specify` (Selected)
- **Overview**: `sr` becomes `spec`, each `sr-<x>` becomes `spec-<x>`, and the specify-stage skill is named after its
  stage, `spec-specify`.
- **Pros**: `/spec <intent>` and `/spec-next` match the bundle and commands; stage skills match stage ids.
- **Cons**: users of specrig relearn the names.

### Option 2: Keep `sr`, `sr-*`
- **Overview**: no rename.
- **Pros**: familiar to specrig users.
- **Cons**: a prefix of the retired product's name, unrelated to the bundle and the commands.

### Option 3: Mechanical rename including `spec-spec`
- **Overview**: `sr-spec` becomes `spec-spec`.
- **Pros**: a uniform rule.
- **Cons**: a stutter, easy to confuse with the `spec` router.

---

## 4. Decision Outcome

We decided to adopt **Option 1**.

**Rationale**: it aligns every user-facing name with the bundle and makes the stage skill's name its stage.

---

## 5. Consequences

- **Positive**: the 14 skills are `spec`, `spec-next`, `spec-specify`, `spec-plan`, `spec-tasks`, `spec-review`,
  `spec-sync`, `spec-integrate`, `spec-delegate`, `spec-challenge`, `spec-scout`, `spec-rule`, `spec-feedback` and
  `spec-entrypoints`; the workflow `skills:` lists and the role contracts' `skill` fields use these names.
- **Negative / Risks**: none beyond the rename.
- **Follow-ups**: none.
