# Document Search

`devkit spec search` finds documents by meaning when the exact ID is not known. The ranking is devkit's
([devkit.search](https://github.com/mjkimR/devkit/blob/main/docs/search/overview.md)); devkit-spec adds the spec
search policy on top. `devkit spec resolve` stays the way to go from a known ID to its path.

```bash
uv run devkit spec search "link integrity between documents"
uv run devkit spec search CAP-CORE-search                 # an exact ID, path or file name is pinned first
uv run devkit spec search "cache policy" --kind decision --kind capability --history
```

```text
[SEARCH: query="cache policy" mode=hybrid count=2]
[HIT: ADR-cache score=0.0328 pinned=no kind=decision status=accepted path=docs/decisions/2026-10/20261001-cache.md title="Cache derived data"]
[HIT: CAP-CORE-search score=0.0161 pinned=no kind=capability status=active path=docs/capabilities/core/CAP-CORE-search.md title="Document search"]
```

## Policy

- **Candidates**: the indexed documents ([documents overview](documents/overview.md)), current ones unless
  `--history`, narrowed by `--kind` (repeatable).
- **Fields**: ID, title and area are the metadata, ranked lexically and densely; the body after the frontmatter is
  ranked lexically only. Keep frontmatter in English: documents written in another language are then still found by
  English queries.
- **Pinning**: a query equal to a document's ID, workspace-relative path or file name (case-insensitive) puts it first
  with `score=-`.
- **Glossary**: the optional, project-owned `docs/glossary.yaml` expands a query with whole synonym clusters (useful
  for terms in another language):

  ```yaml
  terms:
    - primary: reconciliation
      synonyms: [정합성, sync]
  ```

- **Modes**: `--mode auto` (default) is `hybrid` when devkit's search extra is installed
  (`uv add 'devkit-spec[search]'`, which adds `devkit[search]`), else `lexical`; `lexical`, `dense` and `hybrid` force
  one, and an explicit `dense` or `hybrid` without the extra fails with devkit's `SEARCH_EXTRA_MISSING`.
  `--min-similarity` (default `0.35`) drops the long tail of the dense ranking. `[SEARCH: ... mode=]` names the ranking
  that ran.

`--limit/-n` (default `10`, `0` for all). JSON: `query`, `expanded` (the query after glossary expansion), `mode`,
`hits` (`id`, `kind`, `path`, `status`, `title`, `area`, `score`, `pinned`), `notices`.

## Error Codes

| Code | Level | Class | Condition |
| --- | --- | --- | --- |
| `SPEC_GLOSSARY_INVALID` | `ERROR` (`INPUT_ERROR`) | `GlossaryInvalidError` | `docs/glossary.yaml` cannot be read or is not `terms: [{primary, synonyms}]`. |

devkit's `SEARCH_EXTRA_MISSING`, `SEARCH_MODEL_NOT_FOUND` and `SEARCH_MODEL_INVALID` pass through for explicit dense or
hybrid searches; `ARGUMENT_INVALID` for a negative `--limit`. Unreadable documents are `SPEC_DOCUMENT_INVALID`
warnings.
