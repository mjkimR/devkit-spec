# RULE-document-summary

`summary` is one or two English sentences in a document's frontmatter saying what the document defines. It is the main
signal of `devkit spec search`: the embedding model reads a document's ID and summary, while the title and the body,
in any language, are ranked lexically only. A short English summary lets English queries find documents written in
another language.

```yaml
---
id: CAP-CORE-search
title: 문서 검색            # any language
summary: Ranks documents for a query by meaning, pinning exact IDs and narrowing by kind and namespace.
status: active
---
```

## Violations

- A capability, story, decision, architecture document, `proposal.md` or `spec.md` without `summary`. A file still
  carrying the skeleton marker `<!-- devkit:skeleton -->` (a spec just created) is exempt until it is written.
- A `summary` that is not a non-empty string.
- A letter outside the Latin script in any `summary` (Hangul, kana, Cyrillic, ...): write it in English. Digits,
  punctuation and symbols are fine.
- A `summary` longer than `max_length` characters (default 300): a summary is not a description section.

Materials are free-form and exempt; files of completed spec bundles are checked only when named as explicit targets.
Not fixable: write the summary by hand.

## Adoption

In a repository whose documents have no summaries yet, run the rule in the hygiene phase while they are written:

```toml
[rules.phase_overrides]
RULE-document-summary = "hygiene"   # remove once `devkit rules check --phase hygiene` reports none
```

```toml
[rules.settings.RULE-document-summary]
max_length = 300
```
