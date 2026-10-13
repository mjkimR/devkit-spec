# Work Scope Comparison and Shared Registry

`devkit spec scope` reports, for each pair of planned or running tasks, how many documents and code paths they both
touch and how much of their scope is still unknown, and keeps each running task's scope in a registry that every
worktree of the repository shares without configuration. The purpose is detection before parallel work runs: the
overlap evidence is an input to the orchestrator's decision of what runs in parallel and in which order work is
integrated. It never grants or blocks a write, and it is not exclusive ownership.

Ported from specrig's `scope` command (`CAP-HARN-shared-work-scope-registry`, `ADR-scope-registry-contracts`,
`SPEC-scope-event-journal`); the differences are listed in [section 8](#8-differences-from-specrig).

## 1. Scope Inputs

A scope set has a document side, a code side, observed paths and unresolved inputs. Every path is a literal
workspace-relative path under the [entrypoint path contract](entrypoints.md#1-path-contract) (no glob, no
absolute path, no `..`, case-sensitive, `./` and a trailing `/` normalized), with its granularity in the working tree
(`file`, `dir`, or `unknown` when it does not exist), its source and its stage.

| Input | Side | Source | Stage |
| --- | --- | --- | --- |
| Proposal: `targets` of `docs/proposals/PROP-<slug>/target-docs.md` | document | `declared-doc` | `prop` |
| Spec bundle: `targets` of `reconcile.md` (not `waived`); without `reconcile.md`, those of `target-docs.md` | document | `declared-doc` | `spec` (`prop` for `target-docs.md`) |
| `entrypoints` of each capability or story target (also under `docs/packages/<name>/`) | code | `candidate` | as its target |
| `tasks.md` `_Boundary` entries | code | `declared-code` (wins over a candidate of the same path) | `spec` |
| Git in the registering worktree: `<base revision>..HEAD`, staged, unstaged, untracked | code | `observed` | `build` |

`targets` is the same list in both files: `- file: <workspace-relative path>` with an optional `resolution`
(`devkit spec proposal new` scaffolds `target-docs.md` with an empty `targets: []`). Document IDs are not accepted.
When a bundle has both files, a path only one of them names is reported as a `DIFF` line; the two are never merged.
Observed paths are relative to the workspace root and limited to it; a changed path outside the path contract (a
glob character or a colon in its name) is left out.

What cannot become a path is **unresolved** and counted, never read as "no overlap":

| Reason | Input |
| --- | --- |
| `planned-doc` | a document target that does not exist yet (it still counts as a document, so two tasks planning the same file overlap) |
| `no-entrypoints` | a capability or story target without `entrypoints` |
| `not-a-path`, `invalid-path`, `excluded-tree` | a `_Boundary` entry that is `N/A`/`none`, not a literal path, or under `docs/` or `specs/` |
| `invalid-path` | a document target that is not a literal path |
| `waived` | a `reconcile.md` target with `resolution: waived` |
| `no-targets` | a `target-docs.md` without a `targets` key |
| `missing-target-docs`, `missing-reconcile`, `missing-tasks` | the input file does not exist |
| `missing-base-revision`, `unknown-base-revision` | the record has no base commit, or Git does not know it |

## 2. Comparison

Two sets overlap on a **document** when both declare the same document path, and on **code** when a declared,
candidate or observed path of one equals or contains (by whole segments) one of the other's. A pair reports both
counts, each overlapping path with its granularity and the sources of both sides, and the unresolved count of both
sides. Ranking and weighting are the consumer's; the overlap is a join of declarations, so it proves neither a merge
conflict nor semantic independence.

## 3. Registry

**Location.** The default shared path is `devkit-spec-scope/` in the Git common directory
(`git rev-parse --git-common-dir`), and the default namespace is the first 16 hex digits of the SHA-256 of that
directory's absolute path: every worktree of one repository shares them, and cleaning caches never touches them.
`[tool.spec.scope]` overrides both (section 6); to share a registry between clones or hosts, give each the same
absolute `shared_path` and the same `namespace`. Document namespaces (`[[tool.spec.namespaces]]`) are independent of
the registry namespace: package documents contribute their workspace-relative targets and entrypoints like any other.

**Record.** `<shared>/<namespace>/<task-id>.json` (the task ID mapped to a file-name-safe form), schema version 1:
`namespace`, `task_id`, `token_hash`, `revision` (1 on register, +1 per update), `base_revision` (HEAD at
registration), `worktree` (the absolute workspace root), `hostname`, `shared_worktree`, `spec` (workspace-relative),
`scopes` (`path`, `kind`, `source`, `stage`, `first_seen`), `unresolved`, `updated_at`, `last_request_id`.

**Token.** Registration returns an opaque owner token once; the record stores only its SHA-256. The token is saved
in the worktree's own Git directory as `devkit-spec-scope-token` (mode 0600), one per worktree: a second
registration from the same worktree is refused (`SPEC_SCOPE_TOKEN_EXISTS`) so the first record is never orphaned.

**Atomicity.** Every operation holds an exclusive `flock` on `<shared>/<namespace>/.lock` while it reads, compares
and writes; a record is published by writing a `.tmp-*` file in the same directory and renaming it over the record,
so no reader ever sees a partial record. Temp files an interrupted publish left behind are removed at the next lock
acquisition, and the OS releases the lock of a process that died.

**Operations** (`devkit_spec.scope.Registry`; the local file adapter is the only implementation):

- `register`: creates the record; an existing task ID in the namespace is `SPEC_SCOPE_TASK_EXISTS`. A second record
  for the same worktree and host marks both `shared_worktree` (a `SPEC_SCOPE_SHARED_WORKTREE` warning).
- `query`: every readable record; unreadable files are reported, never read as records.
- `update`: requires the owner token and the revision the caller read (`SPEC_SCOPE_TOKEN_MISMATCH`,
  `SPEC_SCOPE_STALE_REVISION`). A `request_id` equal to the record's `last_request_id` is answered from the stored
  record without a second write. `first_seen` survives updates; observed paths are replaced on each update, declared
  ones are never removed by an observation.
- `release`: deletes the record when the token owns it; a missing record is a no-op.
- `sweep`: classifies each record: `active`; `stale` (`worktree-missing`: same host, and the worktree path is gone or
  no longer a Git work tree); `unverifiable` (`other-host`); `error` (`parse`, `permission`). With `--apply` a stale
  record is removed only if its revision still equals the one read before (else `error` with `stale-revision`).
- `claim`: reserved for adapters that can publish exclusively; `SPEC_SCOPE_UNSUPPORTED`.

**Deadline.** Each command runs under `[tool.spec.scope] timeout` (default 10 seconds): the lock wait and every Git
subprocess take the time left, and a Git process that outlives it is killed. Running out is `SPEC_SCOPE_TIMEOUT`
(`[SCOPE_ACK: status=timeout]` for an update); retry an update whose outcome was not seen with `--request-id`.

**Journal.** Each namespace keeps an append-only `journal.jsonl`: one JSON event per line, appended under the
namespace lock with its own 5-second deadline, so an operation that timed out is still recorded. An event has `at`
(RFC 3339 UTC), `event` (`register`, `update`, `release`, `sweep`), `task`, `slug` (from a spec directory named
`YYYYMMDD-<slug>`), `revision`, `request_id`, `status` (every update attempt, applied or not), `added`, `removed`,
`overlaps`, `unresolved` (applied updates only), `verdict` and `reason` (sweep verdicts other than `active`),
`worktree`, `spec`, and `source` (`handoff` when `devkit spec proposal handoff` registered); empty values are left
out. Deleting records never deletes the journal; it has no retention or rotation. It is a diagnostic history, never
an input to an overlap, stale or stage verdict, and a failed append only adds a `SPEC_SCOPE_JOURNAL_UNAVAILABLE`
warning: the operation's result and exit code stay as they are. An unfinished last line (an interrupted append) is
terminated before the next append.

## 4. Commands

Every command takes `-w/--workspace-root` and `--format text|json`; text output is one sentinel per line, warnings
follow on stderr, and JSON is one object with the same data and its `notices`.

| Command | Does |
| --- | --- |
| `devkit spec scope compare (--proposal <slug> \| --spec <dir>)...` | Compares two or more declared scopes pairwise without the registry or Git. |
| `devkit spec scope register --spec <dir> [--task-id <id>]` | Registers this worktree's task (task ID default: the spec ID) and prints its token once. |
| `devkit spec scope query [--spec <dir>]` | Lists the namespace's records and this worktree's overlaps with the others (every pair when this worktree registered nothing). `--spec` compares that bundle's declared scope with every record not owned here, for a task about to start. |
| `devkit spec scope query --history [--task <id>]` | Prints the journal in time order; `--task` keeps events whose task ID or slug matches. |
| `devkit spec scope update --spec <dir> [--request-id <id>]` | Recollects the declared and observed scope, writes it, prints the overlaps and the ACK. |
| `devkit spec scope release [--task-id <id>]` | Removes this worktree's record and token. Repeating it, or running it where nothing is registered, succeeds and changes nothing. |
| `devkit spec scope sweep [--apply] [--expect <task>=<rev>]...` | Reports stale, unverifiable and unreadable records; `--apply` removes stale ones whose revision is unchanged. |

Text output:

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

`overlaps` in the ACK is the number of other records this task overlaps. An update that does not apply prints its
`[SCOPE_ACK: status=failed|stale|timeout ...]` and then its error (`SPEC_SCOPE_TOKEN_MISSING`,
`SPEC_SCOPE_STALE_REVISION`, `SPEC_SCOPE_TIMEOUT`, ...), exiting 2; JSON carries the ACK and the error under
`errors`. `sweep --apply` that kept a record because its revision moved prints its verdicts, then
`SPEC_SCOPE_STALE_REVISION`. JSON shapes: `compare` `{sets, pairs, summary}`; `register`
`{record, token, namespace, shared_path, notices}`; `query` `{own, records, pairs, summary, notices}` (records never
carry the token hash); `query --history` `{events, summary, notices}`; `update` `{ack, pairs, notices[, errors]}`;
`release` `{task, released, registered, already, revision, notices}`; `sweep` `{results, summary, notices[, errors]}`.

## 5. Where the Workflow Calls It

devkit's `workflow next` and `worktree finish` know nothing of devkit-spec, so the bundle's skills call the commands
(`spec` skill, `references/worktree.md`):

- `devkit spec proposal handoff` run inside a linked worktree with `[tool.spec] worktree = true` registers the new
  bundle itself and prints the `[SCOPE: ...]` line with the token; a registration failure is a
  `SPEC_SCOPE_REGISTER_FAILED` warning and the handoff stays done. After `devkit spec new` in a task worktree, the
  skill runs `devkit spec scope register --spec <dir>`.
- `spec-tasks` after writing `tasks.md`, and `spec-sync` after writing `reconcile.md`, run
  `devkit spec scope update --spec <dir>` in a registered worktree; `SPEC_SCOPE_TOKEN_MISSING` means the worktree
  takes no part and the step is skipped.
- After `devkit worktree finish` succeeds, `devkit spec scope sweep --apply` in the base removes the record of the
  removed worktree (now stale); finishing first keeps a task registered when finish refuses. `devkit spec scope
  release -w <worktree>` withdraws an abandoned task.

## 6. Configuration

```toml
[tool.spec.scope]
shared_path = "/srv/devkit-scope"   # absolute, or starting with ~; default: devkit-spec-scope/ in the Git common dir
namespace = "team"                  # letters, digits, '.', '_', '-', not starting with '.'; default: the common-dir hash
timeout = 10                        # whole seconds per command, 1 to 300
```

A malformed table is `SPEC_CONFIG_INVALID` ([Project policy](policy.md)).

## 7. Codes

| Code | Level | Class | Condition |
| --- | --- | --- | --- |
| `SPEC_SCOPE_NOT_A_WORKTREE` | `ERROR` (`INPUT_ERROR`) | `ScopeNotAWorktreeError` | The workspace is not inside a Git work tree. |
| `SPEC_SCOPE_SPEC_NOT_FOUND` | `ERROR` (`INPUT_ERROR`) | `ScopeSpecNotFoundError` | `--spec` names no directory. |
| `SPEC_SCOPE_INPUT_INVALID` | `ERROR` (`MAINTENANCE`) | `ScopeInputInvalidError` | `tasks.md`, `reconcile.md` or `target-docs.md` cannot be read, or its `targets` is not a list of mappings with a string `file`. |
| `SPEC_SCOPE_TOKEN_MISSING` | `ERROR` (`INPUT_ERROR`) | `ScopeTokenMissingError` | This worktree registered nothing (update, release `--task-id`). |
| `SPEC_SCOPE_TOKEN_EXISTS` | `ERROR` (`INPUT_ERROR`) | `ScopeTokenExistsError` | This worktree already registered a task. |
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

devkit's own errors pass through: `ARGUMENT_INVALID` (missing `--spec`, fewer than two compare inputs, `--task`
without `--history`, `--expect` without `--apply` or malformed), `GIT_FAILED`, `SPEC_PROPOSAL_NOT_FOUND` (compare),
`SPEC_CONFIG_INVALID`.

