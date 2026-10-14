---
id: CAP-COLL-work-scope-registry
title: Work Scope Comparison and Shared Registry
summary: devkit spec scope compares the document and code scope of planned or running parallel tasks and keeps their scopes in a registry and journal shared by all worktrees of a repository; overlapping paths inform scheduling and integration order and never block a write.
area: collaboration
status: active
created_at: 2026-10-13
stories:
  - US-run-parallel-work-safely
entrypoints:
  - src/devkit_spec/scope/
  - src/devkit_spec/cli/scope.py
---

# [CAP-COLL-work-scope-registry] Work Scope Comparison and Shared Registry

## 1. Summary

`devkit spec scope` reports, for each pair of planned or running tasks, how many documents and code paths they both
touch and how much of their scope is still unknown, and keeps each running task's scope in a registry that every
worktree of the repository shares without configuration. The purpose is detection before parallel work runs: the
overlap evidence is an input to the orchestrator's decision of what runs in parallel and in which order work is
integrated. It never grants or blocks a write, and it is not exclusive ownership.

## 2. Scope & Boundary

- **In-Scope**: building scope sets from proposals, spec bundles and Git; pairwise comparison; the local file registry
  (records, owner tokens, locking, deadlines, sweep) and its event journal; the `compare`, `register`, `query`,
  `update`, `release` and `sweep` commands; the registration a handoff performs.
- **Out-of-Scope**:
  - The entrypoint path contract and `_Boundary` parsing: `CAP-TRACE-code-entrypoints`.
  - `[tool.spec.scope]` validation: `CAP-DLV-project-policy`. Document namespaces: `CAP-DOCS-namespaces` (independent
    of the registry namespace).
  - Creating and removing task worktrees: devkit's `devkit worktree`.
- **Non-Goals** (Scope Excluded): exclusive claims and write blocking; heartbeats, automatic expiry and distributed
  recovery; journal retention or rotation; remote adapters and their journals; Windows locking; network file systems
  (where `flock` and rename are not reliable); attributing changes to more than one task in a worktree; semantic
  conflict detection; weighting or ranking pairs. Overlap evidence is a join of declarations and Git observations: it
  proves neither a merge conflict nor independence.

## 3. Business Rules & Policies

1. **Detection, never blocking**: no scope result MAY grant or refuse a write; `overlaps=` above 0 informs
   scheduling and integration order only.
2. **Unknown is not "no overlap"**: an input that cannot become a path MUST be counted as unresolved with its reason,
   never dropped silently.
3. **Declarations are not merged**: when a bundle has both `reconcile.md` and `target-docs.md`, a path only one of
   them names is reported as a `DIFF`; the two lists are never merged.
4. **One token per worktree**: registration returns an opaque owner token once and stores only its SHA-256; a second
   registration from the same worktree MUST be refused (`SPEC_SCOPE_TOKEN_EXISTS`) so the first record is never
   orphaned. The token file is created exclusively: of two registrations racing in one worktree, the one that saves
   its token second is refused the same way, and its record is removed again. A record whose token cannot be saved
   is always removed again; when that removal fails, the original error is reported with the failure as a detail.
5. **Optimistic concurrency**: `update` MUST present the owner token and the revision the caller read; a changed
   record is never overwritten (`SPEC_SCOPE_STALE_REVISION`, nothing written).
6. **Idempotent retries**: an `update` whose `request_id` equals the record's `last_request_id` is answered from the
   stored record before anything is collected, without a second write, with the `added` and `removed` counts that
   request recorded. `release` repeated, or run where nothing is registered, succeeds and changes nothing.
7. **Atomic publication**: every operation holds the namespace lock while it reads, compares and writes; readers never
   see a partial record.
8. **The journal is diagnostic**: it is never an input to an overlap, stale or stage verdict, and a failed append
   never changes an operation's result or exit code (only a `SPEC_SCOPE_JOURNAL_UNAVAILABLE` warning).
