# [RULE-document-reference] Exact Document References

## 1. Overview

Documents refer to each other by full ID, never by Markdown path: `` `ADR-example` `` in prose, the bare ID in a
relation field. An ID survives moves and renames and resolves with one lookup; a path breaks silently and a partial or
ambiguous ID sends an agent to the wrong document. `stories` and `related_stories` take `US` IDs, `capabilities` and
`related_capabilities` `CAP` IDs, `spec` a `SPEC` ID and `plan` a `PLAN` ID.

- **Phase and severity**: `linter`, `error`. Shipped by the `spec` bundle (preset `core`).
- **What is checked**: the targeted documents (Markdown files under `docs/` and `specs/` whose frontmatter declares a
  well-formed ID): their relation fields, the `` `ID` `` and `[ID]` references in their prose, and their relative
  Markdown links. A spec's `proposal:` field records where it came from and is not checked.
- **What is not**: reference extraction skips code fences, indented code, inline code other than a single ID, HTML
  comments, escapes, link labels, `~~strikethrough~~` (a historical mention of a removed document stays allowed
  there) and a heading's own ID
  ([documents overview](https://github.com/mjkimR/devkit-spec/blob/main/docs/capabilities/documents/CAP-DOCS-document-model.md)).
  External URLs, images, code files, documents without IDs, links with a fragment or query and root-relative links
  keep Markdown links. Materials (`docs/materials/`, any `/materials/` directory) are free-form and not checked.
- **Completed specs**: files of a spec bundle whose `spec.md` is `completed` are work history: checked only when named
  as explicit targets, without the `[ID]` and handoff findings, and never rewritten.
- **Declarations**: the duplicate-ID and shared-slug checks cover every targeted document, materials and completed
  specs included.

## 2. Cause of Violation

- A relation field of the wrong shape: `<field> must be a list of IDs` (list fields), `<field> must be one ID`
  (`spec`, `plan`) or `<field> must contain string IDs`.
- A value that is not a full ID: `<field> must contain a full document ID, got '<value>'`.
- An ID of the wrong kind: `<field> takes <PREFIX>- IDs, got <ID>`.
- `[ID]` in prose (fixable): `` prose reference <ID> must be written `<ID>`, not [<ID>] ``.
- A `PROP-<slug>` reference that no longer resolves while exactly one `SPEC-<slug>` exists (fixable), typically added
  on another branch after the handoff: `` <ID> was handed off; reference `SPEC-<slug>` ``.
- A reference to an ID no document declares: `no document has the ID <ID>`; or that several declare: `<ID> is declared
  by <n> documents: <paths>`.
- A relative Markdown link to a document that has an ID: `` internal document link <target> must be the ID `<ID>` ``.
- An ID declared by several documents, reported at line 1 of each: `<ID> is declared by <n> documents: <paths>`.
- A `PROP-<slug>` beside a `SPEC-<slug>`, reported on the proposal: `PROP-<slug> shares its slug with SPEC-<slug>
  (<path>); a proposal and a spec cannot share a slug`. Handoff deletes the proposal, so the pair is an unfinished
  handoff or a reused slug.

## 3. Remediation

- **Autofix**: `devkit rules fix` converts `[ID]` to `` `ID` `` and replaces a handed-off `PROP-<slug>` with
  `SPEC-<slug>`, keeping a quoted frontmatter value's quote style. It never changes a spec's `proposal:` provenance
  field, skips completed specs, materials and files that are not valid UTF-8, and writes only the targets when the
  run names any.
- **By hand**: a missing or duplicated ID is fixed by hand; the rule never guesses which document was meant. Find a
  document's path with `devkit spec resolve <ID>` and what references it with `devkit spec refs <ID> --direction in`.
  Create the intended document or correct the exact ID; give each document its own ID, then update the references to
  it; replace a document link with the target's ID; remove an already handed-off proposal or rename it to an unused
  slug.
- **Related**: before replacing a link or a reference by hand, read the `spec:living-spec-writing` instruction
  (References) for which documents take an ID and which keep an ordinary link;
  `devkit rules explain` prints its path as a `[RELATED: ...]` line.

## 4. Configuration

The rule has no settings. Project policy in `.devkit/config.toml` (`[rules] exclude`, `[rules.severity_overrides]`,
`[rules.phase_overrides]`) applies as to every rule.

## 5. Exceptions

There is no inline suppression. Mention a removed document in `~~strikethrough~~`, or keep free-form notes under a
`materials/` directory; `[rules] exclude` removes a file from every rule.

## 6. Example

```markdown
See `ADR-example`.
```

```yaml
capabilities:
  - CAP-AREA-example
```