## 8. Differences from specrig

- devkit's `workflow next` has no `--scope-ack` and `devkit worktree finish` cannot call devkit-spec: the skills run
  `update`, `release` and `sweep` instead, and `finish` no longer releases after its merge check or sweeps after
  removal. Worktree guard refusals (`WORKTREE_*`) are not journaled, so the `guard` event and the `worktree-start`,
  `worktree-finish` and `workflow-next` sources do not occur.
- Output follows devkit's sentinels (`[PAIR: ...]`, `[EVIDENCE: ...]`, `[RECORD: ...]`, `[EVENT: ...]`,
  `[SWEEP: ...]`) instead of specrig's `kv` lines; `query --history --format json` is an object with `events`, not a
  bare array; journal, record and shared-worktree problems are advisory warnings instead of `warning ...` and
  `problem ...` lines.
- `release` without a token succeeds as a no-op (specrig: `SCOPE_TOKEN_MISSING`), so the finish step needs no
  condition; with `--task-id` naming no record it keeps the token unless the token's own record is gone too.
- `query --spec <dir>` compares a bundle's declared scope with the registered tasks (specrig accepted and ignored it).
- `shared_path` must be absolute: a relative path would resolve to a different directory in each worktree.
- A `target-docs.md` without `targets` is unresolved (`no-targets`), and the scaffold writes `targets: []`.
- `--expect` without `--apply` is an argument error instead of being ignored.
- Option and input errors use devkit's `ARGUMENT_INVALID` and the `SPEC_SCOPE_*` codes above; specrig's
  `INVALID_SCOPE_OPTION`, `INVALID_SCOPE_INPUT`, `SCOPE_INPUT_MISSING`, `SPEC_REQUIRED` and `SPEC_NOT_FOUND` are gone.

## 9. Limitations

Exclusive claims and write blocking, heartbeats, automatic expiry and distributed recovery, journal retention or
rotation, remote adapters (and their journals), Windows locking, network file systems (where `flock` and rename are
not reliable), attributing changes to more than one task in a worktree, semantic conflict detection, and weighting or
ranking pairs are out of scope. Overlap evidence is a join of declarations and Git observations: it proves neither a
merge conflict nor independence.
