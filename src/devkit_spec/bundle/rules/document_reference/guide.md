# RULE-document-reference

Documents refer to each other by full ID, never by Markdown path: `` `ADR-example` `` in prose, the bare ID in a
relation field. `stories` and `related_stories` take `US` IDs, `capabilities` and `related_capabilities` `CAP` IDs,
`spec` a `SPEC` ID and `plan` a `PLAN` ID.

Find a document's path with `devkit spec resolve <ID>` and what references it with
`devkit spec refs <ID> --direction in`. A missing or duplicated ID is fixed by hand; the rule never guesses which
document was meant.

## Violations

- A relation field of the wrong shape, a value that is not a full ID, or an ID of the wrong kind.
- A reference to an ID no document declares, or that several documents declare.
- `[ID]` in prose: write `` `ID` ``. `devkit rules fix` converts it.
- `` `PROP-<slug>` `` after the proposal was handed off: when it does not resolve and exactly one `SPEC-<slug>`
  exists, `devkit rules fix` replaces it with `SPEC-<slug>` (typically a reference added on another branch after the
  handoff). The fix never changes a spec's `proposal:` provenance field, skips completed specs and materials, and
  writes only the targets when the run names any.
- A relative Markdown link to a document that has an ID: replace it with the ID.
- An ID declared by several documents (reported on each), and a `PROP-<slug>` beside a `SPEC-<slug>`: handoff deletes
  the proposal, so the pair is an unfinished handoff or a reused slug. Remove the proposal or rename it.

## Scope

Reference extraction skips code fences, indented code, non-ID inline code, HTML comments, escapes, link labels,
`~~strikethrough~~` (a historical mention of a removed document stays allowed there) and a heading's own ID
([documents overview](https://github.com/mjkimR/devkit-spec/blob/main/docs/capabilities/documents/CAP-DOCS-document-model.md)). External URLs,
images, code files, documents without IDs and links with a fragment or query keep Markdown links.

Materials are free-form and not checked. Files of completed spec bundles are work history: checked only when named as
explicit targets, and never rewritten. Like every devkit rule, a violation is reported only in the files the run
targets: a commit checks the files it changes, `devkit rules check` without targets the whole workspace.

```markdown
See `ADR-example`.
```

```yaml
capabilities:
  - CAP-AREA-example
```
