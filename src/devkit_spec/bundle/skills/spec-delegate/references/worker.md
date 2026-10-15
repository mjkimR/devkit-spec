# Worker results

Read this in Steps 4 to 6 of `spec-delegate` for a `worker` (orchestration mode). The worker commits its complete build
on the unit branch and returns its head; you validate the committed range and accept or block it, and never finish
the build for it (`ADR-worker-delivers-committed-result`).

## The last accepted head

The range a worker is judged on starts at the unit's *last accepted head*:

- A unit that is not blocked: the worktree's HEAD when you spawn the worker (`git -C <worktree> rev-parse HEAD`), after
  your own commits (envelopes, review fixes) are in.
- A blocked unit keeps the head its blocked range started from. Never pass a blocked unit's current HEAD as the base:
  the rejected commits must stay in the range.

Pass it as `diff_scope` base, and record the base checkout's `git -C <base> status --short` and HEAD before spawning.

## Validate the cumulative range

From the last accepted head to the returned head (`diff_scope.head`); `<unit>/envelopes/` holds only your records and
is left out of the path comparison:

- `git -C <worktree> merge-base --is-ancestor <accepted> <returned>` succeeds and the worktree's HEAD is `<returned>`.
- Every path of `git -C <worktree> diff --name-only <accepted> <returned> -- . ':(exclude)<unit>/envelopes'` is in the
  write scope.
- `git -C <worktree> diff <accepted> <returned> -- <unit>/spec.md` changes the `status:` line only.
- `git -C <worktree> status --short` is empty; the base checkout's status and HEAD are as recorded.
- The unit's checks pass on `<returned>`: the worker's results, confirmed by the pull request's CI or by rerunning them
  in the worktree.

## Accept or block

Record each validation as a `worker` envelope at the unit's current build stage (`build-verify`, or `fix-verify` in
`bugfix`; `devkit workflow next --unit <dir>` names it) and commit it before anything else, so the worktree stays clean.

- **Accept**: `devkit workflow envelope new --unit <dir> --kind worker --stage <stage> --status completed --base
  <accepted> --head <returned> ...`, commit it, run `devkit spec scope update --spec <dir>`. The unit is no longer
  blocked; the next spawn starts from HEAD.
- **Block**: the same with `--status failed` and one finding per violation (path or check, cause). Keep the commits:
  never reset or amend; a pull request stays open and blocked (changes requested or a failing required check). A
  blocked unit goes to no review and no integration. Send the worker back with the findings, or fix it yourself, with
  further commits on the same branch (a revert commit for an out-of-scope change), then validate the cumulative range
  again from the same last accepted head.

A unit is blocked while its latest `worker` envelope is `failed`, whatever a worker returns afterwards. A worker's
`needs_input` or `failed` return is not a validation and gets no envelope: its last return added no commit, and its
unfinished work is uncommitted in the worktree. Answer inside the approved scope (or through the `direction` gate) and
resume it, or take that work over; validate once a worker returns `completed`.