9. **Cleanup after finish**: devkit-spec's `devkit.post_finish` extension (`devkit_spec.cleanup.after_finish`) runs in the
   base after `devkit worktree finish` succeeds and removes the records whose worktree is the finished one, at the
   revision it read (`sweep --apply` restricted to those tasks); other stale records stay for an explicit sweep.
   When the removal fails (a malformed `[tool.spec]`, a registry timeout), its error is returned beside the proposal
   prune notices, which devkit reports as a warning, and its fix ends with `devkit spec scope sweep --apply`.
   Nothing is released before the finish, so a refused finish leaves the task registered. Rationale:
   `ADR-cleanup-after-worktree-finish`.
10. **Absolute shared path**: a configured `shared_path` MUST be absolute (a relative path would resolve to a
    different directory in each worktree).

## 4. Interfaces & Data Contracts

### 4.1 Scope Inputs

A scope set has a document side, a code side, observed paths and unresolved inputs. Every path is a literal
workspace-relative path under the entrypoint path contract of `CAP-TRACE-code-entrypoints` (no glob, no absolute
path, no `..`, case-sensitive, `./` and a trailing `/` normalized), with its granularity in the working tree (`file`,
`dir`, or `unknown` when it does not exist), its source and its stage.

| Input | Side | Source | Stage |
| --- | --- | --- | --- |
| Proposal: `targets` of `docs/proposals/PROP-<slug>/target-docs.md` | document | `declared-doc` | `prop` |
| Spec bundle: `targets` of `reconcile.md` (not `waived`); without `reconcile.md`, those of `target-docs.md` | document | `declared-doc` | `spec` (`prop` for `target-docs.md`) |
| `entrypoints` of each capability or story target (also under `docs/packages/<name>/`) | code | `candidate` | as its target |
| `tasks.md` `_Boundary` entries | code | `declared-code` (wins over a candidate of the same path) | `spec` |
| Git in the registering worktree: `<fork point>..HEAD`, staged, unstaged, untracked | code | `observed` | `build` |

`targets` is the same list in both files: `- file: <workspace-relative path>` with an optional `resolution`
(`devkit spec proposal new --with-target-docs` scaffolds `targets: []`). Document IDs are not accepted. Observed paths
are relative to the workspace root and limited to it; a changed path outside the path contract (a glob character or
a colon in its name) is left out. Renames are not detected: a moved file is observed at its old and its new path, so
a task that moves a file overlaps a task editing it at its old path.

The committed range starts at the fork point, `git merge-base <base ref> HEAD`, recomputed on every `register` and
`update`: what a task merges or rebases in from its base branch is not observed, while its own changes, including
conflict resolutions, are. The base ref is the branch the base checkout was on at registration (what
`devkit worktree finish` integrates into). In the base checkout itself, on the base branch, or when the base
checkout is detached, the record has no base ref and the range starts at the fixed base revision. A base ref that no
longer resolves (or shares no history with HEAD) falls back to the base revision and is unresolved
(`missing-base-ref`); the update still applies.

| Unresolved reason | Input |
| --- | --- |
| `planned-doc` | A document target that does not exist yet (it still counts as a document, so two tasks planning the same file overlap). |
| `no-entrypoints` | A capability or story target without `entrypoints`. |
| `not-a-path`, `invalid-path`, `excluded-tree` | A `_Boundary` entry that is `N/A`/`none`, not a literal path, or under `docs/` or `specs/`. |
| `invalid-path` | A document target that is not a literal path. |
| `waived` | A `reconcile.md` target with `resolution: waived`. |
| `no-targets` | A `target-docs.md` without a `targets` key. |
| `missing-target-docs`, `missing-reconcile`, `missing-tasks` | The input file does not exist. |
| `missing-base-revision`, `unknown-base-revision` | The record has no base commit, or Git does not know it. |
| `missing-base-ref` | The record's base branch does not resolve or shares no history with HEAD; the base revision is used instead. |

