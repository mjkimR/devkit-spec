---
name: spec-orchestrate
description: User-invoked orchestration mode. The host stops implementing and coordinates independent spec units, each in its own devkit worktree, delegating each unit's build to a worker subagent and validating, committing and integrating the results in order. A plain instruction returns the session to direct mode.
---

# spec-orchestrate: Orchestration Mode

Every session starts in direct mode: the host implements, in the current checkout or the task's worktree as the `GIT_POLICY` levels decide (the `spec` skill's `references/completion.md`). Invoking this skill switches the session to orchestration mode until the user returns it to direct mode with a plain instruction or the session ends. The mode is session state: nothing is configured or recorded for it. Each unit's own records (spec bundle, envelopes, scope registry, worktree) carry what a resumed session needs.

---

## 1. When to propose the switch

The user switches; you propose it when one of these holds, and stay in direct mode otherwise:

- The request splits into independent units whose builds can run at the same time.
- One unit's build is large enough that the host should keep its context for coordination and review.
- The user asks to parallelize or delegate implementation.

The switch changes no gate, policy or authority. `GATE_POLICY` and `GIT_POLICY` apply to each unit as in direct mode; commits, merges, pushes and deletions need the authority they need there.

## 2. Units

- One parallel item is one unit: its own spec bundle (Route 2 `direct-delivery` or `bugfix`, or a Route 3 handoff) in its own worktree from `devkit worktree start <slug>`, at either worktree level. Never use a host-native worktree. Task-level fan-out inside one bundle is not part of this mode.
- After registering each unit, `devkit spec scope query` shows overlaps. Overlapping units run one after the other or become one unit; independent units run in parallel.

## 3. The loop per unit

1. **Start** (host, in the base): `devkit worktree start <slug>` and the printed `cd` target, then `devkit spec new <slug>` (or the proposal handoff) and `devkit spec scope register --spec <dir>` inside it, as the `spec` skill's `references/worktree.md` §1 describes. Keep the worktree's absolute path for every later command.
2. **Plan** (host): G1, G2, `spec-specify`, `spec-plan` and `spec-tasks` in the unit's worktree. Gates follow `GATE_POLICY`; under `ask` the user answers each unit's gates.
3. **Build** (worker): `spec-delegate` with role `worker`. The payload names the worktree's absolute path, the write scope (the tasks' `_Boundary:` paths and `tasks.md`), the tasks and the checks to run. Workers of independent units may run at the same time through the host's subagent mechanism; never two workers, or a worker and you, in one worktree. Where the worker's host status is `unsupported`, build the unit yourself in its worktree.
4. **Validate and commit** (host): `spec-delegate` Steps 4 to 6 in the worktree. A rejected result is reverted and re-delegated with its cause, or built by you. A `needs_input` worker gets an answer inside the approved scope, or the question goes to the user through the `direction` gate.
5. **Review and sync** (host, or the `reviewer` and `reconciler` roles): `spec-review`, `spec-sync`, the feedback sweep and the final change report, as in direct mode.
6. **Integrate** (host): G3 per unit, then `spec-integrate` and `devkit worktree finish` from the base, one unit at a time in the order the overlaps require. A unit integrated after another one first integrates the base (`spec-integrate` Step 1).

## 4. Keeping track

- Keep one line per unit in the conversation: slug, worktree, stage (`devkit workflow next --unit <dir>`), worker state.
- After context loss, `devkit worktree status`, `devkit spec scope query` and `devkit workflow next --unit <dir>` per bundle rebuild the picture; an envelope of kind `worker` marks a validated build.
- Report each unit's completion, commit and integration as separate facts, as in direct mode.

## 5. Returning to direct mode

On the user's instruction, stop starting workers. Let running workers finish and validate their results, or stop them and revert their unvalidated changes; never leave a worktree with an unvalidated worker diff. Units still in flight continue in direct mode, one at a time, from the stage `devkit workflow next` reports.
