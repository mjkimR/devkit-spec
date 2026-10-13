---
id: CAP-DOCS-document-model
title: Document Model
summary: Defines which Markdown files under docs/ and specs/ are documents, the ID grammar and kinds, the reference forms between documents (relation fields and ID code spans) and the workspace document index every spec command and rule reads.
area: documents
status: active
stories:
  - US-find-the-right-documents
  - US-keep-the-living-spec-consistent
entrypoints:
  - src/devkit_spec/documents/
created_at: 2026-10-13
---

# [CAP-DOCS-document-model] Document Model

## 1. Summary

The document model decides which files are spec documents, how each one is identified and how documents reference
each other. `devkit_spec.documents` implements it as a workspace index rebuilt from the files on every load. The
lookup commands (`CAP-DOCS-document-lookup`), document search (`CAP-DOCS-document-search`), namespaces
(`CAP-DOCS-namespaces`) and every spec rule (`CAP-GOV-spec-rules`) read documents only through this index.

## 2. Scope & Boundary

- **In-Scope**:
  - What a document is: location, frontmatter identity, exclusions.
  - The ID grammar and the kind each prefix names.
  - The reference forms (frontmatter relation fields, prose ID spans and brackets) and what prose excludes.
  - The `proposal` provenance field.
  - Historical documents (files of completed spec bundles, their feedback aside).
  - The `summary` field as data of the model.
  - The index: loading, invalid files, ID resolution, incoming and outgoing references, in-place rewriting.
- **Out-of-Scope** (Non-Goals):
  - Path and naming conventions per kind (dated partitions, `CAP-<AREA>-<slug>` stems, arc42 chapters). Scope
    Excluded: the index accepts any well-formed ID wherever it is declared. Rationale: conventions are checked and
    fixed by `RULE-id-convention` (`CAP-GOV-spec-rules`), which can report a misplaced file instead of hiding it.
  - Validity of references (unresolved, duplicated, wrong kind). Scope Excluded: the parser records references and
    skips malformed fields; `RULE-document-reference` reports them.
  - Namespace membership: `CAP-DOCS-namespaces`.
  - A persistent cache or database of documents. Scope Excluded: there is no second source of truth that can go stale.

## 3. Business Rules & Policies

### 3.1 Documents

1. **Location**: A document MUST be a Markdown file (`*.md`) under `docs/` or `specs/` of the workspace root.
2. **Exclusions**: `README.md`, templates (`*-template.md`, `*_template.md`), files under a directory whose name
   starts with `.`, and symbolic links (files or directories) MUST NOT be indexed.
3. **Identity**: A file is a document only when its frontmatter declares a well-formed ID (section 3.2) in `id`, or
   in `reconcile_id` for a reconcile record. A file without frontmatter, without an ID, or with an ID outside the
   grammar is not a document (a README, a glossary, a guide) and is silently left out.
4. **Frontmatter grammar**: The frontmatter MUST follow devkit's grammar (`devkit.core.frontmatter`); `id`,
   `reconcile_id` and `status`, when present, MUST be strings. A file that cannot be read as UTF-8, or whose
   frontmatter breaks either requirement, MUST be left out of the index and reported as a `SPEC_DOCUMENT_INVALID`
   warning; every other document MUST stay usable.
5. **Uniqueness**: IDs are repository-wide and MUST be unique across `docs/`, `specs/` and every namespace docs root.
   The index keeps every declaration of an ID, so a duplicate is detectable (`SPEC_ID_DUPLICATE`).
6. **Summary**: `summary` is one or two English sentences saying what the document defines. It is REQUIRED on
   capabilities, stories, decisions, architecture documents, `proposal.md` and `spec.md` (`RULE-document-summary`)
   and is the main signal of document search (`CAP-DOCS-document-search`). Titles and bodies MAY use any language.
7. **Historical documents**: The files of a spec bundle (`specs/<YYYY-MM>/<bundle>/...`) whose `spec.md` has
   `status: completed` are historical: work history kept in place. Browsing and search MUST hide them unless
   `--history` is passed; the rules check them only when they are named as explicit targets. The bundle's
   `feedback/` directory is the exception: a feedback file stays `open` until a feedback-hygiene session settles it,
   so it MUST stay current whatever the bundle's status (`SPEC-open-feedback-and-progress`).

### 3.2 IDs and Kinds

An ID is `<PREFIX>-<slug>`: one of the prefixes below, a dash, then a letter or digit followed by letters, digits,
`_` and `-`. The prefix names the kind. The location column is where `RULE-id-convention` requires the document to
live; the index itself does not check it.

| Prefix | Kind | Location (checked by the rules) |
| --- | --- | --- |
| `CAP` | `capability` | `docs/capabilities/<area>/CAP-<AREA>-<slug>.md` |
| `US` | `story` | `docs/stories/<area>/US-<slug>.md` |
| `ARCH` | `architecture` | `docs/architecture/ARCH-[<NN>[-<n>]-]<slug>.md` |
| `ADR` | `decision` | `docs/decisions/<YYYY-MM>/<YYYYMMDD>-<slug>.md` |
| `PROP` | `proposal` | `docs/proposals/...` |
| `PADR` | `proposal-decision` | `docs/proposals/...` |
| `SPEC`, `PLAN`, `TASKS`, `REC` | `spec`, `plan`, `tasks`, `reconcile` | `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/{spec,plan,tasks,reconcile}.md` |
| `FB` | `feedback` | `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/feedback/<slug>.md`, `specs/<YYYY-MM>/feedback/<YYYYMMDD>-<slug>.md` |
| `MAT` | `material` | `docs/materials/...` |

