---
id: ARCH-08-cross-cutting
title: Cross-cutting Concepts
summary: Cross-cutting conventions of all devkit-spec commands and modules, namely the agent-first output contract, SPEC_ error codes, configuration in .devkit/config.toml, rule targeting and Git snapshot runs, devkit's public surface, the path contract, language and platform support.
status: active
created_at: 2026-10-13
---

# [ARCH-08-cross-cutting] Cross-cutting Concepts

- **arc42**: §8 Cross-cutting Concepts
- devkit's specifications this document applies: [Agent-First Output](https://github.com/mjkimR/devkit/blob/main/docs/architecture/agent-output.md),
  [Agent Advisory Protocol](https://github.com/mjkimR/devkit/blob/main/docs/advisory/protocol.md),
  [Command Plugins](https://github.com/mjkimR/devkit/blob/main/docs/architecture/command-plugins.md).

---

## 1. Agent-First Output

An AI coding agent is the primary consumer of every command; people read the same output. Every `devkit spec`
command:

- MUST print its result on stdout as one-line `[KIND: <value> key=value ...]` sentinels, or exactly one JSON object
  under `--format json`. A value is `-` when empty, `yes`/`no` for a boolean, bare when it holds no space, quote or
  bracket, else a JSON string (`devkit_spec.cli.output`). No colour, tables or progress output.
- MUST print advisories (`[ERROR]`, `[WARN]`, `[NOTICE]` blocks of the Agent Advisory Protocol) on stderr, after the
  result; `[INFO]` diagnostics appear only under devkit's `-v`.
- MUST exit `0` on success, `1` for a negative result, `2` when it could not run. Warnings and notices do not change
  the exit code.
- MUST end a paged listing with `[PAGE: total= offset= limit= count= next=]` and, when more items follow,
  `[NEXT_CMD: devkit spec ... --offset <n>]`; a command that hands over to a next step prints the exact command as
  `[NEXT_CMD: ...]` (`CAP-HARN-command-mount`).
- MUST return warnings and notices of a successful operation under `notices` in JSON and as advisory blocks in text,
  never raise them.

Libraries never print: modules below `cli` return results and notices or raise `AdvisoryError` subclasses, and
`cli` renders them through `devkit.core.cli` (`boundary`, `FORMAT_OPTION`, `workspace_option`, `echo_json`,
`echo_notices`, `exit_on_warnings`, `exit_on_problems`).

---

## 2. Advisory Codes

- Every devkit-spec failure, warning and notice is an `AdvisoryError` subclass in `devkit_spec.errors` with a stable
  `SPEC_`-prefixed `UPPER_SNAKE` code, a level and the protocol fields (actor, retry, `[ACTION]` directive) that fit its
  condition. Callers branch on `error.code`, never on message text.
- devkit's own codes pass through unchanged (`ARGUMENT_INVALID`, `CONFIG_INVALID`, `FRONTMATTER_INVALID`,
  `GIT_FAILED`, `SEARCH_EXTRA_MISSING`, ...); devkit-spec never reuses a devkit code for another condition.
- Each code is documented with its level and condition in the capability that owns it; `tests/test_documented_codes.py`
  fails when a code defined under `src/` does not appear as `` `CODE` `` under `docs/`.

| Code family | Owner |
| :--- | :--- |
| `SPEC_DOCUMENT_INVALID`, `SPEC_ID_UNRESOLVED`, `SPEC_ID_DUPLICATE` | `CAP-DOCS-document-model`, `CAP-DOCS-document-lookup` |
| `SPEC_GLOSSARY_INVALID` | `CAP-DOCS-document-search` |
| `SPEC_CONFIG_INVALID` | `CAP-DLV-project-policy` |
| `SPEC_PROPOSAL_*` | `CAP-DLV-proposal-incubation` |
| `SPEC_SLUG_INVALID`, `SPEC_EXISTS`, `SPEC_WORKFLOW_INVALID`, `SPEC_WRITE_FAILED`, `SPEC_UNBOUND` | `CAP-DLV-spec-bundles` |
| `SPEC_ENTRYPOINTS_*` | `CAP-TRACE-code-entrypoints` |
| `SPEC_SCOPE_*` | `CAP-COLL-work-scope-registry` |

---

## 3. Configuration

- Project policy lives in `.devkit/config.toml`. What devkit models stays in devkit's tables (`[presets]`,
  `[workflow.approvals]`, `[workflow.stages]`, `[worktree]`, `[rules]`); devkit-spec owns only `[tool.spec]`, which
  devkit passes through unread (`ADR-policy-in-the-tool-spec-table`):

  | Key | Meaning |
  | :--- | :--- |
  | `[tool.spec] worktree` | `required`: Route 2 and above always run in a task worktree; `auto` (default): when the task needs one (`ADR-worktree-and-pull-request-levels`) |
  | `[[tool.spec.namespaces]]` (`name`, `path`) | Monorepo packages with their own Living Spec under `docs/packages/<name>/` (`CAP-DOCS-namespaces`) |
  | `[tool.spec.scope]` (`shared_path`, `namespace`, `timeout`) | The work-scope registry (`CAP-COLL-work-scope-registry`) |

