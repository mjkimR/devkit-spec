# Documents: Overview

The document model of spec-driven development: which files are documents, how they are identified, and how they reference each other. `devkit_spec.documents` implements it; the `devkit spec resolve|refs|list` commands ([reference](reference.md)) and the spec rules read it. Ported from specrig's `documents` package; reference extraction matches specrig line for line (checked against every document of the specrig repository).

## 1. Documents and IDs

A document is a Markdown file under `docs/` or `specs/` whose frontmatter declares a well-formed ID: `id`, or `reconcile_id` for a reconcile file. The ID is `<PREFIX>-<slug>`: a prefix below, a dash, then a letter or digit followed by letters, digits, `_` and `-`.

| Prefix | Kind | Where it lives (checked by the rules) |
| --- | --- | --- |
| `CAP` | `capability` | `docs/capabilities/<area>/CAP-<AREA>-<slug>.md` |
| `US` | `story` | `docs/stories/<area>/US-<slug>.md` |
| `ARCH` | `architecture` | `docs/architecture/ARCH-[<NN>[-<n>]-]<slug>.md` |
| `ADR` | `decision` | `docs/decisions/<YYYY-MM>/<YYYYMMDD>-<slug>.md` |
| `PROP`, `PADR` | `proposal`, `proposal-decision` | `docs/proposals/...` |
| `SPEC`, `PLAN`, `TASKS`, `REC` | `spec`, `plan`, `tasks`, `reconcile` | `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/{spec,plan,tasks,reconcile}.md` |
| `FB` | `feedback` | `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/feedback/<slug>.md`, `specs/<YYYY-MM>/feedback/<YYYYMMDD>-<slug>.md` |
| `MAT` | `material` | `docs/materials/...` |

- IDs are repository-wide and must be unique. A file whose frontmatter has no ID, or an ID outside this grammar, is not a document (a README, a glossary).
- `README.md`, templates (`*-template.md`, `*_template.md`), directories starting with `.` and symbolic links are never documents.
- The frontmatter follows devkit's grammar (`devkit.core.frontmatter`); `id`, `reconcile_id` and `status` must be strings. A file that breaks either is left out of the index and reported as a `SPEC_DOCUMENT_INVALID` warning; the other documents stay usable.
- The files of a spec bundle whose `spec.md` has `status: completed` are **historical**: work history kept in place, hidden from `devkit spec list` unless `--history`.

## 2. References

A document references another by its full ID, never by a Markdown path. A reference is one of:

- **Frontmatter fields**: `stories`, `capabilities`, `related_stories`, `related_capabilities` (lists of IDs) and `spec`, `plan` (one ID). A field of the wrong shape is skipped and left to the rules.
- **Prose**: `` `ID` `` (the canonical form: a single-backtick code span holding exactly one ID) or `[ID]`.

Prose excludes fenced code blocks, lines indented four or more spaces, HTML comments, backslash escapes, other inline code, `~~strikethrough~~`, and link or image labels (`[label](...)`, `[label][ref]`, `[label]:`, `![alt]`). A heading line starting with `# ` does not reference the document's own ID (`# [CAP-...] Title`).

`proposal` is **provenance**, not a reference: the proposal a spec was handed off from. It is history, kept out of the reference graph.

Every reference keeps its field, 1-based line and column, and the character offsets of the ID in the file (quotes included for a quoted frontmatter value), so a rule can rewrite exactly what was read.

## 3. Namespaces

A monorepo registers its packages as namespaces, each with its own Living Spec under `docs/packages/<name>/`
(the same layout as `docs/`):

```toml
[[tool.spec.namespaces]]
name = "api"            # lowercase words joined by -, not "global"
path = "services/api"   # the package's source directory
```

- **Membership**: a document under `docs/packages/<name>/` belongs to `<name>`; the files of a spec bundle or a
  proposal bundle belong to the namespace their `spec.md` or `proposal.md` names in its `namespace` frontmatter field
  (`devkit spec new --namespace`, `devkit spec proposal new --namespace`; handoff carries it), so a bundle keeps its
  package wherever the work happens; everything else is `global`.
- **Browsing**: `devkit spec list` and `devkit spec search` show the selected namespace plus the global documents.
  The selection is `--namespace NAME` (`global` for the global documents only), `--all-namespaces`, or by default the
  namespace of the current directory: the one whose docs root contains it, else the one whose source path contains it
  (the deepest), else every namespace.
- **Identity stays global**: IDs are unique across the whole repository, and `resolve`, `refs` and the reference rules
  ignore namespaces. Use `--all-namespaces` to see cross-package impact.
- The rules treat `docs/packages/<name>/` like `docs/`, and `RULE-spec-format` checks that a `namespace` field names a
  registered namespace or `global`.

`devkit_spec.namespaces` implements it (`select`, `detect`, `namespace_resolver`, `living_path`, `docs_roots`).

## 4. Not Yet Ported

- Per-kind listing extras of specrig (`--with-story`, `--with-cap`, proposal priority and size, feedback filters).
