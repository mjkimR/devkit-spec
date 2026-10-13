# Code Entrypoints

Capabilities and stories may declare `entrypoints` in their frontmatter: the files and directories where their
implementation starts. An entrypoint is an anchor for finding code from a document and documents from code, not a
complete list of the implementation and not proof that the code implements the document. devkit-spec keeps the
declarations alive (`RULE-code-entrypoints`), finds documents by path (`devkit spec list --file`) and proposes
declarations from the spec bundles that already name both sides (`devkit spec entrypoints derive`).

Ported from specrig's `CAP-HARN-code-entrypoints` and `SPEC-entrypoint-derivation`; the implementation is
`devkit_spec.entrypoints`.

## 1. Path Contract

```yaml
entrypoints:
  - src/example/engine.py
  - src/example/cli/
```

- A list of strings; the field may be omitted or empty.
- Each path is relative to the workspace root and written with `/`, whatever directory the document is in
  (documents under `docs/packages/<name>/` too). `./` and a trailing `/` are normalized away; `.` is the whole
  workspace. Files and directories are both allowed.
- Invalid: an empty value, an absolute path, a `..` segment, a backslash, a colon (drive), a glob character (`*`,
  `?`, `[`, `]`), NUL or a line break (`SPEC_ENTRYPOINTS_PATH_INVALID` where a command takes a path).
- Paths compare by whole segments, case-sensitively: `src/a` covers `src/a/b.py`, not `src/ab`.

Entrypoint-bearing documents are the Markdown files under `docs/capabilities/` and `docs/stories/`, and under the
same directories of a namespace docs root `docs/packages/<name>/`.

## 2. RULE-code-entrypoints

Phase linter, severity error, not fixable. For each targeted capability or story that declares `entrypoints`: the
field is a list of strings, each a valid path (section 1), each an existing file or directory inside the workspace
with symbolic links resolved (a link pointing outside counts as missing). `check --staged` and `--ci` resolve paths
in the snapshot's tree, where an empty directory does not exist.

As every devkit rule, it reports only in the documents the run targets. Deleting code without touching the document
that declares it is caught by `devkit rules check` without targets (the whole workspace), not by the commit gate or
`--ci`, whose targets are the changed files. specrig's Git-snapshot gate checked every declaration against the
snapshot tree; devkit's targeting has no hook for frontmatter paths yet.

## 3. Reverse Query

`devkit spec list [capability|story] --file <path>` lists the documents whose `entrypoints` equal the path, lie under
it, or are a directory containing it ([documents reference](documents/reference.md)). The path need not exist, so a
deleted file still finds its documents.

## 4. Derivation: `devkit spec entrypoints derive`

```text
devkit spec entrypoints derive (--spec <dir> | --all [--status <csv>] [--min-count <n>])
    [--code <path>]... [--exclude <path>]... [--apply [--target <id|path>]...] [-w <root>] [--format json]
```

A spec bundle already declares both sides of a link: `tasks.md` names the code each task may touch on its
`_Boundary` lines, and `reconcile.md` names the Living Spec documents the change reconciled. The command joins them.

**Code side.** Every `_Boundary` line of `tasks.md` outside fenced code blocks, attached to the checklist item above
it (task `0` before the first one). The label may carry bold or italic markers and the line may be a list item. The
value is split on commas; each entry loses backticks and `(...)` notes, and a value wrapped in `**...**` loses the
markers. An entry is skipped as `not-a-path` (empty, `N/A`, `none`), `invalid-path` (section 1, globs included) or
`excluded-tree` (`.`, `docs/...`, `specs/...`). Each path counts once per bundle, with the first task naming it; a
candidate under another candidate of the same bundle is folded into the shortest such ancestor (`folded_into`).

**Document side.** Every `reconcile.md` target (the shape `RULE-reconcile-contract` checks: `targets` of `file` and
`resolution`) is a document unless its resolution is `waived` or it is not entrypoint-bearing (section 1). A target
that is not an indexed document is skipped as `missing-doc` (no such file) or `not-a-document` (a file without an
ID, with malformed frontmatter, a `README.md` or a template).

**Pairs.** Every document is paired with every candidate. `state` is `declared` when an existing entrypoint equals
the path or is a directory containing it, else `new`; `exists` tells whether the path is in the working tree.

**Scope.** `--spec <dir>` derives one bundle (the directory relative to the workspace root, or absolute). A missing
`tasks.md` or `reconcile.md` is `SPEC_ENTRYPOINTS_INPUT_MISSING`; an unreadable one, or a `reconcile.md` without
frontmatter or with malformed `targets`, is `SPEC_ENTRYPOINTS_INPUT_INVALID`. `spec.md` is optional and labels the
bundle with its ID (the directory name without one).

