# [RULE-document-summary] English Document Summary

## 1. Overview

`summary` is one or two English sentences in a document's frontmatter saying what the document defines. It is the
main signal of `devkit spec search`: the embedding model reads a document's ID and summary, while the title and the
body, in any language, are ranked lexically only. A short English summary lets English queries find documents written
in another language.

- **Phase and severity**: `linter`, `error`. Shipped by the `spec` bundle (preset `core`).
- **What is checked**: the targeted documents, Markdown files under `docs/` and `specs/` whose frontmatter `id` (or
  `reconcile_id`) is a well-formed document ID. A summary is required on capabilities (`CAP-`), stories (`US-`),
  decisions (`ADR-`), architecture documents (`ARCH-`), `proposal.md` and `spec.md`; any other document that has one
  is checked for its form.
- **What is not**: materials (`docs/materials/`, any `/materials/` directory), which are free-form; `README.md`,
  templates (`*-template.md`, `*_template.md`) and symbolic links, which are not documents. A file still carrying the
  skeleton marker `<!-- devkit:skeleton -->` (a spec just created) needs no summary until it is written.
- **Completed specs**: files of a spec bundle whose `spec.md` is `completed` are work history and are checked only
  when named as explicit targets.

## 2. Cause of Violation

Reported at the `summary` line, or line 1 when the key is missing:

- A required summary is missing: `<ID> has no summary`.
- The value is not a non-empty string: `summary must be a non-empty string`.
- It contains a letter outside the Latin script (Hangul, kana, Cyrillic, ...): `summary must be English; it contains
  <letters>` (the first five such letters). Digits, punctuation and symbols are fine.
- It is longer than `max_length` characters, surrounding whitespace not counted: `summary has <n> characters; keep it
  to one or two sentences (<max> at most)`. A summary is not a description section.

## 3. Remediation

Not fixable: a summary is written, never generated. Write `summary:` in the frontmatter, one or two English sentences
saying what the document defines; the title and body may stay in any language.

Read the `spec:living-spec-writing` instruction (Summaries) before writing or rewriting one: it says what a summary
states and how to quote it in YAML; `devkit rules explain` prints its path as a `[RELATED: ...]` line.

## 4. Configuration

| Setting | Type | Default | Meaning |
| --- | --- | --- | --- |
| `max_length` | positive integer | `300` | Characters allowed in a summary. |

```toml
[rules.settings.RULE-document-summary]
max_length = 300
```

## 5. Exceptions

There is no inline suppression. In a repository whose documents have no summaries yet, run the rule in the hygiene
phase while they are written, then remove the override:

```toml
[rules.phase_overrides]
RULE-document-summary = "hygiene"   # remove once `devkit rules check --phase hygiene` reports none
```

## 6. Example

```yaml
---
id: CAP-CORE-search
title: 문서 검색            # any language
summary: Ranks documents for a query by meaning, pinning exact IDs and narrowing by kind and namespace.
status: active
---
```
