---
id: PROP-terminology-authoring-guidance
title: Terminology authoring guidance and a glossary that agents read
summary: "Adds domain-neutral terminology authoring guidance to the spec bundle, reshapes the seeded glossary table around owners, exclusions, avoided synonyms and code identifiers, and makes spec-sync update the glossary, so docs/glossary.md is read while writing instead of only seeded."
status: draft                         # draft | reviewing | accepted | rejected
created_at: 2026-10-14
target_area: capabilities/harness/
priority: high                        # critical | high | medium | low
size: M                               # S | M | L | XL
boundaries:
  owns:
    - capabilities/harness/
    - src/devkit_spec/bundle/instructions/
    - src/devkit_spec/bundle/seed/docs/glossary.md
    - src/devkit_spec/bundle/skills/spec-sync/
    - docs/glossary.md
  excludes:
    - docs/decisions/
    - src/devkit_spec/bundle/rules/
# handoff_workflow: bugfix            # workflow after handoff (default: direct-delivery)
workflow: incubated-delivery
workflow_hash: sha256:c6cf386f9eb37b061d626d4bc701dd4e01f43674666d160179f69da5c391463e
---

# [PROP-terminology-authoring-guidance] Terminology authoring guidance and a glossary that agents read

## 1. Background & Hypothesis

### 1.1 Problem

The starting point is a draft of terminology rules used in another project (origin: user), first incubated earlier
and carried over here because its findings hold for the `spec` bundle. The current state of the bundle:

- **Nothing reads the glossary while writing.** The only bundle mention of the glossary in an authoring path is the
  `## Glossary` section of the `living-spec-writing` instruction, which says where terms are defined and nothing about
  when to check or update them. No `spec*` skill mentions it, so `spec-sync` never asks whether a change introduced or
  renamed a domain term. The seeded `docs/glossary.md` is written once and then not consulted.
- **The seeded guideline reads as permission to rename code.** The second authoring guideline of
  `src/devkit_spec/bundle/seed/docs/glossary.md` is "Code symbols (classes, DB tables, API fields) should adhere to the
  canonical terminology defined in this glossary." Tidying document terms can be read as a mandate to rename API fields
  and tables; what is actually needed, a way to map terms to existing identifiers, is missing.
- **The table has no place for the rules.** The seeded columns are `Term | English / Abbr | Definition & Description |
  Relevant Area | Remarks`: no owner, no adjacent concepts to keep apart, no rejected synonyms, no code identifiers.
- devkit-spec's own `docs/glossary.md` already moved part of the way: its tables are `Term | Definition | Defined in`,
  where "Defined in" names the owning document ID, and it settles that `docs/` as a whole is the Living Spec (the
  scope conflict earlier glossaries had).

### 1.2 Hypothesis

Ship domain-neutral terminology guidance as bundle instruction text, reshape the seeded glossary table around the
fields that guidance uses, and add one impact question to `spec-sync`. Every session then sees the guidance header
through `devkit get-context spec` and reads the body before writing documents, and the glossary becomes a document that
is checked while writing and updated at reconciliation instead of a seeded file nobody opens.

- No new human gate or question point. The guidance informs the agent's naming decisions and asks for no approval.
- No command change: instructions are bundle assets (`CAP-HARN-agent-guidance`), and the skeleton stays opt-in
  (`ADR-docs-skeleton-is-opt-in`). Projects without a `docs/glossary.md` still receive the guidance; registration
  steps apply only where a glossary exists.

## 2. Technical Spike Questions

- **Q1. Separate instruction or a section of `living-spec-writing`.** A new `terminology` instruction gets its own
  header and description, the trigger the proposal relies on. Folding the text into the existing `## Glossary`
  section of `living-spec-writing` keeps the instruction count at two and costs no extra header in every
  `get-context` result; that instruction is already read before any `docs/` or `specs/` edit. Draft: fold it into
  `living-spec-writing` and widen that instruction's description to mention naming and the glossary.
- **Q2. Where the generic-noun list lives.** Rule 1 below lists bare generic nouns. Keep a short default in the
  instruction and put project additions and exceptions in a section of `docs/glossary.md`, or only one of the two.
  Draft: both; short examples in the instruction, project-specific lists in the glossary.