### 4.2 Comparison

Two sets overlap on a **document** when both declare the same document path, and on **code** when a declared,
candidate or observed path of one equals or contains (by whole segments) one of the other's. A pair reports both
counts, each overlapping path with its granularity and the sources of both sides, and the unresolved count of both
sides. Ranking and weighting are the consumer's.

### 4.3 Registry

- **Location**: the default shared path is `devkit-spec-scope/` in the Git common directory
  (`git rev-parse --git-common-dir`), and the default namespace is the first 16 hex digits of the SHA-256 of that
  directory's absolute path: every worktree of one repository shares them, and cleaning caches never touches them.
  `[tool.spec.scope]` overrides both; to share a registry between clones or hosts, give each the same absolute
  `shared_path` and the same `namespace`. Package documents contribute their workspace-relative targets and
  entrypoints like any other.
- **Record**: `<shared>/<namespace>/<task-id>.json` (the task ID mapped to a file-name-safe form), schema version 1:
  `namespace`, `task_id`, `token_hash`, `revision` (1 on register, +1 per update), `base_revision` (HEAD at
  registration), `base_ref` (the base checkout's branch at registration, `refs/heads/<name>`; empty when there is
  none, 4.1), `worktree` (the absolute workspace root), `hostname`, `shared_worktree`, `spec` (workspace-relative),
  `scopes` (`path`, `kind`, `source`, `stage`, `first_seen`), `unresolved`, `updated_at`, `last_request_id`,
  `last_added` and `last_removed` (the counts of the update `last_request_id` applied; 0 after registration).
- **Token**: saved in the worktree's own Git directory as `devkit-spec-scope-token` (mode 0600), never in the working
  tree or the registry; it is written to a temporary file and linked into place, so it is created exclusively and
  never read half-written.
- **Atomicity**: an exclusive `flock` on `<shared>/<namespace>/.lock`; a record is published by writing a `.tmp-*`
  file in the same directory and renaming it over the record. Temp files an interrupted publish left behind are
  removed at the next lock acquisition, and the OS releases the lock of a process that died.
- **Operations** (`devkit_spec.scope.Registry`; the local file adapter `LocalRegistry` is the only implementation):
  - `register`: creates the record; an existing task ID in the namespace is `SPEC_SCOPE_TASK_EXISTS`. A second record
    for the same worktree and host marks both `shared_worktree` (a `SPEC_SCOPE_SHARED_WORKTREE` warning).
  - `query`: every readable record; unreadable files are reported, never read as records.
  - `update`: requires the owner token and the read revision (`SPEC_SCOPE_TOKEN_MISMATCH`,
    `SPEC_SCOPE_STALE_REVISION`); `first_seen` survives updates; observed paths are replaced on each update,
    declared ones are never removed by an observation.
  - `release`: deletes the record when the token owns it; a missing record is a no-op. A record left alone in the
    worktree the released one shared loses its `shared_worktree` flag.
  - `sweep`: classifies each record: `active`; `stale` (`worktree-missing`: same host, and the worktree path is gone
    or no longer a Git work tree); `unverifiable` (`other-host`); `error` (`parse`, `permission`). With `--apply` a
    stale record is removed (`removed`, `worktree-missing`) only if its revision still equals the one read before,
    else `error` with `stale-revision`.
  - `claim`: reserved for adapters that can publish exclusively; `SPEC_SCOPE_UNSUPPORTED`.
- **Deadline**: each command runs under `[tool.spec.scope] timeout` (default 10 seconds): the lock wait and every Git
  subprocess take the time left, and a Git process that outlives it is killed. Running out is `SPEC_SCOPE_TIMEOUT`
  (`[SCOPE_ACK: status=timeout]` for an update); retry an update whose outcome was not seen with `--request-id`.
