---
id: CAP-DOCS-document-search
title: Document Search
summary: Defines devkit spec search, which ranks spec documents for a free-text query on top of devkit's lexical, dense and hybrid search, embedding only the ID and English summary, pinning exact IDs and paths, expanding glossary synonyms and narrowing by kind, history and namespace.
area: documents
status: active
stories:
  - US-find-the-right-documents
entrypoints:
  - src/devkit_spec/search.py
  - src/devkit_spec/cli/search.py
created_at: 2026-10-13
---

# [CAP-DOCS-document-search] Document Search

## 1. Summary

`devkit spec search` finds documents by meaning when the exact ID is not known. The ranking is devkit's
([devkit.search](https://github.com/mjkimR/devkit/blob/main/docs/search/overview.md)); devkit-spec adds the spec
search policy on top: which documents are candidates, which fields are embedded, exact-match pinning and glossary
expansion. Going from a known ID to its path stays `devkit spec resolve` (`CAP-DOCS-document-lookup`).

## 2. Scope & Boundary

- **In-Scope**: candidate selection, field policy, pinning, glossary expansion, mode selection, the command's
  options, text and JSON output, and error codes.
- **Out-of-Scope** (Non-Goals):
  - The ranking algorithms themselves (tokenizer, BM25, embedding model, fusion): devkit's `devkit.search`.
  - Embedding titles, areas or bodies. Scope Excluded: only the ID and the `summary` go to the dense ranking.
    Rationale: on specrig's documents (Korean titles and bodies, English paraphrase queries) hybrid MRR was 0.54 with
    ID, title and area embedded, 0.70 with the ID alone and 0.81 with ID and summary; embedding whole bodies ranked
    below the ID alone. When to Reconsider: a multilingual embedding model in devkit's search extra.
  - A persistent search index. Scope Excluded: candidates are read from the document index on every call.

## 3. Business Rules & Policies

1. **Candidates**: the indexed documents (`CAP-DOCS-document-model`), current ones unless `--history`, narrowed by
   `--kind` (repeatable) and by the namespace selection (`--namespace NAME`, `--all-namespaces`, default: the current
   directory's namespace plus the global documents; `CAP-DOCS-namespaces`).
2. **Fields**: a document's ID and its English `summary` are its metadata, ranked lexically and densely (the ID alone
   for a document without a summary). The title, the area and the body after the frontmatter are ranked lexically
   only, in any language. `RULE-document-summary` requires the summary on the documents agents search.
3. **Pinning**: a query equal to a document's ID, workspace-relative path or file name (compared case-insensitively
   after trimming) MUST put that document first, whatever the ranking, with `score=-` (`null` in JSON) and
   `pinned=yes`. A pinned document is not repeated among the ranked hits.
4. **Glossary expansion**: the optional, project-owned `docs/glossary.yaml` expands the query. When the query
   contains a word of a cluster (a token of the query, or a multi-word term contained in it, case-insensitively), the
   whole cluster (`primary` plus `synonyms`) is appended, minus terms the query already contains. Useful for terms in
   another language. Without the file there is no expansion.
5. **Modes**: `--mode auto` (default) is `hybrid` when devkit's search extra is installed
   (`uv add 'devkit-spec[search]'`, which adds `devkit[search]`), else `lexical`. `lexical`, `dense` and `hybrid`
   force one; an explicit `dense` or `hybrid` without the extra MUST fail with devkit's `SEARCH_EXTRA_MISSING`.
   `[SEARCH: ... mode=]` names the ranking that ran, never `auto`.
6. **Similarity floor**: `--min-similarity` (default `0.35`, the floor of devkit's playbook search) drops the long
   tail of the dense ranking in `dense` and `hybrid` modes.
7. **Limit**: `--limit/-n` (default `10`, `0` for all) caps the hits, pinned ones included. A negative limit MUST fail
   with `ARGUMENT_INVALID`.
8. **Query language**: English queries work best, since the summary is the main dense signal.

## 4. Interfaces & Data Contracts

### 4.1 Command

```text
devkit spec search QUERY... [--kind KIND]... [--history] [--namespace NAME | --all-namespaces]
    [--mode auto|lexical|dense|hybrid] [--limit/-n N] [--min-similarity F] [-w ROOT] [--format text|json]
```

The words of `QUERY...` are joined with single spaces. `KIND` is one of the document kinds of
`CAP-DOCS-document-model`.

```bash
devkit spec search "link integrity between documents"
devkit spec search CAP-CORE-search                  # an exact ID, path or file name is pinned first
devkit spec search "cache policy" --kind decision --kind capability --history
```

### 4.2 Text Output

```text
[SEARCH: query="cache policy" mode=hybrid count=2]
[HIT: ADR-cache score=0.0328 pinned=no kind=decision status=accepted path=docs/decisions/2026-10/20261001-cache.md title="Cache derived data"]
[HIT: CAP-CORE-search score=0.0161 pinned=no kind=capability status=active path=docs/capabilities/core/CAP-CORE-search.md title="Document search"]
```

`[SEARCH: query= mode= count=]` comes first, then one `[HIT: <id> score= pinned= kind= status= path= title=]` per
document, best first. `score` has four decimals; a hit also carries `namespace=` (before `title`) in a workspace that
registers namespaces.

### 4.3 JSON Keys

`query`, `expanded` (the query after glossary expansion), `mode` (the ranking that ran), `namespace` (the selection,
`null` for every namespace), `hits` (document records `id`, `kind`, `path`, `status`, `title`, `area`, `summary`, `namespace`,
plus `score` and `pinned`), `notices`.

### 4.4 Glossary File

```yaml
# docs/glossary.yaml (optional, project-owned)
terms:
  - primary: reconciliation
    synonyms: [정합성, sync]
```

`terms` is a list of mappings, each with a string `primary` and an optional list of string `synonyms`.

### 4.5 Error Codes

| Code | Level | Class | Condition |
| --- | --- | --- | --- |
| `SPEC_GLOSSARY_INVALID` | `ERROR` (`INPUT_ERROR`) | `GlossaryInvalidError` | `docs/glossary.yaml` cannot be read or is not `terms: [{primary, synonyms}]`. |

devkit's `SEARCH_EXTRA_MISSING`, `SEARCH_MODEL_NOT_FOUND` and `SEARCH_MODEL_INVALID` pass through for explicit dense
or hybrid searches; `ARGUMENT_INVALID` for a negative `--limit` or an invalid namespace selection;
`SPEC_CONFIG_INVALID` for a malformed `[tool.spec]` table. Unreadable documents are `SPEC_DOCUMENT_INVALID`
warnings. Exit codes: `0` success (also with no hit), `2` an error, warnings `1` only under `--strict`.

### 4.6 Library

`devkit_spec.search.search_documents(index, query, kinds=..., history=..., mode=..., limit=..., min_similarity=...,
accept=...)` returns `SpecSearchResult` (`query`, `expanded`, `mode`, `hits` of `SpecHit`: `document`, `score`,
`pinned`); `accept` narrows candidates further (a namespace selection). `load_glossary`, `expand_query` and
`metadata` (the embedded text) expose the policy steps.
