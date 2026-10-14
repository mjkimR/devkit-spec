---
id: PROP-terminology-authoring-guidance-target
title: Target Living Spec Structure for PROP-terminology-authoring-guidance
status: draft
proposal: PROP-terminology-authoring-guidance
created_at: 2026-10-14
# The Living Spec files this proposal changes, one "- file: <workspace-relative path>" each;
# devkit spec scope compare reads them to find overlaps with other work.
targets:
  - file: docs/capabilities/harness/CAP-HARN-agent-guidance.md
  - file: docs/capabilities/delivery/CAP-DLV-delivery-workflows.md
  - file: docs/glossary.md
---

# [Blueprint] PROP-terminology-authoring-guidance: Target Living Spec Structure for Terminology authoring guidance and a glossary that agents read

This document defines the target blueprint of how the docs/ backbone (Living Spec) will evolve if proposal PROP-terminology-authoring-guidance is accepted. It represents a hypothesis plan subject to adjustment during implementation. Upon handoff, it is copied into specs/ to serve as a baseline for plan.md boundaries and reconcile.md targets.

---

## 1. System Capabilities Plan (docs/capabilities/)

- `CAP-HARN-agent-guidance`: section 4.3 describes the terminology guidance (a widened `living-spec-writing` or a new
  `terminology` instruction, proposal Q1); section 4.7 describes the revised seeded `glossary.md` columns and its
  project section for avoided generic nouns.
- `CAP-DLV-delivery-workflows`: the reconciliation scope includes glossary updates when a change introduces or
  renames a domain term (`spec-sync` Step 1).

---

## 2. User Stories Plan (docs/stories/)

None expected. `US-keep-the-living-spec-consistent` already covers keeping documents current; review it during
reconciliation in case its acceptance criteria name the glossary.

---

## 3. Architecture & Decision Impact (docs/architecture/ & docs/decisions/)

None expected. Instructions are existing bundle assets, and the skeleton stays opt-in (`ADR-docs-skeleton-is-opt-in`).

---

## 4. Development Conventions & Governance (docs/development/ & .devkit/)

- `src/devkit_spec/bundle/instructions/`: the guidance text.
- `src/devkit_spec/bundle/skills/spec-sync/SKILL.md` Step 1: one impact question for domain terms.
- `src/devkit_spec/bundle/seed/docs/glossary.md`: new columns, a project section for avoided generic nouns and
  exceptions, a pointer to the guidance; the two existing authoring guidelines removed.
- `docs/glossary.md`: migrated to the chosen columns.
- No rule, workflow or command change.

---

## 5. System Before & After Comparison (Before & After)

| Aspect | Before | After |
| --- | --- | --- |
| Authoring rules | Two lines in the seeded `glossary.md`, never read by a skill | Instruction text read before writing documents |
| Code identifiers | Seeded guideline reads as permission to rename code to the glossary | Identifiers are quoted and mapped; a rename is its own spec |
| Seeded table | Term, English / Abbr, Definition, Area, Remarks | Term, Definition, Owner, (Distinct from / Excludes), Avoid, Code identifiers (proposal Q3) |
| Registration timing | Not defined | Checked while writing; updated in `spec-sync` Step 1 |
| Existing glossaries | Unchanged | Unchanged (project-owned); the guidance's fallback applies to old columns |