- `devkit config template` writes these tables into the file as comments at their defaults, from
  `devkit_spec.config.template` (the `devkit.config_template` entry point `spec`), so a project sees every key
  without reading this documentation.
- Agents read the effective policy with `devkit spec policy`, never by parsing the file (`CAP-DLV-project-policy`).
- A malformed `[tool.spec]` is `SPEC_CONFIG_INVALID`. In a rule run it is not a violation: it fails the run
  (`SPEC_CONFIG_INVALID` with the rule's ID, exit `2`), because no document can be checked against a registry that cannot
  be read.
- `docs/glossary.yaml` is the project-owned synonym list of `devkit spec search` (`CAP-DOCS-document-search`).

---

## 4. Documents Are Read Afresh

The document index (`devkit_spec.documents.DocumentIndex`) is rebuilt from the files under `docs/` and `specs/` on
every load; there is no cache to go stale. Within one rule run a parsed document is reused while its text is
unchanged. A file that cannot be read or parsed is left out with a `SPEC_DOCUMENT_INVALID` warning, so one broken file
never hides the others. IDs and references are repository-wide; namespaces narrow browsing only (`CAP-DOCS-namespaces`).

---

## 5. Rule Targeting and Snapshot Runs

The spec rules follow devkit's rule engine contract (`CAP-GOV-spec-rules`):

- **Reads through the run's cache.** Rules read files only through `ctx.cache` (`document_index(ctx)`), so a Git
  snapshot run (`check --staged`, `check --ci`) evaluates exactly the staged or CI tree, and a fix is seen by the
  recheck.
- **Targeting.** A violation is reported for a file only when `ctx.is_file_targeted` accepts it (the run's targets and
  `[rules] exclude`). Rules spanning several files (`RULE-spec-lifecycle`, `RULE-task-coverage`,
  `RULE-traceability-link`) report on a targeted member of the relationship.
- **History.** Files of a completed spec bundle are work history: checked only when named as explicit targets
  (`RULE-spec-lifecycle` excepted, whose subject is the completed status).
- **Snapshot evidence.** `ctx.snapshot` (changed and deleted paths, base, mode) is set in snapshot runs only.
  `RULE-reconcile-contract` uses it to require the evidence of a resolved record in the diff, `RULE-code-entrypoints`
  to report documents declaring a path the diff deletes.
- **Policy from the snapshot.** In a snapshot run devkit reads `.devkit/config.toml`, the receipt and the rule files
  from the snapshot, so policy takes effect in the gate once committed.

---

## 6. devkit Public Surface

- devkit-spec imports only each devkit module's exports (`devkit.core`, `devkit.core.frontmatter`, `devkit.core.cli`,
  `devkit.core.errors`, `devkit.advisory`, `devkit.rules`, `devkit.workflow`, `devkit.worktree`, `devkit.search`),
  never private helpers, and never copies them.
- A capability that is not specific to spec-driven development is added to devkit first, then used here. The
  SDD-agnostic building blocks come from devkit: Git calls (`run_git`), deadlines (`Deadline`, with a devkit-spec
  error factory where a `SPEC_` code applies), file locks (`file_lock`), atomic writes (`atomic_write_text`),
  empty-tree removal (`remove_empty_tree`), Markdown links (`extract_links`) and link relocation (`relocate_links`).
- devkit is pinned to a minor range (`devkit>=0.1,<0.2`). While neither package has external consumers, breaking
  changes to the bundle, the commands and the APIs are made in place, without migrations or deprecation shims.

---

## 7. Paths and Writes

- Every path a command reads from documents (entrypoints, `_Boundary` entries, `reconcile.md` and `target-docs.md`
  targets, scope paths) is a literal workspace-relative path under the entrypoint path contract: no glob, no absolute
  path, no `..`, no backslash or colon; `./` and a trailing `/` normalized; compared by whole segments,
  case-sensitively (`CAP-TRACE-code-entrypoints`).
- Writers validate before the first write and undo partial writes on a file system failure (`devkit spec new`,
  `devkit spec proposal handoff`). Rewrites change only what was parsed (a reference's offsets, the `entrypoints`
  block), leaving every other byte as it was.
- Nothing is deleted beyond what the command owns: handoff removes the handed-off proposal, `proposal prune` removes
  only directories that hold no file, `scope sweep --apply` removes only stale records whose revision is unchanged,
  and `scope release` keeps the worktree's token while an unreadable record file may still be its record.

---

## 8. Language

- Documentation, bundle assets, skill text, generated text and `summary` fields are English. A `summary` must contain
  no letter outside the Latin script, because dense search embeds it (`RULE-document-summary`).
- Titles and bodies of a project's own documents may use any language; they are ranked lexically.

---

## 9. Platform Support

- Python 3.12 or later; macOS and Linux. Windows is not supported: the scope registry needs `fcntl.flock`
  (`SPEC_SCOPE_LOCK_UNSUPPORTED` otherwise).
- The registry on a network file system is not supported: `flock` and rename atomicity are not guaranteed there.
