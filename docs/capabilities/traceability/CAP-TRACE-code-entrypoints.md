---
id: CAP-TRACE-code-entrypoints
title: Code Entrypoints
summary: Defines the entrypoints frontmatter of capabilities and stories that anchors documents to code paths, its path contract, the RULE-code-entrypoints liveness check, the reverse lookup by path, and devkit spec entrypoints derive, which proposes and applies declarations from spec bundles.
area: traceability
status: active
stories:
  - US-keep-the-living-spec-consistent
  - US-run-parallel-work-safely
entrypoints:
  - src/devkit_spec/entrypoints/
  - src/devkit_spec/cli/entrypoints.py
  - src/devkit_spec/rules/code_entrypoints.py
created_at: 2026-10-13
---

# [CAP-TRACE-code-entrypoints] Code Entrypoints

## 1. Summary

Capabilities and stories MAY declare `entrypoints` in their frontmatter: the files and directories where their
implementation starts. An entrypoint is an anchor for finding code from a document and documents from code. devkit-spec
keeps the declarations alive (`RULE-code-entrypoints`), finds documents by path (`devkit spec list --file`,
`CAP-DOCS-document-lookup`) and proposes declarations from the spec bundles that already name both sides
(`devkit spec entrypoints derive`). `devkit_spec.entrypoints` implements it.

## 2. Scope & Boundary

- **In-Scope**: the path contract, which documents carry `entrypoints`, the rule, the reverse query, derivation from
  spec bundles, review before apply, and writing chosen declarations.
- **Out-of-Scope** (Non-Goals):
  - A complete list of the implementation, or proof that the code implements the document. Scope Excluded: an
    entrypoint is where reading starts; coverage and correctness are for tests and review.
  - Glob patterns. Scope Excluded: paths are literal, so a declaration is checkable and a reverse query is exact.
  - Judging the relevance of derived pairs. Scope Excluded: derivation joins declarations mechanically; the
    `spec-entrypoints` skill holds the review (`CAP-HARN-agent-guidance`).
  - Automatic repair of dead entrypoints. Scope Excluded: the rule never guesses whether code moved or the
    declaration is obsolete.

## 3. Business Rules & Policies

### 3.1 Path Contract

```yaml
entrypoints:
  - src/example/engine.py
  - src/example/cli/
```

1. The field is a list of strings; it MAY be omitted or empty.
2. Each path is relative to the workspace root and written with `/`, whatever directory the document is in
   (documents under `docs/packages/<name>/` too; never package-relative). `./` and a trailing `/` are normalized away;
   `.` is the whole workspace. Files and directories are both allowed.
3. A path MUST NOT be empty, absolute, contain a `..` segment, a backslash, a colon (drive), a glob character (`*`,
   `?`, `[`, `]`), NUL or a line break. Where a command takes a path argument under this contract, a violation fails
   with `SPEC_ENTRYPOINTS_PATH_INVALID`.
4. Paths compare by whole segments, case-sensitively: `src/a` covers `src/a/b.py`, not `src/ab`.
5. **Entrypoint-bearing documents** are the Markdown files under `docs/capabilities/` and `docs/stories/`, and under
   the same directories of a namespace docs root `docs/packages/<name>/` (`CAP-DOCS-namespaces`).

The same contract governs the code paths of the work-scope registry (`CAP-COLL-work-scope-registry`).

### 3.2 `RULE-code-entrypoints`

Phase `linter`, severity `error`, not fixable (`CAP-GOV-spec-rules`).

1. For each targeted capability or story that declares `entrypoints`: the field MUST be a list of strings, each a
   valid path (section 3.1), each an existing file or directory inside the workspace with symbolic links resolved (a
   link pointing outside counts as missing: "Dead code entrypoint").