`--all` derives every bundle whose `specs/<YYYY-MM>/<bundle>/spec.md` status is in `--status` (default
`completed,in-progress`, case-insensitive), in spec ID order. A bundle without inputs is skipped (`kind=bundle`,
`input-missing` or `invalid-input`). Pairs are merged by (document, path): folded pairs are left out, each merged pair
carries `count` (the number of specs that produced it) and `specs`, and pairs below `--min-count` (default 1) are
dropped.

**Filters.** `--code <path>` keeps only candidates equal to or under a path: the review's selection. `--exclude
<path>` drops candidates equal to or under a path (hub files every bundle touches) and reports each as
`reason=excluded`.

**Apply.** Nothing is written without `--apply`. With it, for each document (only those named by `--target`, an ID
or a path that must be among the derived documents before `--code`/`--exclude`, else
`SPEC_ENTRYPOINTS_TARGET_UNKNOWN`), the `new` pairs whose path exists and is not folded are appended to the
document's `entrypoints`: directories with a trailing `/`, sorted, after the existing entries. An addition an existing
entry or another addition already covers is dropped, so a document never lists a directory and files inside it from
one apply. Folded and missing paths are reported as `kind=apply` with `reason=folded` or `missing-path`. Only the
`entrypoints` block of the frontmatter is rewritten (in place, or before `created_at`, or at the end of the header);
every other byte, the line endings included, is kept, and the file is replaced atomically. A rerun writes nothing. A
document that cannot be read or written is `SPEC_ENTRYPOINTS_APPLY_FAILED` after the result, which lists the
documents that were written.

### Output

```text
[PAIR: CAP-CORE-engine code=src/engine spec=SPEC-engine task=1 state=new exists=yes]
[PAIR: CAP-CORE-engine code=src/engine/parse.py spec=SPEC-engine task=2 state=new exists=yes folded_into=src/engine]
[SKIPPED: N/A kind=boundary spec=SPEC-engine task=3 reason=not-a-path]
[SKIPPED: docs/decisions/2026-10/20261001-x.md kind=target spec=SPEC-engine reason=not-entrypoint-bearing]
[APPLIED: CAP-CORE-engine path=docs/capabilities/core/CAP-CORE-engine.md added=src/engine/]
[SUMMARY: pairs=2 new=2 declared=0 skipped=2 applied=1]
```

With `--all`, a pair carries `count=` and `specs=` (comma-separated) instead of `spec=` and `task=`. `[SKIPPED: ...]`
carries `spec=` and `task=` when known. Skip reasons: `not-a-path`, `invalid-path`, `excluded-tree`, `excluded`
(`kind=boundary`); `waived`, `not-entrypoint-bearing`, `missing-doc`, `not-a-document` (`kind=target`);
`input-missing`, `invalid-input` (`kind=bundle`); `folded`, `missing-path` (`kind=apply`).

`--format json` prints one object: `pairs` (`doc`, `doc_path`, `code`, `spec`, `task`, `folded_into`, or `count` and
`specs` with `--all`, then `state`, `exists`), `skipped` (`kind`, `value`, `spec`, `task`, `reason`), `applied`
(`doc`, `doc_path`, `added`), `summary`, `errors` and `notices`. Files that could not be indexed are
`SPEC_DOCUMENT_INVALID` warnings. Option conflicts (`--spec` with `--all` or neither, `--status`/`--min-count` with
`--spec`, `--min-count` below 1, `--target` without `--apply`) are devkit's `ARGUMENT_INVALID`.

### Review before apply

The command joins declarations; it does not judge relevance. A bundle that touched a capability only for wording
still pairs it with every path its tasks named. The `spec-entrypoints` skill holds the review: drop documents touched
only for metadata, keep directory candidates only for documents that own the package, exclude hub files, then apply
per document with `--target` and `--code`. Inside `spec-sync` it runs on the current bundle; as a backfill it runs
over `--all` with a `--min-count` threshold.

## 5. Differences from specrig

- Output follows devkit's contract (`[PAIR: ...]` sentinels, `yes`/`no`, `SPEC_ENTRYPOINTS_*` codes, devkit's
  `ARGUMENT_INVALID` for option conflicts) instead of specrig's `pair key=value` lines.
- A reconcile target that exists but is not an indexed document is `not-a-document` (specrig: `missing-doc`, or a
  pair labelled with the file stem for a file without an ID).
- Bundles for `--all` come from the document index: a `spec.md` with malformed frontmatter is a
  `SPEC_DOCUMENT_INVALID` warning and its bundle is left out (specrig stopped with `SPEC_SCAN_FAILED`).
- Replacing an existing `entrypoints` value also removes a zero-indented sequence or a multi-line flow list;
  specrig removed only indented `- ` items.
- `RULE-code-entrypoints` follows devkit's targeting (section 2).
