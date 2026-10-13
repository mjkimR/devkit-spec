# [RULE-code-entrypoints] Live Code Entrypoints

## 1. Overview

A capability or story may declare `entrypoints` in its frontmatter: the files and directories where its
implementation starts. They are anchors for finding the code (`devkit spec list capability --file <path>` finds the
documents that own a path), not a complete list of the implementation and not proof that the code implements the
document. The rule keeps every declared path alive, so an agent following an entrypoint never lands on nothing.

- **Phase and severity**: `linter`, `error`. Shipped by the `spec` bundle (preset `core`).
- **What is checked**: capabilities (`CAP-`) and stories (`US-`) under `docs/capabilities/`, `docs/stories/` and the
  same directories of a namespace docs root `docs/packages/<name>/`, when they declare `entrypoints`. An omitted
  field and an empty list pass.
- **Path contract**: paths are relative to the workspace root, written with `/`, whatever the document's directory
  (also under `docs/packages/<name>/`). `./` and a trailing `/` are normalized; `.` is the whole workspace. Files
  and directories are both allowed; comparison is by whole path segments and case-sensitive (`src/a` covers
  `src/a/b.py`, not `src/ab`).
- **Targeting and snapshots**: violations are reported in the targeted documents, so `devkit rules check` without
  targets checks every declaration. `--staged` and `--ci` check the documents the change touches and, in addition,
  every current document not matched by `[rules] exclude` that declares a path the diff deletes (or a directory
  containing it): deleting code without touching the document that declares it fails the commit gate too. Snapshot
  runs resolve paths in the snapshot's tree, where an empty directory does not exist.

## 2. Cause of Violation

Reported at the offending list item, or at the `entrypoints` key:

- The field is not a list: `entrypoints must be an array of path strings`.
- An item is not a string: `entrypoints must contain only path strings`.
- An item is empty or blank, absolute, or contains a backslash, a colon, a glob character (`*`, `?`, `[`, `]`), NUL
  or a line break: `invalid entrypoint '<value>': use a literal workspace-relative path`.
- An item has a `..` segment: `invalid entrypoint '<value>': parent traversal is forbidden`.
- The path is neither a file nor a directory inside the workspace, or is a symbolic link resolving outside it:
  `Dead code entrypoint: '<value>' (missing or outside workspace)`.

## 3. Remediation

Not fixable: the rule never guesses whether the code moved or the declaration is obsolete. Restore the code, point
the declaration at where the code moved, or remove an obsolete declaration.
`devkit spec entrypoints derive --spec <bundle>` proposes paths from a spec bundle's `tasks.md` boundaries.

## 4. Configuration

The rule has no settings. Project policy in `.devkit/config.toml` (`[rules] exclude`, `[rules.severity_overrides]`,
`[rules.phase_overrides]`) applies as to every rule.

## 5. Exceptions

There is no inline suppression. Remove a declaration rather than excuse it: an entrypoint is optional, and one that
does not exist misleads. Documents matched by `[rules] exclude` are not checked.

## 6. Example

```yaml
entrypoints:
  - src/example/engine.py
  - src/example/cli/
```