2. `check --staged` and `--ci` resolve paths in the snapshot's tree, where an empty directory does not exist.
3. It reports in the documents the run targets and, in a snapshot run, also in every current document that declares
   a path the diff deletes (read from devkit's `ctx.snapshot`), so deleting code without touching the document that
   declares it fails the commit gate and CI.
4. Remediation: restore the code, point the declaration at where the code moved, or remove an obsolete declaration;
   `devkit spec entrypoints derive --spec <bundle>` proposes paths.

### 3.3 Reverse Query

`devkit spec list [capability|story] --file <path>` lists the documents whose `entrypoints` equal the path, lie under
it, or are a directory containing it (`CAP-DOCS-document-lookup`). The path need not exist, so a deleted file still
finds its documents.

### 3.4 Derivation Inputs

A spec bundle already declares both sides of a link: `tasks.md` names the code each task may touch on its `_Boundary`
lines, and `reconcile.md` names the Living Spec documents the change reconciled. `devkit spec entrypoints derive`
joins them.

1. **Code side**: every `_Boundary` line of `tasks.md` outside fenced code blocks, attached to the checklist item
   above it (task `0` before the first one; tasks are numbered by checklist position from `1`). The label MAY carry
   bold or italic markers and the line MAY be a list item. The value MAY continue on the following lines indented
   deeper than the label line; a blank line, a list item (bullet or ordered), another `_Boundary` line, a fence or a
   line indented no deeper ends it, and the lines are joined with a space (`SPEC-boundary-continuation-lines`). The
   value is split on commas; each entry loses backticks and `(...)` notes, and a value wrapped in `**...**` loses the
   markers.
2. **Skipped entries** (`kind=boundary`): `not-a-path` (empty, `N/A`, `none`), `invalid-path` (section 3.1, globs
   included) and `excluded-tree` (`.`, `docs/...`, `specs/...`).
3. **Candidates**: each path counts once per bundle, with the first task naming it. A candidate under another
   candidate of the same bundle is folded into the shortest such ancestor (`folded_into`).
4. **Document side**: every `reconcile.md` target (the shape `RULE-reconcile-contract` checks: `targets` of `file`
   and `resolution`) is a document unless its resolution is `waived` or it is not entrypoint-bearing. A target that
   is not an indexed document is skipped as `missing-doc` (no such file) or `not-a-document` (an existing file without
   an ID, with malformed frontmatter, a `README.md` or a template). Each document counts once per bundle.
5. **Pairs**: every document is paired with every candidate. `state` is `declared` when an existing entrypoint equals
   the path or is a directory containing it, else `new`; `exists` tells whether the path is in the working tree.

### 3.5 Derivation Scope and Filters

1. **`--spec <dir>`** derives one bundle (the directory relative to the workspace root, or absolute, inside the
   workspace). A missing `tasks.md` or `reconcile.md` fails with `SPEC_ENTRYPOINTS_INPUT_MISSING`; an unreadable one,
   or a `reconcile.md` without frontmatter or with malformed `targets`, with `SPEC_ENTRYPOINTS_INPUT_INVALID`.
   `spec.md` is optional and labels the bundle with its ID (the directory name without one).
2. **`--all`** derives every bundle whose `specs/<YYYY-MM>/<bundle>/spec.md` status is in `--status` (default
   `completed,in-progress`, comma-separated, case-insensitive), in spec ID order. Bundles come from the document index:
   a `spec.md` with malformed frontmatter is a `SPEC_DOCUMENT_INVALID` warning and its bundle is left out. A bundle
   without inputs is skipped (`kind=bundle`, `input-missing` or `invalid-input`). Pairs are merged by (document,
   path): folded pairs are left out, each merged pair carries `count` (the number of specs that produced it) and
   `specs`, and pairs below `--min-count` (default `1`) are dropped.
3. **`--code <path>`** (repeatable) keeps only candidates equal to or under a path: the review's selection.
4. **`--exclude <path>`** (repeatable) drops candidates equal to or under a path (hub files every bundle touches) and
   reports each as `reason=excluded` (`kind=boundary`).
5. `--code` and `--exclude` values follow the path contract (`SPEC_ENTRYPOINTS_PATH_INVALID`).

### 3.6 Apply

1. Nothing MUST be written without `--apply`.
2. With `--apply`, for each document (only those named by `--target`, an ID or a workspace-relative path that MUST be
   among the derived documents before `--code`/`--exclude`, else `SPEC_ENTRYPOINTS_TARGET_UNKNOWN`), the `new` pairs
   whose path exists and is not folded are appended to the document's `entrypoints`: directories with a trailing `/`,
   sorted, after the existing entries.
3. An addition that an existing entry or another addition already covers is dropped, so one apply never lists a
   directory and files inside it.
4. Folded and missing paths are reported as `kind=apply` with `reason=folded` or `missing-path`.
5. Only the `entrypoints` block of the frontmatter is rewritten: in place (every line of the old value, including a
   zero-indented sequence or a multi-line flow list), else before `created_at`, else at the end of the header. Every
   other byte, the line endings included, MUST be kept, and the file is replaced atomically (its mode preserved).
6. A rerun MUST write nothing (every written path is then `declared`).
7. A document that cannot be read or written fails with `SPEC_ENTRYPOINTS_APPLY_FAILED` after the result, which lists
   the documents that were written; the others are still written.

### 3.7 Review Before Apply

A bundle that touched a capability only for wording still pairs it with every path its tasks named. The
`spec-entrypoints` skill holds the review: drop documents touched only for metadata, keep directory candidates only
for documents that own the package, exclude hub files, then apply per document with `--target` and `--code`. Inside
`spec-sync` it runs on the current bundle; as a backfill it runs over `--all` with a `--min-count` threshold.

## 4. Interfaces & Data Contracts

### 4.1 Command

```text
devkit spec entrypoints derive (--spec <dir> | --all [--status <csv>] [--min-count <n>])
    [--code <path>]... [--exclude <path>]... [--apply [--target <id|path>]...] [-w <root>] [--format json]
```

Option conflicts fail with devkit's `ARGUMENT_INVALID`: `--spec` with `--all` or neither; `--status` or
`--min-count` with `--spec`; `--min-count` below `1`; `--target` without `--apply`; a `--spec` outside the workspace.

### 4.2 Text Output

```text
[CANDIDATES: CAP-CORE-engine path=docs/capabilities/core/CAP-CORE-engine.md new=src/engine missing=- folded=src/engine/parse.py declared=-]
[SKIPPED: N/A kind=boundary spec=SPEC-engine task=3 reason=not-a-path]
[SKIPPED: docs/decisions/2026-10/20261001-x.md kind=target spec=SPEC-engine reason=not-entrypoint-bearing]
[APPLIED: CAP-CORE-engine path=docs/capabilities/core/CAP-CORE-engine.md added=src/engine/]
[SUMMARY: pairs=2 new=2 declared=0 skipped=2 applied=1]
```

- `[CANDIDATES: <doc-id> path= new= missing= folded= declared=]` per document, in document path order: its
  candidate paths by state, comma-separated in code order (`-` for none). `new`: not declared and present in the
  working tree; `missing`: not declared and absent; `folded`: covered by a same-bundle ancestor candidate; `declared`:
  covered by an existing entrypoint. With `--all` each path carries its spec count, `src/engine(2)`. One line per
  document keeps the review per document, as `--apply --target` applies it; `--format json` lists every pair with
  its `spec` and `task` (or `count` and `specs`) and `folded_into`.
- `[SKIPPED: <value> kind= spec= task= reason=]` per input or candidate left out; `spec=` and `task=` only when known.
- `[APPLIED: <doc-id> path= added=]` per document written (`added` comma-separated).
- `[SUMMARY: pairs= new= declared= skipped= applied=]` last.

| `kind` | Reasons |
| --- | --- |
| `boundary` | `not-a-path`, `invalid-path`, `excluded-tree`, `excluded` |
| `target` | `waived`, `not-entrypoint-bearing`, `missing-doc`, `not-a-document` |
| `bundle` | `input-missing`, `invalid-input` |
| `apply` | `folded`, `missing-path` |

### 4.3 JSON Keys

One object: `pairs` (`doc`, `doc_path`, `code`, then `spec`, `task`, `folded_into`, or `count` and `specs` with
`--all`, then `state`, `exists`), `skipped` (`kind`, `value`, `spec`, `task`, `reason`), `applied` (`doc`,
`doc_path`, `added`), `summary` (`pairs`, `new`, `declared`, `skipped`, `applied`), `errors` and `notices`. Files that
could not be indexed are `SPEC_DOCUMENT_INVALID` warnings under `notices`.

### 4.4 Exit Codes

`0` success (pairs or none); `2` an error (input, target, path, apply or argument). Warnings exit `0` (`1` under
`--strict`).

### 4.5 Error Codes

| Code | Level | Class | Condition |
| --- | --- | --- | --- |
| `SPEC_ENTRYPOINTS_INPUT_MISSING` | `ERROR` (`INPUT_ERROR`) | `EntrypointsInputMissingError` | `--spec`: the bundle has no `tasks.md` or `reconcile.md`. |
| `SPEC_ENTRYPOINTS_INPUT_INVALID` | `ERROR` (`MAINTENANCE`) | `EntrypointsInputInvalidError` | `--spec`: `tasks.md` or `reconcile.md` cannot be read, or `reconcile.md` has no frontmatter or malformed `targets`. |
| `SPEC_ENTRYPOINTS_PATH_INVALID` | `ERROR` (`INPUT_ERROR`) | `EntrypointsPathError` | A `--code` or `--exclude` path breaks the path contract. |
| `SPEC_ENTRYPOINTS_TARGET_UNKNOWN` | `ERROR` (`INPUT_ERROR`) | `EntrypointsTargetError` | A `--target` ID names no document, or the ID or path is not among the derived documents. |
| `SPEC_ENTRYPOINTS_APPLY_FAILED` | `ERROR` (`MAINTENANCE`) | `EntrypointsApplyError` | `--apply` could not read or write some documents; `[TARGET]` lists them, the documents listed as applied were written. |
| `SPEC_ID_DUPLICATE` | `ERROR` (`MAINTENANCE`) | `DuplicateIdError` | A `--target` ID is declared by several documents. |
| `SPEC_DOCUMENT_INVALID` | `WARNING` | `DocumentInvalidWarning` | A file could not be indexed; a malformed `spec.md` leaves its bundle out of `--all`. |
| `ARGUMENT_INVALID` | `ERROR` (`INPUT_ERROR`) | `devkit.core.ArgumentError` | An option conflict (section 4.1). |

### 4.6 Library

`devkit_spec.entrypoints`: `normalize`, `covers`, `overlaps`, `exists`, `entrypoint_bearing`, `living_path` (the path
contract); `load_bundle`, `parse_boundaries` (inputs); `derive`, `aggregate`, `select`, `exclude`, `classify_boundary`,
`declared_entrypoints` (pairs); `apply`, `collapse`, `set_entrypoints` (writing). Libraries never print; the command
renders the results.