The table order is the kind order: `devkit spec list` sorts by it. Living Spec documents of a namespace live under
`docs/packages/<name>/` with the same layout (`CAP-DOCS-namespaces`).

### 3.3 References

1. **Full IDs only**: A document MUST reference another by its full ID, never by a Markdown path.
2. **Relation fields** (frontmatter): `stories`, `capabilities`, `related_stories`, `related_capabilities` hold a list
   of IDs; `spec` and `plan` hold one ID. A field of the wrong shape (a scalar where a list is expected, a non-string
   item) is recorded as an issue and skipped; `RULE-document-reference` reports it.
3. **Prose references**: a single-backtick code span holding exactly one ID (the canonical form) or the same ID in
   square brackets (the bracket form, which `devkit rules fix` converts to the canonical form).
4. **Prose exclusions**: fenced code blocks (a run of three or more backticks or tildes indented at most three
   spaces, closed by a run of the same character at least as long), lines indented four or more spaces, HTML
   comments, backslash escapes, every other inline code span, `~~strikethrough~~`, and link or image labels
   (`[label](...)`, `[label][ref]`, `[label]:`, `![alt]`) MUST NOT yield references. An inline span may continue on
   the following lines of its paragraph; an opener nothing closes is literal text.
5. **Self heading**: on a heading line starting with `# `, the document's own ID (the `# [<ID>] Title` token) is not a
   reference.
6. **Provenance**: `proposal` (the proposal a spec was handed off from) is provenance, not a reference. It is kept
   apart from the reference graph: `refs` does not show it and reference rules do not resolve it.
7. **Positions**: every reference MUST keep its field (`body` for prose), its 1-based line and column, and the
   character offsets of the ID in the file (quotes included for a quoted frontmatter value), so a fix rewrites
   exactly what was read and nothing else.

### 3.4 Index

1. **Rebuilt per load**: `DocumentIndex.load` walks `docs/` and `specs/` (sorted, symbolic links skipped) or reads the
   file list a caller supplies; the rules supply the run's workspace cache, so a snapshot run (`check --staged`,
   `--ci`) indexes the snapshot and a fix is seen by the recheck.
2. **Parse reuse**: a parsed document is reused while its path and text are unchanged, so the rules of one run parse
   every file once.
3. **Resolution**: resolving an ID MUST return the one document that declares it, else raise `SPEC_ID_UNRESOLVED`
   (no document) or `SPEC_ID_DUPLICATE` (several; `[TARGET]` lists their paths).
4. **Reference queries**: outgoing references are grouped by target ID and incoming references by source ID, both in
   ID order. A target that no single document declares stays in the result (a dangling or ambiguous reference).
5. **Rewriting**: `rewrite` replaces only parsed references whose target a mapping names, never other occurrences
   of the ID. A quoted frontmatter value keeps its quote style; a bracket reference becomes a code-span reference
   (mapping an ID to itself converts the notation only).

## 4. Interfaces & Data Contracts

### 4.1 Frontmatter Fields Read by the Model

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | string | The document ID. |
| `reconcile_id` | string | The ID of a reconcile record (used when `id` is absent). |
| `status` | string | Lifecycle status; `completed` on a `spec.md` makes its bundle historical, its feedback aside. |
| `title` | string | Display title (any language). |
| `summary` | string | One or two English sentences; embedded by search. |
| `area` | string | Area of a capability or story (its directory). |
| `stories`, `capabilities`, `related_stories`, `related_capabilities` | list of IDs | Relation fields. |
| `spec`, `plan` | ID | Relation fields. |
| `proposal` | ID | Provenance of a handed-off spec. |
| `namespace` | string | Namespace of a spec or proposal bundle (`CAP-DOCS-namespaces`). |
| `entrypoints` | list of paths | Code entrypoints of a capability or story (`CAP-TRACE-code-entrypoints`). |

### 4.2 Document Record (JSON)

Commands that print documents in JSON use the record `id`, `kind`, `path` (workspace-relative), `status`, `title`,
`area`, `summary`; an absent or non-string value is `""`. A reference is `target`, `source`, `path`, `field`, `line`,
`column`, `bracket` (`true` for the bracket form).

### 4.3 Error Codes

| Code | Level | Class | Condition |
| --- | --- | --- | --- |
| `SPEC_DOCUMENT_INVALID` | `WARNING` | `DocumentInvalidWarning` | A file under `docs/` or `specs/` cannot be read as UTF-8 or has malformed frontmatter (including a non-string `id`, `reconcile_id` or `status`); it is left out of the index. Returned under `notices`; exit `0`, `1` under `--strict`. |
| `SPEC_ID_UNRESOLVED` | `ERROR` (`INPUT_ERROR`) | `UnresolvedIdError` | No document declares the ID. |
| `SPEC_ID_DUPLICATE` | `ERROR` (`MAINTENANCE`) | `DuplicateIdError` | More than one document declares the ID; `[TARGET]` lists them. |

### 4.4 Library

```python
from devkit_spec.documents import DocumentIndex, Kind, is_id, kind_of, rewrite

index = DocumentIndex.load(root)  # documents, by_id, problems (SPEC_DOCUMENT_INVALID), historical
document = index.resolve("CAP-CORE-search")  # UnresolvedIdError, DuplicateIdError
index.outgoing(document)  # {target ID: [Reference, ...]}
index.incoming(document.id)  # {source ID: [Reference, ...]}
index.is_historical(document)  # a file of a completed spec bundle outside its feedback/
```

`parse_document(path, text)` reads one document (`None` without a well-formed ID); `visible_lines` is the prose
scanner behind reference extraction; `SOURCE_DIRECTORIES`, `is_document_file` and `in_source_directory` expose the
file selection.
