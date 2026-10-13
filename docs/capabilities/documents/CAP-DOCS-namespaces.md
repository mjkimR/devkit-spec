---
id: CAP-DOCS-namespaces
title: Document Namespaces
summary: Defines monorepo namespaces, packages registered in [[tool.spec.namespaces]] that keep their own Living Spec under docs/packages/<name>/, how each document's namespace is determined, and how list and search select namespaces while IDs and references stay repository-wide.
area: documents
status: active
stories:
  - US-find-the-right-documents
entrypoints:
  - src/devkit_spec/namespaces.py
  - src/devkit_spec/config.py
created_at: 2026-10-13
---

# [CAP-DOCS-namespaces] Document Namespaces

## 1. Summary

A monorepo registers its packages as namespaces, each with its own Living Spec under `docs/packages/<name>/` (the
same layout as `docs/`). A namespace narrows what browsing shows, never what exists: `devkit spec list` and
`devkit spec search` show the selected namespace plus the global documents, while IDs, `resolve`, `refs` and the
reference rules stay repository-wide. `devkit_spec.namespaces` implements it.

## 2. Scope & Boundary

- **In-Scope**: the `[[tool.spec.namespaces]]` registry, namespace membership of documents, the selection options and
  the default selection, and how the rules treat namespace docs roots.
- **Out-of-Scope** (Non-Goals):
  - Namespaced IDs or per-package ID spaces. Scope Excluded: IDs stay unique across the repository and references
    cross packages freely. Rationale: a namespace prefix would change every reference when code moves between
    packages.
  - Writing the `namespace` field: `devkit spec new --namespace` (`CAP-DLV-spec-bundles`) and
    `devkit spec proposal new --namespace` (`CAP-DLV-proposal-incubation`); handoff carries it.
  - The rest of `[tool.spec]` (`worktree`, `scope`) and `devkit spec policy`: `CAP-DLV-project-policy`.

## 3. Business Rules & Policies

### 3.1 Registry

1. Each `[[tool.spec.namespaces]]` entry of `.devkit/config.toml` MUST have exactly the keys `name` and `path`.
2. `name` MUST be lowercase letters and digits in words joined by `-`, and MUST NOT be `global`.
3. `path` MUST be a safe workspace-relative directory (the package's source directory) without a trailing `/`.
4. Names and paths MUST be unique across entries.
5. A namespace's docs root is `docs/packages/<name>/`.
6. A malformed registry MUST fail with `SPEC_CONFIG_INVALID` in every command that reads it, and fail a rules run
   (`RULES_EXECUTION_FAILED`, exit `2`; `CAP-GOV-spec-rules`).

### 3.2 Membership

Every document belongs to exactly one namespace:

1. A document under `docs/packages/<name>/` belongs to `<name>`.
2. The files of a spec bundle (`specs/<YYYY-MM>/<bundle>/...`, month-level feedback excluded) or a proposal bundle
   (`docs/proposals/<bundle>/...`) belong to the namespace the bundle's `spec.md` or `proposal.md` names in its
   `namespace` frontmatter field, so a bundle keeps its package wherever the work happens. A value that is not a
   registered name counts as `global` (and `RULE-spec-format` reports it).
3. Everything else is `global`.

### 3.3 Selection

1. `--namespace NAME` selects that namespace plus the global documents; `--namespace global` selects only the global
   documents. An unknown name MUST fail with `ARGUMENT_INVALID` listing the valid names.
2. `--all-namespaces` selects every namespace. Combining it with `--namespace` MUST fail with `ARGUMENT_INVALID`.
3. Default: the namespace of the current directory: the one whose docs root contains it, else the one whose source
   `path` contains it (the deepest), else every namespace.
4. In a workspace without registered namespaces, the selection is always every namespace and output carries no
   `namespace` field in text.
5. Identity stays global: `resolve`, `refs` and the reference rules MUST ignore namespaces. Agents SHOULD use
   `--all-namespaces` to see cross-package impact.

### 3.4 Rules

The rules treat `docs/packages/<name>/` like `docs/`: `RULE-id-convention`, `RULE-spec-format`,
`RULE-traceability-link`, `RULE-code-entrypoints` and `RULE-document-summary` check its `capabilities/`, `stories/`
and `architecture/` directories as they check those of `docs/`. `RULE-spec-format` also checks that a proposal's or
spec's `namespace` names `global` or a registered namespace, and rechecks every one of them when a run targets
`.devkit/config.toml`. Entrypoint paths of a namespace's documents stay workspace-relative, never package-relative
(`CAP-TRACE-code-entrypoints`).

## 4. Interfaces & Data Contracts

### 4.1 Configuration

```toml
[[tool.spec.namespaces]]
name = "api"            # lowercase words joined by -, not "global"
path = "services/api"   # the package's source directory
```

### 4.2 Options

| Option | Commands | Effect |
| --- | --- | --- |
| `--namespace NAME` | `devkit spec list`, `devkit spec search` | `NAME` plus global documents; `global` for the global documents only. |
| `--all-namespaces` | `devkit spec list`, `devkit spec search` | Every namespace. |
| `--namespace NAME` | `devkit spec new`, `devkit spec proposal new` | Writes the bundle's `namespace` field (`CAP-DLV-spec-bundles`, `CAP-DLV-proposal-incubation`). |

### 4.3 Output

- Text: `list` and `search` lines carry `namespace=<name>` only in a workspace that registers namespaces.
- JSON: `list` and `search` carry `namespace` (the selection, `null` for every namespace); each `list` document
  carries its `namespace`.

### 4.4 Error Codes

| Code | Level | Class | Condition |
| --- | --- | --- | --- |
| `SPEC_CONFIG_INVALID` | `ERROR` (`INPUT_ERROR`) | `devkit_spec.errors.SpecConfigError` | `[tool.spec.namespaces]` is not an array of tables, an entry has keys other than exactly `name` and `path`, a name is malformed or `global`, a path is unsafe or ends with `/`, or a name or path is registered twice. |
| `ARGUMENT_INVALID` | `ERROR` (`INPUT_ERROR`) | `devkit.core.ArgumentError` | `--namespace` names an unregistered namespace, or is combined with `--all-namespaces`. |

### 4.5 Library

`devkit_spec.namespaces`: `select` (the selection of the options or the current directory), `detect` (the namespace
of a directory), `require` (validate a name), `namespace_resolver` (the namespace of each indexed document),
`living_path` (`docs/packages/<name>/X` as the `docs/X` it mirrors) and `docs_roots` (`docs` plus every namespace
docs root). `devkit_spec.config.read_spec_config(root).namespaces` reads the registry.
