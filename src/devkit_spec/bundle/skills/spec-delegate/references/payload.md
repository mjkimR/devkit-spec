# Payload per role

Read this in Step 2 of `spec-delegate` when you fill the five payload fields. Record the head SHA you passed (`git rev-parse HEAD`, or `git -C <worktree> rev-parse HEAD` for a worker). Before spawning a worker, also record the base checkout's `git -C <base> status --short` and HEAD: the worker shares the session's directory, so a stray write lands there.

Never inject the whole tree.

| Field | Content |
| :--- | :--- |
| `task_goal` | One goal for this call |
| `relevant_files` | Files, acceptance criteria, non-goals and ADRs to read; starting points, not a dump |
| `allowed_boundaries` | Read scope and write scope for this task, plus explicitly denied paths; repository-declared paths, not generic globs |
| `diff_scope` | Base ref and head of the change under review (required for `reviewer`, `reconciler`, `worker`) |
| `expected_output_format` | Summary, comparison table, review envelope, docs draft diff, etc. |

| Role | `relevant_files` | `diff_scope` | Also pass |
| --- | --- | --- | --- |
| `scout` | Starting points | optional | The `materials/` path when an artifact is wanted |
| `challenger` | Proposal or spec, AC, non-goals, ADRs, capabilities, as paths (it has no shell) | optional | |
| `reviewer` | `spec.md`, `plan.md`, `tasks.md`, touched capabilities and ADRs | required | Your check results (tests, build, `devkit rules check --staged`) |
| `reconciler` | `spec.md`, the deciding review envelope, likely affected docs (`devkit spec refs <ID> --direction in`) | required | |
| `worker` | The unit's `spec.md`, `plan.md`, `tasks.md` and the code starting points | required: the worktree's base and head | The worktree's absolute path, the write scope inside it (the tasks' `_Boundary:` paths and `tasks.md`), the tasks to build, the checks to run |
