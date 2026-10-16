---
name: spec-orchestrate
description: User-invoked local-orchestrated mode for an activity. The Host stops implementing and coordinates spec and proposal units, each activity on its own branch and devkit worktree, handing each Planning or Development turn to a one-shot worker that commits its result and records, then validating, handling questions and problems, and integrating the results in order. A plain instruction returns to direct mode.
---

# spec-orchestrate: local-orchestrated Mode

The mode is chosen per activity of a slug (Planning or Development), not per session: `direct` is the default, and `local-orchestrated` is the user's choice, never yours; propose it only. Invoking this skill moves the activities the user names into `local-orchestrated` until the user returns them to `direct` or the session ends. Nothing is configured or recorded for the mode: each unit's branch, documents, envelopes and worktree carry what the next worker or a resumed session needs, so a mode can also change at a worker's turn boundary.

---

## 1. When to propose it

Propose it when one of these holds, and stay in `direct` otherwise:

- Independent units whose turns can run at the same time.
- One unit large enough that you should keep your context for coordination and verification.
- The user asks to parallelize or delegate.

It changes no gate, policy or authority. `GATE_POLICY` and `GIT_POLICY` apply as in `direct`; commits, merges, pushes and deletions need the authority they need there. Nested subagents are assumed (Host → worker → role); a host without them stays in `direct`, never a substitute.

## 2. Units and what stays yours

- One unit is one activity of one slug on its own branch (`plan-<slug>` for Planning, `dev-<slug>` for Development) in its own worktree from `devkit worktree start`. Never use a host-native worktree, and never start an activity whose branch already exists: continue it explicitly instead.
- A `session`-depth task never becomes a unit: handle it yourself in `direct`, while the other units keep their mode.
- You keep only: splitting units, preparing each unit (worktree, the handoff or inline Planning), validating results, questions to the user, problems, `dev-integration` and integration. Workers do the rest.
- After registering each unit, `devkit spec scope query` shows overlaps. Overlapping units run one after the other or become one unit; independent units run in parallel.

## 3. The loop per unit

1. **Prepare** (you, in the base): the worktree as the `spec` skill's `references/worktree.md` §1 describes, and the unit's input: an accepted proposal for handoff, a spec Unit whose `plan-intent` is recorded, or a `draft` proposal with `plan-intent` recorded for Planning. Keep the worktree's absolute path for every later command.
2. **Run a turn** (worker): `spec-delegate` with role `planning-worker` or `development-worker`. The payload names the worktree's absolute path, the write scope, the `activity-effort` and, for a later turn, the rewritten answers or the recovery request. The worker runs from the stage `devkit workflow next` names, commits at every stage boundary through the commit gate, writes its own records and returns its head (`ADR-worker-delivers-committed-result`); it never leaves the finishing to you. Workers of independent units may run at the same time; never two workers, or a worker and you, in one worktree. Where the worker's host status is `unsupported`, run the unit yourself in `direct`.
3. **Validate** (you): `spec-delegate` Steps 4 to 6 on the committed range from the last accepted head. A failing range is blocked, never discarded: a `failed` validation envelope, the commits kept (a pull request stays open and blocked), fixed with further commits by a new worker or by you; a blocked unit goes no further. Questions go to the user in one round and the answers to a new worker; a recorded problem is yours to decide (`spec-delegate`'s worker reference).
4. **Accept** (Planning): when the worker returns with no question left, ask the user for `plan-accept` with the change summary and the decisions made in this Planning; record it with `status: accepted`, commit, merge the Planning branch and clean up its worktree. A rejection changes only the status, with the user's reason in the commit message; no worker runs for it.
5. **Integrate** (Development): `dev-integration` per unit once the final change report holds, then `spec-integrate` and `devkit worktree finish` from the base, one unit at a time in the order the overlaps require. A unit integrated after another one first integrates the base (`spec-integrate` Step 1).

## 4. Keeping track

- Keep one line per unit in the conversation: slug, activity, worktree, stage (`devkit workflow next --unit <dir>`), worker state.
- After context loss, `devkit worktree status`, `devkit spec scope query` and `devkit workflow next --unit <dir>` per unit rebuild the picture; the latest `validation` envelope marks the range accepted (`completed`) or blocked (`failed`), and a worker's recorded problem without a resolution keeps the unit blocked.
- Report each unit's completion, commit and integration as separate facts, as in `direct`.

## 5. Returning to direct mode

On the user's instruction, stop starting workers. Let running workers finish and validate their committed results; a blocked unit stays blocked until a later range passes or its problem is resolved. Units still in flight continue in `direct`, one at a time, from the stage `devkit workflow next` reports.
