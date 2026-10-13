---
id: CAP-DOCS-document-lookup
title: Document Lookup
summary: Defines the devkit spec resolve, refs and list commands that map IDs to paths, follow incoming and outgoing references, and browse documents by kind, status, area, text, history, namespace or owned code path, with paging and JSON output.
area: documents
status: active
stories:
  - US-find-the-right-documents
entrypoints:
  - src/devkit_spec/cli/documents.py
created_at: 2026-10-13
---

# [CAP-DOCS-document-lookup] Document Lookup

## 1. Summary

Three commands give an agent deterministic access to the document index (`CAP-DOCS-document-model`): `devkit spec
resolve` maps IDs to paths, `devkit spec refs` follows the references of one document in either direction, and
`devkit spec list` browses documents with filters. They are the exact-match counterpart of `devkit spec search`
(`CAP-DOCS-document-search`), which ranks by meaning when the ID is not known.

## 2. Scope & Boundary

- **In-Scope**: `resolve`, `refs` and `list`: arguments, options, filters, ordering, paging, text sentinels, JSON
  keys, exit codes and error codes.
- **Out-of-Scope** (Non-Goals):
  - Ranking by meaning: `CAP-DOCS-document-search`.
  - Namespace semantics (membership, default selection): `CAP-DOCS-namespaces`; this capability only applies them.
  - Per-kind listing extras: filters by linked story or capability (`--with-story`, `--with-cap`), proposal priority
    and size, and feedback filters. Scope Excluded: `list` filters only by the generic fields below. When to
    Reconsider: when agents repeatedly combine `refs` and `list` by hand for one of these questions.
  - Validating references: `RULE-document-reference` (`CAP-GOV-spec-rules`).

## 3. Business Rules & Policies

### 3.1 Common

1. **Workspace**: every command takes `-w/--workspace-root` (default: the devkit project containing the current
   directory), `--format text|json` and devkit's output options (`-q`, `-v`, `--strict`), as every `devkit spec`
   command does (`CAP-HARN-command-mount`). Paths in the output MUST be workspace-relative.
2. **Invalid files**: files the index left out are `SPEC_DOCUMENT_INVALID` warnings on stderr (under `notices` in
   JSON); they MUST NOT change the exit code except under `--strict`.
3. **Namespaces ignored for identity**: `resolve` and `refs` MUST resolve IDs repository-wide whatever namespace is
   selected; only `list` (and `search`) narrows by namespace.

### 3.2 `devkit spec resolve ID...`

1. Prints one `[DOCUMENT: ...]` line per resolved ID, in argument order.
2. Each unresolved or duplicated ID MUST be reported as an error after the lines that did resolve
   (`SPEC_ID_UNRESOLVED`, `SPEC_ID_DUPLICATE`); the command then exits `2`.

### 3.3 `devkit spec refs ID`

1. `--direction out` (default) lists the documents ID references; `--direction in` the documents that reference ID.
2. One `[REF: <id> ...]` line per document on the other side, in ID order. `fields` lists where the references are
   (`body` or frontmatter field names, sorted, comma-separated), `count` how many references there are.
3. `path=-` and `status=-` mark an ID that no single document declares: a dangling reference, or a duplicated ID.
4. The `proposal` provenance field is not a reference and MUST NOT appear.
5. An unresolvable ID argument fails with `SPEC_ID_UNRESOLVED` or `SPEC_ID_DUPLICATE` (exit `2`).

### 3.4 `devkit spec list [KIND]...`

1. **Kinds**: `KIND...` restricts to `capability`, `story`, `architecture`, `decision`, `proposal`,
   `proposal-decision`, `spec`, `plan`, `tasks`, `reconcile`, `feedback`, `material` (default: all).
2. **Filters** (all combine with AND):
   - `--status/-s a,b`: comma-separated statuses, compared case-insensitively.
   - `--area/-a TEXT`: case-insensitive substring of the frontmatter `area`.
   - `--query TEXT`: case-insensitive substring of the ID or the title.
   - `--history`: include historical documents (files of completed spec bundles); hidden by default.
   - `--file PATH`: documents whose frontmatter `entrypoints` overlap the workspace-relative path: an entry equal to
     it, under it, or a directory containing it (whole path segments, case-sensitive; `CAP-TRACE-code-entrypoints`).
     The path need not exist, so a deleted file still finds its documents; an invalid path matches nothing. Only
     capabilities and stories declare `entrypoints`.
   - `--namespace NAME` / `--all-namespaces`: the namespace selection (`CAP-DOCS-namespaces`). Default: the namespace
     of the current directory plus the global documents.