- **Q3. Column set.** The six-column table of section 3.3 or devkit-spec's own three columns (`Term | Definition |
  Defined in`) plus `Avoid` and `Code identifiers`. `Distinct from / Excludes` may fit inside the definition. Draft:
  `Term | Definition | Owner | Avoid | Code identifiers`, with exclusions written in the definition; the original-
  language rendering goes in the `Term` cell (`기능 원장 (Living Spec)`) instead of an `English / Abbr` column.
- **Q4. `Avoid` and `glossary.yaml` synonyms.** A rejected synonym should still find the registered term in `devkit spec
  search` (`CAP-DOCS-document-search` expands glossary synonyms). Decide whether one line of guidance ("an Avoid entry
  is also added as a synonym in `docs/glossary.yaml`") is enough. Generating one file from the other stays out of
  scope.
- **Q5. Existing glossaries.** A seeded glossary is project-owned, so projects keep the old columns. Decide whether the
  guidance carries a one-line fallback ("without the column, record owner and exclusions in the remarks"). Draft: yes.
- **Q6. Context budget.** The text is read before most documentation work. Decide whether a length bound (for example
  40 lines added) is an acceptance criterion.

## 3. Proposed Design & Impact

### 3.1 Placement

| Location | Content |
| --- | --- |
| `src/devkit_spec/bundle/instructions/` (`living-spec-writing.md` or a new `terminology.md`, Q1) | The guidance of 3.2 |
| `src/devkit_spec/bundle/seed/docs/glossary.md` | The table of 3.3, a project section for avoided generic nouns and exceptions, a one-line pointer to the guidance; the two existing authoring guidelines removed |
| `src/devkit_spec/bundle/skills/spec-sync/SKILL.md`, Step 1 | One impact question: did the change introduce or rename a domain term? Then update `docs/glossary.md` |
| `docs/glossary.md` (dogfood) | Migrated to the chosen columns |

The constitution (`src/devkit_spec/bundle/AGENTS.md`) gains nothing: it already tells every session to read the
relevant instruction bodies, and repeating the guidance there costs context in every session.

### 3.2 Guidance Draft

The normative level follows the `contract-authoring` instruction: no check enforces these rules, so the text uses
boundary statements ("does not authorize") and SHOULD rather than MUST.

```markdown
1. Do not name a new domain concept with a bare generic noun (target, resource, scope,
   context, state, status, revision, data, item). Add a qualifier that shows what it applies
   to, who owns it, or where it ends. Padding (`target data`) is not a qualifier.
2. Use the full registered term in titles, headings, table cells and sentences meant to
   stand alone. A short form is fine inside a paragraph whose subject is already clear.
3. One concept, one term. Record rejected synonyms in the Avoid column and do not alternate.
4. Same spelling, different owner or meaning: register each separately with its owner
   (approval request version vs. deployment revision). Never bulk-replace a word across contexts.
5. Use established terms and proper nouns (User Story, idempotency, product names) with their
   standard meaning; describe only the project's scope of use.
6. Keep document terms and code identifiers distinct. Quote existing API fields, types, paths
   and JSON exactly and map them ("approval subject (`target` field)"). This guidance does not
   authorize renaming code, APIs or schemas; a rename is its own spec. New identifiers SHOULD
   follow the registered term.
7. Before registering a term, check overlap with existing rows and record its owner and what it
   excludes. In Living Spec documents, rename in place without "formerly X" notes.
8. ADRs, docs/materials/, completed specs, quotations and generated output keep their original
   wording and are not reused as the current contract.
```

Relative to the original draft: rule 3 (one concept, one term) is new, covering the direction the draft missed; the
draft's last item is split into 7 (when to check, tied to in-place rewriting) and 8 (records keep their wording,
mapped to ADRs, materials and completed specs); domain-specific examples are replaced with generic ones.

### 3.3 Glossary Table

```markdown
| Term | Definition | Owner | Distinct from / Excludes | Avoid | Code identifiers |
```

- **Owner**: the document ID that defines the term (`CAP-...`, `ADR-...`) or the owning component; rules 4 and 7.
- **Distinct from / Excludes**: adjacent terms that are easily confused and what the term does not cover.
- **Avoid**: rejected synonyms; rule 3.
- **Code identifiers**: the matching API fields, types and paths; rule 6.
- Q3 may reduce this set.

### 3.4 Non-Goals

- No deterministic rule checks generic or avoided terms: the judgement is contextual and false positives are costly.
  A hygiene rule is a separate proposal once repeated violations are observed.
- No bulk renaming of code, API or database identifiers.
- No generation or synchronisation between `glossary.md` and `glossary.yaml`.
- No command change.

## 4. Lifecycle & Retirement Criteria

- Preliminary decisions: none expected; the instruction mechanism is devkit's resource taxonomy and the bundle's
  instruction assets (`CAP-HARN-agent-guidance`).
- Research: none needed.
- On acceptance: once Q1 to Q6 have a direction, set `status: accepted` and run `devkit spec proposal handoff
  terminology-authoring-guidance`.
- On rejection: record a rejection ADR in `docs/decisions/` and delete the proposal directory.
