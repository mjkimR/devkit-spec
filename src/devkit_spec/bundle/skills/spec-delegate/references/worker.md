# Worker results

Read this in Steps 4 to 6 of `spec-delegate` for a `planning-worker` or `development-worker` (`local-orchestrated`
mode). A worker is one-shot: it runs one turn in its activity branch's worktree, writes its own records, commits at
every stage boundary and ends with its head returned, also when it stops on a question or a problem (an emergency
commit of the unfinished work with its `worker` envelope). You validate the committed range, accept or block it, and
decide what a recorded problem needs; you never finish a turn by writing the worker's records for it
(`ADR-worker-delivers-committed-result`).

## The last accepted head

The range a worker is judged on starts at the unit's *last accepted head*:

- A unit that is not blocked: the worktree's HEAD when you spawn the worker (`git -C <worktree> rev-parse HEAD`), after
  your own commits (validations, recoveries) are in.
- A blocked unit keeps the head its blocked range started from. Never pass a blocked unit's current HEAD as the base:
  the rejected commits must stay in the range.

Pass it as `diff_scope` base, and record the base checkout's `git -C <base> status --short` and HEAD before spawning.

## Validate the cumulative range

From the last accepted head to the returned head (`diff_scope.head`):

- `git -C <worktree> merge-base --is-ancestor <accepted> <returned>` succeeds and the worktree's HEAD is `<returned>`.
- Every path of `git -C <worktree> diff --name-only <accepted> <returned>` is in the write scope: the worker's own
  records under `<unit>/envelopes/` and `<unit>/decisions/` included, except the validation envelopes you wrote under
  `<unit>/envelopes/` since `<accepted>`, each unchanged since your commit of it
  (`git -C <worktree> diff <your commit> <returned> -- <envelope>` is empty). A worker never writes a `validation`
  envelope. After context loss, take as yours only the envelope commits `git log` shows touching nothing else and whose
  records you can account for; otherwise block.
- `git -C <worktree> status --short` is empty; the base checkout's status and HEAD are as recorded.
- The unit's checks pass on `<returned>`: the worker's results, confirmed by the pull request's CI or by rerunning them
  in the worktree. A worker that stopped on a problem returns unfinished work: validate its paths, not its checks.

## Accept or block

Record each validation as a `validation` envelope at the unit's current stage (`devkit workflow next --unit <dir>`
names it; `build-verify`, or `fix-verify` in `sdd-spec-bugfix`, while building) and commit it before anything else, so
the worktree stays clean.

- **Accept**: `devkit workflow envelope new --unit <dir> --kind validation --stage <stage> --status completed --base
  <accepted> --head <returned> ...`, commit it, run `devkit spec scope update --spec <dir>`. The unit is no longer
  blocked by it; the next spawn starts from HEAD.
- **Block**: the same with `--status failed` and one finding per violation (path or check, cause). Keep the commits:
  never reset or amend; a pull request stays open and blocked (changes requested or a failing required check). A
  blocked unit goes to no review and no integration. Send a new worker with the findings, or fix it yourself, with
  further commits on the same branch (a revert commit for an out-of-scope change), then validate the cumulative range
  again from the same last accepted head.

A unit is blocked while its latest `validation` envelope is `failed`, whatever a worker returns afterwards, and while a
problem a worker recorded has no resolution that names it; a later commit or a successful `worker` envelope clears
neither.

## Questions and problems

- **Questions** (`planning-worker`, `needs_input` without a problem): put the recorded questions to the user in one
  round, ask back at once about anything ambiguous, and hand the rewritten answers to a new worker, which records them
  first. Waiting for answers is not a problem and needs no resolution.
- **Problems** (`failed`, or `needs_input` with a problem): read the cause, what was tried and the recommended recovery.
  Inside the approved scope decide yourself: fix or revert (`git revert`, never reset) and commit the fix together
  with a resolution record that names the problem, or send a new worker the recovery request, which commits its fix
  with that record only once it actually solved it. A comment or a rerun request alone resolves nothing. A problem
  that needs the scope changed goes to the user and a close (the `spec` skill's `references/classification.md`).