- **Journal**: each namespace keeps an append-only `journal.jsonl`, one JSON event per line, appended under the
  namespace lock with its own 5-second deadline, so an operation that timed out is still recorded. An event has `at`
  (RFC 3339 UTC), `event` (`register`, `update`, `release`, `sweep`), `task`, `slug` (from a spec directory named
  `YYYYMMDD-<slug>`), `revision`, `request_id`, `status` (every update attempt, applied or not), `added`, `removed`,
  `overlaps`, `unresolved` (applied updates only), `verdict` and `reason` (sweep verdicts other than `active`),
  `worktree`, `spec`, and `source` (`handoff` when `devkit spec proposal handoff` registered); empty values are left
  out. Deleting records never deletes the journal; it has no retention or rotation. An unfinished last line (an
  interrupted append) is terminated before the next append.

### 4.4 Commands

Every command takes `-w/--workspace-root`, `--format text|json`, `-q`, `-v` and `--strict`; text output is one
sentinel per line, warnings follow on stderr, and JSON is one object with the same data and its `notices`.

| Command | Does |
| --- | --- |
| `devkit spec scope compare (--proposal <slug> \| --spec <dir>)...` | Compares two or more declared scopes pairwise without the registry or Git. |
| `devkit spec scope register --spec <dir> [--task-id <id>]` | Registers this worktree's task (task ID default: the spec ID) and prints its token once. |
| `devkit spec scope query [--spec <dir>]` | Lists the namespace's records and this worktree's overlaps with the others (every pair when this worktree registered nothing). `--spec` compares that bundle's declared scope with every record not owned here, for a task about to start. |
| `devkit spec scope query --history [--task <id>]` | Prints the journal in time order; `--task` keeps events whose task ID or slug matches. |
| `devkit spec scope update --spec <dir> [--request-id <id>]` | Recollects the declared and observed scope, writes it, prints the overlaps and the ACK. |
| `devkit spec scope release [--task-id <id>]` | Removes this worktree's record and token. With `--task-id`, a token is required and must own that record; a token whose record is already gone is removed. |
| `devkit spec scope sweep [--apply] [--expect <task>=<rev>]...` | Reports stale, unverifiable and unreadable records; `--apply` removes stale ones whose revision is unchanged (without `--expect`, the revisions this command read first). |

Argument errors (`ARGUMENT_INVALID`): `register`/`update` without `--spec`, `compare` with fewer than two inputs,
`--task` without `--history`, `--spec` with `--history`, `--expect` without `--apply`, or an `--expect` that is not
`<task-id>=<revision>`.

### 4.5 Output

```text
[PAIR: a=SPEC-a b=SPEC-b docs=1 code=2 unresolved=3]
[EVIDENCE: docs/capabilities/x/CAP-X-a.md a=SPEC-a b=SPEC-b kind=doc granularity=file]
[EVIDENCE: src/a a=SPEC-a b=SPEC-b kind=code granularity=dir other=src/a/a.py source=declared-code other_source=observed]
[DIFF: docs/capabilities/x/CAP-X-c.md set=SPEC-a in=target-docs]                        # compare
[UNRESOLVED: docs/capabilities/x/CAP-X-new.md set=SPEC-a reason=planned-doc]            # compare
[SUMMARY: sets=2 pairs=1 overlapping=1]                                                  # compare
[SCOPE: SPEC-a namespace=3f2a... revision=1 scopes=6 unresolved=2 shared_path=/repo/.git/devkit-spec-scope token=...]  # register
[RECORD: SPEC-b revision=3 worktree=/repo-wt-b host=h spec=specs/... scopes=7 unresolved=1 shared_worktree=no own=no]  # query
[SUMMARY: namespace=3f2a... records=2 pairs=1 overlapping=1 problems=0]                  # query
[EVENT: update at=2026-10-13T08:00:00.000000Z task=SPEC-a slug=a revision=2 request_id=... status=applied added=1 removed=0 overlaps=1 unresolved=2 ...]
[SUMMARY: namespace=3f2a... events=4 problems=0]                                         # query --history
[SCOPE_ACK: status=applied revision=2 added=1 removed=0 overlaps=1 unresolved=2 request_id=...]  # update
[SCOPE: SPEC-a released=yes registered=yes already=no revision=2]                        # release
[SWEEP: SPEC-b verdict=stale reason=worktree-missing revision=3]                         # sweep
[SUMMARY: namespace=3f2a... active=1 stale=1 unverifiable=0 error=0 removed=0]           # sweep
```

