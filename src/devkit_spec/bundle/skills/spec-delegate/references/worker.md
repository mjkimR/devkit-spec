# Worker results

Read this in Steps 4 to 6 of `spec-delegate` for a `worker` (orchestration mode). The worker commits its complete build
on the unit branch and returns its head; you validate the committed range and accept or block it, and never finish
the build for it (`ADR-worker-delivers-committed-result`).

## Before spawning

Record the worktree's head (`git -C <worktree> rev-parse HEAD`), the *last accepted head* until a range is accepted,
and the base checkout's `git -C <base> status --short` and HEAD. Pass that head as `diff_scope` base.

## Validate the cumulative range

From the last accepted head to the returned head (`diff_scope.head`):

- `git -C <worktree> merge-base --is-ancestor <accepted> <returned>` succeeds and the worktree's HEAD is `<returned>`.
- Every path of `git -C <worktree> diff --name-only <accepted> <returned>` is in the write scope.
- `git -C <worktree> diff <accepted> <returned> -- <unit>/spec.md` changes the `status:` line only.
- `git -C <worktree> status --short` is empty; the base checkout's status and HEAD are as recorded.
- The unit's checks pass on `<returned>`: the worker's results, confirmed by the pull request's CI or by rerunning them
  in the worktree.

## Accept or block

- **Accept**: `devkit workflow envelope new --unit <dir> --kind worker --stage build-verify --status completed --base
  <accepted> --head <returned> ...`, commit the envelope, run `devkit spec scope update --spec <dir>`. `<returned>`
  becomes the last accepted head.
- **Block**: record the envelope with `--status failed` and one finding per violation (path or check, cause). Keep the
  commits: never reset or amend; a pull request stays open and blocked (changes requested or a failing required check).
  A blocked unit goes to no review and no integration. Send the worker back with the findings, or fix it yourself, with
  further commits on the same branch (a revert commit for an out-of-scope change), then validate the cumulative range
  again from the same last accepted head.
- **`needs_input` or `failed` from the worker**: nothing incomplete was committed. Answer inside the approved scope (or
  through the `direction` gate) and resume it, or take its uncommitted work over.
