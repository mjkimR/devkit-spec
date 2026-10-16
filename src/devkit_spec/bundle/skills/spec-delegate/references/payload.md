# Payload per role

Read this in Step 2 of `spec-delegate` when you fill the five payload fields. Record the head SHA you passed (`git rev-parse HEAD`). For a worker, pass the `activity-effort` of the activity and record what [worker](worker.md) lists before spawning: the unit's last accepted head (a blocked unit keeps its own, never its current HEAD) and the base checkout's status and HEAD, since the worker shares the session's directory and a stray write lands there.

Never inject the whole tree.

| Field | Content |
| :--- | :--- |
| `task_goal` | One goal for this call |
| `relevant_files` | Files, acceptance criteria, non-goals and ADRs to read; starting points, not a dump |
| `allowed_boundaries` | Read scope and write scope for this task, plus explicitly denied paths; repository-declared paths, not generic globs |
| `diff_scope` | Base ref and head of the change under review (required for `reviewer`, `reconciler` and the workers) |
| `expected_output_format` | Summary, comparison table, review envelope, docs draft diff, etc. |

| Role | `relevant_files` | `diff_scope` | Also pass |
| --- | --- | --- | --- |
| `scout` | Starting points | optional | The `materials/` path when an artifact is wanted |
| `challenger` | Proposal or spec, AC, non-goals, ADRs, capabilities, as paths (it has no shell) | optional | |
| `reviewer` | `spec.md`, `plan.md`, `tasks.md`, touched capabilities and ADRs | required | Your check results (tests, build, `devkit rules check --staged`) |
| `reconciler` | `spec.md`, `reconcile.md`, the deciding review envelope, the targeted and likely affected docs (`devkit spec refs <ID> --direction in`) | required | |
| `development-worker` | The unit's `spec.md`, `plan.md`, `tasks.md` and the code starting points | required: the last accepted head; the worker returns its own head | The worktree's absolute path, the write scope inside it (the unit's directory, the tasks' `_Boundary:` paths, the Living Spec paths the reconcile targets), the checks to run, the `activity-effort`, a recovery request for an open problem |
| `planning-worker` | The proposal bundle and the starting points | required: the last accepted head; the worker returns its own head | The worktree's absolute path, the proposal directory as write scope, the `activity-effort`, the user's rewritten answers to the recorded questions |