3. **Order**: kind order (the table of `CAP-DOCS-document-model`), then ID, then path.
4. **Line fields**: `kind`, `status`, `path`, `tasks` (`<checked>/<total>` of the `tasks.md` beside a spec, counted
   as devkit counts checklist items; `-` for other kinds or without `tasks.md`), `namespace` (only in a workspace that
   registers namespaces), `title`.

### 3.5 Paging (`refs`, `list`)

1. `--limit/-n` (default `20`, `0` for all) and `--offset` (default `0`). A negative value MUST fail with devkit's
   `ARGUMENT_INVALID`.
2. The output ends with `[PAGE: total= offset= limit= count= next=]`; `next` is the offset of the next page, `-` on
   the last one.
3. When more items follow, `[NEXT_CMD: devkit spec ...]` repeats the command with every given filter, `-w` when it
   was given, `--limit` and the next `--offset`.

## 4. Interfaces & Data Contracts

### 4.1 Usage

```bash
devkit spec resolve CAP-CORE-search US-find-docs     # the path of each ID
devkit spec refs CAP-CORE-search                      # what it references
devkit spec refs CAP-CORE-search --direction in       # what references it
devkit spec list story --status active --area core    # browse
devkit spec list capability --file src/engine/        # documents owning a code path
devkit spec list spec --history --all-namespaces      # completed bundles too, every package
```

### 4.2 Text Output

```text
[DOCUMENT: US-find-docs kind=story status=active path=docs/stories/core/US-find-docs.md]
[REF: US-find-docs path=docs/stories/core/US-find-docs.md status=active fields=body,stories count=2]
[REF: US-removed path=- status=- fields=body count=1]
[DOCUMENT: SPEC-search kind=spec status=draft path=specs/2026-10/20261002-search/spec.md tasks=1/2 title="Search"]
[PAGE: total=42 offset=0 limit=20 count=20 next=20]
[NEXT_CMD: devkit spec list spec --limit 20 --offset 20]
```

`resolve` prints `[DOCUMENT: <id> kind= status= path=]`; `list` prints
`[DOCUMENT: <id> kind= status= path= tasks= namespace= title=]`, `namespace=` only with registered namespaces. Values follow devkit's sentinel conventions: `-` for empty, `yes`/`no` for booleans, a JSON
string when the value holds spaces, quotes or brackets.

### 4.3 JSON Keys (`--format json`)

| Command | Keys |
| --- | --- |
| `resolve` | `documents` (document records: `id`, `kind`, `path`, `status`, `title`, `area`, `summary`), `errors` (advisory objects), `notices` |
| `refs` | `id`, `direction`, `total`, `offset`, `limit`, `items` (`id`, `path`, `status`, `references`: `target`, `source`, `path`, `field`, `line`, `column`, `bracket`), `notices`; `path` and `status` are `null` for an ID no single document declares |
| `list` | `total`, `offset`, `limit`, `namespace` (the selection, `null` for every namespace), `documents` (document records plus `namespace`, `historical`, `tasks`), `notices` |

### 4.4 Exit Codes

`0` success; `2` an unresolved or duplicated ID, or an argument error. Warnings exit `0` (`1` under `--strict`).

### 4.5 Error Codes

| Code | Level | Class | Condition |
| --- | --- | --- | --- |
| `SPEC_ID_UNRESOLVED` | `ERROR` (`INPUT_ERROR`) | `UnresolvedIdError` | No document declares the ID. |
| `SPEC_ID_DUPLICATE` | `ERROR` (`MAINTENANCE`) | `DuplicateIdError` | More than one document declares the ID; `[TARGET]` lists them. |
| `SPEC_DOCUMENT_INVALID` | `WARNING` | `DocumentInvalidWarning` | A file under `docs/` or `specs/` cannot be read or has malformed frontmatter; it is left out. |
| `ARGUMENT_INVALID` | `ERROR` (`INPUT_ERROR`) | `devkit.core.ArgumentError` | A negative `--limit` or `--offset`; an unknown `--namespace`, or `--namespace` combined with `--all-namespaces`. |
| `SPEC_CONFIG_INVALID` | `ERROR` (`INPUT_ERROR`) | `devkit_spec.errors.SpecConfigError` | `list`: a malformed `[tool.spec]` table, namespaces included (`CAP-DLV-project-policy`). |
