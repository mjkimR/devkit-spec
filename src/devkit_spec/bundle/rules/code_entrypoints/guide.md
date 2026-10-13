# RULE-code-entrypoints

A capability or story may declare `entrypoints` in its frontmatter: the files and directories where its
implementation starts. They are anchors for finding the code (`devkit spec list capability --file <path>` finds the
documents that own a path), not a complete list of the implementation and not proof that the code implements the
document. This rule keeps every declared path alive.

```yaml
entrypoints:
  - src/example/engine.py
  - src/example/cli/
```

## Path contract

- Paths are relative to the workspace root, written with `/`, whatever the document's directory (also under
  `docs/packages/<name>/`). `./` and a trailing `/` are normalized; `.` is the whole workspace.
- Files and directories are both allowed. Comparison is by whole path segments and case-sensitive.
- The field may be omitted or empty.

## Violations

- `entrypoints` is not a list, or an item is not a string.
- An item is empty, absolute, contains a `..` segment, a backslash, a colon, a glob character (`*`, `?`, `[`, `]`),
  NUL or a line break.
- A path is missing, or is a symbolic link that resolves outside the workspace ("Dead code entrypoint").

Not fixable: restore the code, point the declaration at where the code moved, or remove an obsolete declaration.
`devkit spec entrypoints derive --spec <bundle>` proposes paths from a spec bundle's `tasks.md` boundaries.

## Scope

Checks capabilities and stories under `docs/capabilities/`, `docs/stories/` and the same directories under
`docs/packages/<name>/`. Like every devkit rule, a violation is reported only in the documents the run targets:
`devkit rules check` without targets checks every declaration; `--staged` and `--ci` check the documents the
change touches and, in addition, every current document that declares a path the diff deletes, so deleting code
without touching the document that declares it fails the commit gate too. `--staged` and `--ci` resolve paths in the
snapshot's tree, where an empty directory does not exist.