- `[PAIR]` lines are followed by their `[EVIDENCE]` lines; `[DIFF]` carries `in=target-docs|reconcile`.
- `register` is the only place the owner token is ever printed; `query` records never carry the token hash.
- `overlaps` in the ACK is the number of other records this task overlaps. An update that does not apply prints its
  `[SCOPE_ACK: status=failed|stale|timeout ...]`, then its error (`SPEC_SCOPE_TOKEN_MISSING`,
  `SPEC_SCOPE_STALE_REVISION`, `SPEC_SCOPE_TIMEOUT`, ...), exiting 2; JSON carries the ACK and the error under
  `errors`.
- `sweep` verdicts are `active`, `stale`, `unverifiable`, `error` and `removed`. `sweep --apply` that kept a record
  because its revision moved prints its verdicts, then `SPEC_SCOPE_STALE_REVISION`.

JSON shapes: `compare` `{sets, pairs, summary}`; `register` `{record, token, namespace, shared_path, notices}`;
`query` `{own, records, pairs, summary, notices}`; `query --history` `{events, summary, notices}`; `update`
`{ack, pairs, notices[, errors]}`; `release` `{task, released, registered, already, revision, notices}`; `sweep`
`{results, summary, notices[, errors]}`.

### 4.6 Where the Workflow Calls It

