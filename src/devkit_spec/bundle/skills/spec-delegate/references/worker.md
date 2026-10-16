# Worker results

Read this in Steps 4 to 6 of `spec-delegate` for a `planning-worker` or `development-worker` (`local-orchestrated`
mode). A worker is one-shot: it runs one turn in its activity branch's worktree, writes its own records, commits at
every stage boundary and ends with its head returned and exactly one `worker` envelope, also when it stops on a
question or a problem (an emergency commit of the unfinished work). You validate the committed range, accept or block
it, and decide what a recorded problem needs; you never finish a turn by writing the worker's records for it
(`ADR-worker-delivers-committed-result`). The record formats are in the `spec` skill's `references/worker-records.md`.

## The last accepted head

The range a worker is judged on starts at the unit's *last accepted head*:

- A unit that is not blocked: the worktree's HEAD when you spawn the worker (`git -C <worktree> rev-parse HEAD`), after
  your own commits (blocks, recoveries) are in.
- A blocked unit keeps the head its blocked range started from. Never pass a blocked unit's current HEAD as the base:
  the rejected commits must stay in the range.
- After context loss, when you cannot account for the last accepted head, validate the whole branch: from its merge
  base with the base branch.

Pass it as `diff_scope` base, and record the base checkout's `git -C <base> status --short` and HEAD before spawning.

## Validate the cumulative range

From the last accepted head to the worker's *final HEAD* (`<returned>`: the `final_head` it returns, the commit that contains its `worker` envelope). The envelope's `diff_scope.head` is the head of the work it did, committed before the envelope, so it is never `<returned>`; it is evidence about the work, not the end of the range:

- `git -C <worktree> merge-base --is-ancestor <accepted> <returned>` succeeds, the worktree's HEAD is `<returned>`, and the envelope's `diff_scope.head` is an ancestor of `<returned>` (`merge-base --is-ancestor <diff_scope.head> <returned>`).
- Every path of `git -C <worktree> diff --name-only <accepted> <returned>` is in the write scope: the worker's own
  records under `<unit>/envelopes/` and `<unit>/decisions/` included, except the records you wrote under
  `<unit>/envelopes/` since `<accepted>` (your blocking `worker` envelopes and your resolutions), each unchanged since
  your commit of it (`git -C <worktree> diff <your commit> <returned> -- <envelope>` is empty). After context loss,
  take as yours only the envelope commits `git log` shows touching nothing else and whose records you can account
  for; otherwise block.
- `git -C <worktree> status --short` is empty; the base checkout's status and HEAD are as recorded.
- The unit's checks pass on `<returned>`: the worker's results, confirmed by the pull request's CI or by rerunning them
  in the worktree. A worker that stopped on a problem returns unfinished work: validate its paths, not its checks.

## Accept or block

- **Accept**: write nothing; run `devkit spec scope update --spec <dir>`. The next spawn starts from HEAD.
- **Block**: the violation is a problem your validation run found. Record it as that run's own `worker` envelope at
  the unit's current stage (`devkit workflow next --unit <dir>` names it; `build-verify`, or `fix-verify` in
  `sdd-spec-bugfix`, while building): `devkit workflow envelope worker --unit <dir> --stage <stage>
  --effort <activity-effort> --problem "<the committed range breaks its boundary or checks>" --recovery "<what must change>" --findings-file -
  --base <accepted> --head <returned>`, one finding per violation (path or check, cause), and commit it before
  anything else, so the worktree stays clean. Keep the commits: never reset or amend; a pull request stays open and
  blocked (changes requested or a failing required check). A blocked unit goes to no review and no integration: devkit
  holds the gates of the blocked stage and later ones and the handoff, and refuses `devkit worktree finish --merge`
  (`WORKTREE_BLOCKED`); `devkit workflow next` keeps naming the current stage, where the recovery runs. Send a new worker the findings
  as a recovery request, or fix it yourself, with further commits on the same branch (a revert commit for an
  out-of-scope change); whoever fixes it commits a `resolution` naming your envelope with the fix. Then validate the
  cumulative range again from the same last accepted head.

A unit is blocked while any problem, a worker's or yours, has no resolution that names it (`[BLOCKED]` in
`devkit workflow next` and `devkit workflow envelope check`); a later commit or a successful `worker` envelope clears
nothing. A comment or a rerun request alone resolves nothing.

## Questions and problems

- **Questions** (`needs_input` without a problem; `[PENDING_QUESTION]`): put the questions of the worker's envelope to
  the user in one round, ask back at once about anything ambiguous, and hand the rewritten answers to a new worker,
  which records them first as an `answer` envelope naming that `worker` envelope. Waiting for answers is not a problem
  and needs no resolution, but it holds the gates from the run's stage on, and the handoff, until answered.
- **Problems** (`failed`, or `needs_input` with a problem): read the cause, what was tried and the recommended recovery.
  Inside the approved scope decide yourself: fix or revert (`git revert`, never reset) and commit the fix together
  with a resolution that names the problem, or send a new worker the recovery request, which commits its fix with
  that resolution only once it actually solved it. A problem that needs the scope changed goes to the user and a close
  (the `spec` skill's `references/classification.md`).


Planning feedback remains inside the proposal directory, with no extra worker write root. Each Planning run records
observations before its last work commit and returns fresh enabled sweep evidence plus its single worker record,
including question rounds; validate the actual range against that procedure. A previous PASS is not later-run coverage.
Stage-off has no sweep envelope, requested-only has policy-skip PASS and incomplete coverage names its gap. Development
workers likewise capture observed feedback in their own spec before their last work commit.
