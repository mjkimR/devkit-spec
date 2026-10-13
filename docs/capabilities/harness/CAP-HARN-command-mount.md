---
id: CAP-HARN-command-mount
title: devkit spec Command Mount and Output Conventions
summary: How the devkit spec command group mounts into devkit's command line through the devkit.commands entry point, its --version line, and the output conventions all its subcommands share (options, sentinel encoding, [PAGE] and [NEXT_CMD] paging, JSON, advisories, exit codes).
area: harness
status: active
created_at: 2026-10-13
stories:
  - US-adopt-in-an-existing-repository
entrypoints:
  - pyproject.toml
  - src/devkit_spec/cli/__init__.py
  - src/devkit_spec/cli/output.py
  - src/devkit_spec/errors.py
---

# [CAP-HARN-command-mount] devkit spec Command Mount and Output Conventions

## 1. Summary

devkit-spec has no executable of its own. Its click group `spec` (`devkit_spec.cli:cli`) is registered under the
`devkit.commands` entry point `spec`, and devkit's root group imports it only when `devkit spec` runs
([Command Plugins](https://github.com/mjkimR/devkit/blob/main/docs/architecture/command-plugins.md)). Agents reach
the whole toolchain through the one `devkit` executable of the project environment. Every subcommand is built on
`devkit.core.cli` and follows devkit's agent-first output contract
([Agent-First Output](https://github.com/mjkimR/devkit/blob/main/docs/architecture/agent-output.md)). Rationale:
`ADR-mount-under-the-devkit-command-line`.

## 2. Scope & Boundary

- **In-Scope**: the entry points of the package, the `devkit spec` group and its `--version` option, the subcommand
  catalog, and the conventions shared by all subcommands: options, sentinel encoding, paging, JSON, advisories, exit
  codes and the `SPEC_` code namespace.
- **Out-of-Scope**: each subcommand's own contract (see the catalog in 4.2); devkit's root command line, plugin
  loading and the Agent Advisory Protocol renderer.
- **Non-Goals**:
  - **Scope Excluded**: a separate `devkit-spec` console script. `devkit --version` reports devkit itself; the
    package version is `devkit spec --version`.
  - **Scope Excluded**: terminal-dependent output (colour, tables, progress) on stdout.

## 3. Business Rules & Policies

1. **stdout is the result**: a command MUST print one-line `[KIND: ...]` sentinels, or exactly one JSON object under
   `--format json`; stderr carries Agent Advisory Protocol blocks (`[ERROR]`, `[WARN]`, `[NOTICE]`) and `[INFO]` log
   lines only under `-v`.
2. **Errors are advisories**: a failure or refusal MUST be raised as an `AdvisoryError` subclass of
   `devkit_spec.errors.SpecError` with a stable `SPEC_`-prefixed code and a deterministic `[ACTION]`; agents branch on
   codes, never on message text. devkit's own codes (`ARGUMENT_INVALID`, `GIT_FAILED`, `CONFIG_INVALID`, ...) pass
   through unchanged.
3. **Warnings and notices are results**: something a successful operation must report is returned under `notices`
   at `WARNING` or `NOTICE` and printed after the result; it never changes the exit code except under `--strict`.
4. **Libraries never print**: commands write only through `devkit.core.cli` (`boundary`, `echo_json`,
   `echo_notices`, `exit_on_warnings`) and the helpers in `devkit_spec.cli.output`.
5. **Every code is documented**: each `code` a `SpecError` subclass declares MUST appear as `` `CODE` `` in a
   document under `docs/` (`tests/test_documented_codes.py`).
6. **Public surface only**: the CLI uses devkit through its public modules (`devkit.core.cli`, `devkit.workflow`,
   `devkit.worktree`, `devkit.advisory`, ...), never private helpers.

## 4. Interfaces & Data Contracts

### 4.1 Entry Points

```toml
# pyproject.toml
[project.entry-points."devkit.bundles"]
spec = "devkit_spec"                 # the spec bundle, deployed by devkit sync (auto_select)

[project.entry-points."devkit.commands"]
spec = "devkit_spec.cli:cli"         # the command group mounted as `devkit spec`
```

`devkit spec --version` prints `[VERSION: devkit-spec <version>]` (the installed distribution's version) and exits
`0`; it is eager, so it works without a subcommand.

### 4.2 Subcommand Catalog

| Command | Capability |
| --- | --- |
| `devkit spec resolve`, `refs`, `list` | `CAP-DOCS-document-lookup` |
| `devkit spec search` | `CAP-DOCS-document-search` |
| `devkit spec entrypoints` | `CAP-TRACE-code-entrypoints` |
| `devkit spec new` | `CAP-DLV-spec-bundles` |
| `devkit spec proposal new\|padr\|handoff\|prune` | `CAP-DLV-proposal-incubation` |
| `devkit spec policy` | `CAP-DLV-project-policy` |
| `devkit spec scope compare\|register\|query\|update\|release\|sweep` | `CAP-COLL-work-scope-registry` |

### 4.3 Shared Options

Every subcommand (through `workspace_option`, `FORMAT_OPTION` and `boundary`):

| Option | Meaning |
| --- | --- |
| `-w/--workspace-root DIR` | Workspace root (default: the devkit project containing the current directory). Paths in output are relative to it. |
| `--format text\|json` | Sentinel lines (default) or one JSON object. |
| `-q/--quiet` | Hide `[NOTICE]` blocks on stderr (or `DEVKIT_QUIET=1`). |
| `-v/--verbose` | Also print `[INFO]` log lines on stderr (or `DEVKIT_VERBOSE=1`). |
| `--strict` | Exit `1` when a warning was reported (or `DEVKIT_STRICT=1`). |

### 4.4 Sentinel Encoding

A sentinel is `[KIND: <positional> key=value ...]`, or `[KIND: key=value ...]` without a positional value. A value
is printed as:

- `-` when it is empty or absent (`None`, `""`);
- `yes` / `no` for a boolean;
- bare when it has no whitespace, `"`, `]` or `=`;
- otherwise a JSON string (`setup="uv sync"`), non-ASCII kept.

### 4.5 Paging

The listing commands `list` and `refs` take `--limit/-n` (default `20`, `0` for all) and `--offset` (default `0`).
After the items they print:

```text
[PAGE: total=57 offset=0 limit=20 count=20 next=20]
[NEXT_CMD: devkit spec list capability --limit 20 --offset 20]
```

`next` is the offset of the following page, `-` on the last page; `[NEXT_CMD: ...]` repeats the command's own
arguments with `--offset <next>` and is printed only when more items follow. A negative `--limit` or `--offset` is
`ARGUMENT_INVALID`. `[NEXT_CMD: devkit workflow next --unit <dir>]` is also the line `devkit spec new`,
`proposal new` and `proposal handoff` print when the unit they created is bound to a workflow.

### 4.6 JSON and Errors

Under `--format json` stdout carries exactly one object: the command's result with its `notices` (each
`notice.to_dict()`), or, when the command fails, `{"error": {...}}` with the warnings and notices reported before it
under `notices`. A command that reports a result and errors together (`resolve` with unresolved IDs, `scope update`,
`scope sweep`) puts the errors under `errors` in its result object instead. In text mode the error block goes to stderr.

### 4.7 Exit Codes

| Code | Meaning |
| --- | --- |
| `0` | Success, including results that carry warnings or notices. |
| `1` | A warning under `--strict` (devkit's negative-result code; no `devkit spec` command reports a negative result otherwise). |
| `2` | The command could not run or refused: every `SPEC_*` error, devkit's `ARGUMENT_INVALID`, and any unexpected exception (`UNEXPECTED_ERROR`, traceback under `-v`). A closed stdout (`BrokenPipeError`) exits `2` without output. |
