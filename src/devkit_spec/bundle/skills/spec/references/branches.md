# Activity branches: start, continue, leftovers and stale branches

Read this when you start an activity's branch without a worktree, continue a branch that already exists, or report leftover and stale branches in `/spec-next`. Starting and finishing a worktree is [worktree](worktree.md).

## 1. Names

Every `spec` and `proposal` activity runs on its own branch, whatever the mode: `plan-<slug>` for a proposal's Planning, `dev-<slug>` for Development (`<slug>` the proposal or spec slug). A `session` task bound for a PR uses `dev-<slug>`. The full branch name is what every `devkit worktree` command takes; anything else is `ARGUMENT_INVALID`. A new start refuses a branch that exists locally or on a remote (`WORKTREE_BRANCH_EXISTS`, checked with `git ls-remote`; an unreachable remote is a `WORKTREE_REMOTE_UNCHECKED` warning and the fetched refs decide). One slug's activity runs in one place only: never start it again, continue it (§3).

## 2. Branch only (`direct`, no worktree)

When `GIT_POLICY` leaves the worktree to you and the task needs none ([git policy](git-policy.md)), start the branch in this checkout:

- `devkit worktree start <branch> --no-worktree` creates the branch from the current HEAD, switches this checkout to it and carries uncommitted changes (`[BRANCH_STARTED: <branch> checkout= from=]`). It records the branch it started from.
- `session` → `spec` during Development: on the session's own `dev-<slug>` keep going; otherwise run this command in the same checkout, then `devkit spec new <slug>` ([classification](classification.md) §3).
- Integrate from the base branch: switch back to the recorded start branch, then `devkit worktree finish <branch> --merge` (or the PR path); finish refuses while the base checkout is on the branch and names the switch.

## 3. Continue an existing branch

Resuming after a stop, switching an activity's mode, and handing an inline-Planned `dev-<slug>` to a worker or a cloud run all continue the branch explicitly, never by starting anew:

```bash
devkit worktree start <branch> --existing-branch <branch|remote/branch> --unit <dir>
```

- `<dir>` is the activity's unit, relative to the project: `docs/proposals/PROP-<slug>` on `plan-<slug>`; on `dev-<slug>` the spec bundle `specs/<YYYY-MM>/<YYYYMMDD>-<slug>`, or the accepted proposal before Development's handoff. devkit-spec's attach check reads it at the branch tip and refuses another unit, another slug or a binding that does not fit (`WORKTREE_ATTACH_REFUSED`, one reason per detail); `WORKTREE_ATTACH_CHECK_FAILED` means it could not verify. Nothing is reset: the unit's records and approvals stay, and the run continues from the stage `devkit workflow next --unit <dir>` names.
- Fetch first to see a branch made elsewhere. A local branch behind or diverged from the remote is `WORKTREE_BRANCH_OUT_OF_SYNC`: synchronize it with the user, never by reset. One ahead is attached with a `WORKTREE_BRANCH_AHEAD` notice: push it when the work is shared.
- A base checkout on the branch is switched back to its recorded start branch first (clean only), else refused.
- Continue a branch only once its earlier run ended. Before taking a cloud run's branch local, confirm the pull request has no active run.

## 4. Leftovers and stale branches

`devkit worktree status` (from the base or any worktree; it changes nothing) lists each worktree as `[WORKTREE: <path> branch= head= role= merged= dirty= prunable=]` and each local branch no worktree checks out and the base HEAD does not contain as `[BRANCH: <name> head= merged=no]`.

- A linked worktree with `merged=yes dirty=no` (including one with no commits yet): `devkit worktree finish <branch>` cleans it.
- `merged=no`, `dirty=yes`, `dirty=-` (unreadable), `prunable=yes` or a `[BRANCH]` line: remove only with the user's authorization, never with `-D` or `--force`. A prunable worktree's directory is already gone; `git worktree prune` forgets it.
- `devkit spec scope sweep` lists registry records whose worktree is gone (`verdict=stale`); `devkit spec scope sweep --apply` removes them.

A `plan-*` or `dev-*` branch whose last commit and pull request activity are older than `[worktree] stale_after` (default `14d`) is stale. `devkit worktree stale` reports each as `[STALE_BRANCH: ...]` with its pull request state and the resume command, and `devkit rules check -p hygiene` repeats them as warnings; both run only when `gh auth status` succeeds and skip with a notice otherwise. Neither blocks anything. Report them with the two ways on, and do neither unasked:

- **Resume**: the `--existing-branch` command it prints. When its unit is `-` (recorded only by an earlier `--existing-branch`), map the slug: `plan-<slug>` → `docs/proposals/PROP-<slug>`; `dev-<slug>` → the spec bundle whose `spec.md` path ends in `-<slug>/spec.md` in `git ls-tree -r --name-only <branch> -- specs`, else the accepted proposal.
- **Discard**: only once the user decides: close its pull request, delete the branch, and for an accepted proposal follow a close ([classification](classification.md) §4).
