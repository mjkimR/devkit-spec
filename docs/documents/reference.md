# Documents Reference

Commands over the document model ([overview](overview.md)). Every command takes `-w/--workspace-root` (default: the devkit project containing the current directory), `--format text|json` and devkit's output options (`-q`, `-v`, `--strict`). Paths are relative to the workspace root.

## Usage

```bash
uv run devkit spec resolve CAP-CORE-search US-find-docs     # the path of each ID
uv run devkit spec refs CAP-CORE-search                      # what it references
uv run devkit spec refs CAP-CORE-search --direction in       # what references it
uv run devkit spec list story --status active --area core    # browse; --history adds completed spec bundles
```

`refs` and `list` page their output: `--limit/-n` (default `20`, `0` for all) and `--offset` (default `0`).

## Output

```text
[DOCUMENT: US-find-docs kind=story status=active path=docs/stories/core/US-find-docs.md]
[REF: US-find-docs path=docs/stories/core/US-find-docs.md status=active fields=body,stories count=2]
[REF: US-removed path=- status=- fields=body count=1]
[DOCUMENT: SPEC-search kind=spec status=draft path=specs/2026-10/20261002-search/spec.md tasks=1/2 title="Search"]
[PAGE: total=42 offset=0 limit=20 count=20 next=20]
[NEXT_CMD: devkit spec list spec --limit 20 --offset 20]
```

- `resolve` prints one `[DOCUMENT: ...]` line per resolved ID, in argument order; each unresolved or duplicated ID is an error after them.
- `refs` prints one `[REF: <id> ...]` line per document on the other side, in ID order. `fields` lists where the references are (`body` or frontmatter fields), `count` how many there are. `path=-` is an ID no single document declares: a dangling reference, or a duplicated ID.
- `list` prints one `[DOCUMENT: ...]` line per document, ordered by kind (the order of the table in the overview), then ID. `tasks` is `<checked>/<total>` of the `tasks.md` beside a spec, `-` otherwise. Filters: `KIND...` (default all), `--status a,b` (case-insensitive), `--area` and `--query` (substring of the area, or of the ID or title, case-insensitive), `--history`, `--file PATH` (capabilities and stories whose frontmatter `entrypoints` contain the path, sit under it, or are a directory containing it), and in a workspace with namespaces `--namespace NAME` / `--all-namespaces` (default: the namespace of the current directory plus the global documents; [overview, section 3](overview.md#3-namespaces)). With namespaces configured, each line also carries `namespace=`.
- `[PAGE: ...]` ends `refs` and `list`; `next` is the offset of the next page, `-` on the last one, and `[NEXT_CMD: ...]` repeats the command for it.

JSON keys: `resolve`: `documents`, `errors`, `notices`; `refs`: `id`, `direction`, `total`, `offset`, `limit`, `items` (`id`, `path`, `status`, `references`: `target`, `source`, `path`, `field`, `line`, `column`, `bracket`), `notices`; `list`: `total`, `offset`, `limit`, `namespace` (the selection, `null` for every namespace), `documents` (`id`, `kind`, `path`, `status`, `title`, `area`, `namespace`, `historical`, `tasks`), `notices`.

## Error Codes

`0` success; `2` an unresolved or duplicated ID, or an argument error. Warnings exit `0` (`1` under `--strict`).

| Code | Level | Class | Condition |
| --- | --- | --- | --- |
| `SPEC_ID_UNRESOLVED` | `ERROR` (`INPUT_ERROR`) | `UnresolvedIdError` | No document declares the ID. |
| `SPEC_ID_DUPLICATE` | `ERROR` (`MAINTENANCE`) | `DuplicateIdError` | More than one document declares the ID; `[TARGET]` lists them. |
| `SPEC_DOCUMENT_INVALID` | `WARNING` | `DocumentInvalidWarning` | A file under `docs/` or `specs/` cannot be read or has malformed frontmatter; it is left out. |
| `ARGUMENT_INVALID` | `ERROR` (`INPUT_ERROR`) | `devkit.core.ArgumentError` | A negative `--limit` or `--offset`; an unknown `--namespace`, or it combined with `--all-namespaces`. |
| `SPEC_CONFIG_INVALID` | `ERROR` (`INPUT_ERROR`) | `devkit_spec.errors.SpecConfigError` | A malformed `[tool.spec]` table, namespaces included ([policy](../policy.md)). |

## Library

```python
from devkit_spec.documents import DocumentIndex, Kind

index = DocumentIndex.load(root)  # documents, by_id, problems (SPEC_DOCUMENT_INVALID warnings)
document = index.resolve("CAP-CORE-search")  # UnresolvedIdError, DuplicateIdError
index.outgoing(document)  # {target ID: [Reference, ...]}
index.incoming(document.id)  # {source ID: [Reference, ...]}
```
