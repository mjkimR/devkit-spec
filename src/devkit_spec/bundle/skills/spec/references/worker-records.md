# Worker records: questions, answers, problems and resolutions

Read this when a Planning or Development run ends, when you process a run's questions or problem, and when `devkit workflow next` or `devkit workflow envelope check` prints `[PENDING_QUESTION]` or `[BLOCKED]`. devkit owns the format and the checks (its envelope contract); this says who writes what in spec-driven delivery. A `session` task writes none of these: it reports in the conversation or the PR body.

The rule: **one run leaves one `worker` envelope; what another actor does later is a separate envelope that names it.** The questions a run asks and the problem it stopped on live in its `worker` envelope; the answers live in an `answer` envelope (`answers_to`), the fix in a `resolution` envelope (`resolves`). There is no separate question or problem kind.

## 1. The `worker` envelope (one per run)

Every run of one activity's turn ends with exactly one `worker` envelope, not one per stage, committed with the run's last changes: completed, waiting for answers or stopped by a problem. A `planning-worker` or `development-worker` writes its own; in `direct` mode you write it for your run whenever you stop for the user or end the activity. It is the run's record (what it did, its effort, how it ended), which `cloud-pr` has nowhere else to keep.

```bash
devkit workflow envelope new --unit <dir> --kind worker --stage <stage> --summary "<what this run did>" \
  --effort <low|medium|high> --check tests="PASS 14/14" --head <last commit>
```

`<last commit>` is `git -C <worktree> rev-parse HEAD` after the run's last commit.

- **Questions**: add `--questions-file <path>|-`, a YAML list of `id`, `title` (40 characters at most), `prompt`, optional `context`, `options` (`{id, description, recommended}`, at most one recommended) and `allow_note`; the status becomes `needs_input`. Gather every question of the round in it; finish everything that does not depend on an answer first.
- **Problem**: add `--problem "<cause>" --tried "<attempt>" --recovery "<recommended recovery>"`; the status becomes `failed`, or pass `--status needs_input` when only the user can decide. A run that both asks and hit a problem records both (`needs_input`). A `completed` envelope never carries a problem.
- A problem is only what breaks the agreed goal, scope or contract, or what cannot be solved at all; a choice you can decide is not one, and waiting for answers is not one either.

## 2. Answers

devkit shows every unanswered question as `[PENDING_QUESTION: <file> id=<q> ...]` and as a request `[REQUEST: id=question:worker-NN.<q> kind=choose ... answer=envelope]`, and holds every gate (`[GATE: ... held=yes]`) until all are answered. `devkit workflow answer` refuses those requests (`DECISION_INVALID`).

- Put the questions to the user in one round with their options and recommendation; ask back at once about anything ambiguous.
- The run that processes the answers records them first, in a commit of its own, then folds the decisions into the documents (proposal and PADRs, or `spec.md` and `plan.md`) in a separate commit. In `local-orchestrated` the new worker writes the record from your rewritten answers; in `direct` you write it:

```bash
devkit workflow envelope new --unit <dir> --kind answer --stage <stage> --summary "q1, q2 decided" \
  --answers-to worker-NN.yaml --answers-file -    # - { question: q1, choice: a, decision: "...", constraints: [...] }
```

- One decision sentence per question; `choice: null` for an answer outside the options; `constraints` only for what the answer adds. Never the raw conversation, the reasoning or the question again. An answer that leaves something ambiguous becomes a new question in the next run's `worker` envelope, never a guess.

## 3. Problems and resolutions

`[BLOCKED: <file> cause="..." recovery="..."]` means the unit is blocked: a problem has no `resolution` that names it. Every gate is held, and `devkit worktree finish --merge` refuses the branch (`WORKTREE_BLOCKED`). A later commit, a successful `worker` envelope, a comment or a rerun request clears nothing.

- You decide the recovery inside the approved scope: fix or revert yourself (`git revert`, never reset), or send a new worker the recovery request. A recovery that needs the scope changed goes to the user and a close ([classification](classification.md) §4).
- Whoever actually fixed it writes the resolution, in the same commit as the fix; one who could not fix it writes none and records what it tried in its own `worker` envelope:

```bash
devkit workflow envelope new --unit <dir> --kind resolution --resolves worker-NN.yaml \
  --summary "<what was done and why it resolves the problem>"
```

## 4. Checking and integrating

`devkit workflow envelope check --unit <dir>` lists the files, `[BLOCKED]` and `[PENDING_QUESTION]`; `--format json` gives `blocked`, `problems` and `pending_questions`. Before a pull request merges, the integrator (you, `spec-integrate`, or the cloud service) runs it on the PR head and merges only with `"blocked": false` and no `pending_questions`; a local `devkit worktree finish --merge` checks the same itself.