devkit's `workflow next` and `worktree finish` know nothing of devkit-spec, so the bundle's skills call the commands
(the `spec` skill's `references/worktree.md`):

- `devkit spec proposal handoff` run inside a linked worktree with `[tool.spec] worktree = true` registers the new
  bundle itself (journal `source=handoff`) and prints the `[SCOPE: ...]` line with the token; a registration failure
  is a `SPEC_SCOPE_REGISTER_FAILED` warning and the handoff stays done. Outside Git, in the base checkout or with
  `worktree = false` nothing is registered. After `devkit spec new` in a task worktree, the skill runs
  `devkit spec scope register --spec <dir>`.
- `spec-tasks` after writing `tasks.md`, and `spec-sync` after writing `reconcile.md`, run
  `devkit spec scope update --spec <dir>` in a registered worktree; `SPEC_SCOPE_TOKEN_MISSING` means the worktree
  takes no part and the step is skipped.
- After `devkit worktree finish` succeeds, its post-finish extension removes the record of the removed worktree (item 9).
  `devkit spec scope sweep --apply` removes other stale records; `devkit spec scope release -w <worktree>` withdraws
  an abandoned task.

### 4.7 Configuration

```toml
[tool.spec.scope]
shared_path = "/srv/devkit-scope"   # absolute, or starting with ~; default: devkit-spec-scope/ in the Git common dir
namespace = "team"                  # letters, digits, '.', '_', '-', not starting with '.'; default: the common-dir hash
timeout = 10                        # whole seconds per command, 1 to 300
```

A malformed table is `SPEC_CONFIG_INVALID` (`CAP-DLV-project-policy`).

### 4.8 Codes

| Code | Level | Class | Condition |
| --- | --- | --- | --- |
| `SPEC_SCOPE_NOT_A_WORKTREE` | `ERROR` (`INPUT_ERROR`) | `ScopeNotAWorktreeError` | The workspace is not inside a Git work tree. |
| `SPEC_SCOPE_SPEC_NOT_FOUND` | `ERROR` (`INPUT_ERROR`) | `ScopeSpecNotFoundError` | `--spec` names no directory. |
| `SPEC_SCOPE_INPUT_INVALID` | `ERROR` (`MAINTENANCE`) | `ScopeInputInvalidError` | `tasks.md`, `reconcile.md` or `target-docs.md` cannot be read, or its `targets` is not a list of mappings with a string `file`. |
| `SPEC_SCOPE_TOKEN_MISSING` | `ERROR` (`INPUT_ERROR`) | `ScopeTokenMissingError` | This worktree registered nothing (update, release `--task-id`). |
| `SPEC_SCOPE_TOKEN_EXISTS` | `ERROR` (`INPUT_ERROR`) | `ScopeTokenExistsError` | This worktree already registered a task, or a concurrent registration in it saved its token first. |
| `SPEC_SCOPE_TASK_EXISTS` | `ERROR` (`INPUT_ERROR`) | `ScopeTaskExistsError` | Another record has the task ID. |
| `SPEC_SCOPE_RECORD_MISSING` | `ERROR` (`INPUT_ERROR`) | `ScopeRecordMissingError` | The token's record was released or swept; `release` removes the orphaned token. |
| `SPEC_SCOPE_TOKEN_MISMATCH` | `ERROR` (`BLOCKED`) | `ScopeTokenMismatchError` | The token does not own the record. |
| `SPEC_SCOPE_STALE_REVISION` | `ERROR` (`AUTO`) | `ScopeStaleRevisionError` | The record changed between read and write; nothing was written. |
| `SPEC_SCOPE_TIMEOUT` | `ERROR` (`DEFER`) | `ScopeTimeoutError` | The lock or Git outlasted `timeout`. |
| `SPEC_SCOPE_LOCK_UNSUPPORTED` | `ERROR` (`BLOCKED`) | `ScopeLockUnsupportedError` | No `fcntl.flock` on this platform. |
| `SPEC_SCOPE_NAMESPACE_INVALID` | `ERROR` (`INPUT_ERROR`) | `ScopeNamespaceError` | An adapter call names an empty, dotted or nested namespace. |
| `SPEC_SCOPE_SHARED_PATH_UNAVAILABLE` | `ERROR` (`INTERACTION`) | `ScopeSharedPathError` | The registry directory (or the token file) cannot be created, read or written. |
| `SPEC_SCOPE_UNSUPPORTED` | `ERROR` (`MAINTENANCE`) | `ScopeUnsupportedError` | The reserved `claim` operation was called. |
| `SPEC_SCOPE_ACK_FAILED` | `ERROR` (`MAINTENANCE`) | `ScopeAckFailedError` | An update failed for a cause without its own code. |
| `SPEC_SCOPE_RECORD_INVALID` | `WARNING` | `ScopeRecordInvalidWarning` | A record file cannot be read (an `ERROR` when it is this worktree's record during update or release). |
| `SPEC_SCOPE_SHARED_WORKTREE` | `WARNING` | `ScopeSharedWorktreeWarning` | Another task registered the same worktree. |
| `SPEC_SCOPE_JOURNAL_UNAVAILABLE` | `WARNING` | `ScopeJournalWarning` | The journal could not be written. |
| `SPEC_SCOPE_JOURNAL_LINE_INVALID` | `WARNING` | `ScopeJournalLineWarning` | `query --history` skipped lines that are not JSON events. |
| `SPEC_SCOPE_REGISTER_FAILED` | `WARNING` | `ScopeRegisterFailedWarning` | A handoff in a task worktree could not register its bundle. |

devkit's own errors pass through: `ARGUMENT_INVALID` (4.4), `GIT_FAILED`, `SPEC_PROPOSAL_NOT_FOUND` (compare),
`SPEC_CONFIG_INVALID`.
