# Workflows: Overview

The delivery workflows of spec-driven development and the support roles they delegate to. The `spec` bundle ships them as devkit assets: four `kind = "workflow"` definitions (`src/devkit_spec/bundle/workflows/`) and four host-neutral role contracts (`src/devkit_spec/bundle/subagents/`), all in the `core` preset. devkit's workflow engine evaluates them ([Workflow Engine](https://github.com/mjkimR/devkit/blob/main/docs/workflow/overview.md)); `devkit sync` projects the roles into each agent's subagent directory ([Agent Projections](https://github.com/mjkimR/devkit/blob/main/docs/distribution/agent-projections.md)). Ported from specrig's `workflows/` and `subagents/`; the stage schemas are unchanged except where section 4 says otherwise.

## 1. Routes

| Workflow | Route | Unit (layout) | Anchor | Gates |
| --- | --- | --- | --- | --- |
| `s-lane` | 1: low uncertainty, low risk, session-contained | none | none | `intent`, `integration` |
| `direct-delivery` | 2: low uncertainty, contract impact | `specs/{date:%Y-%m}/{date:%Y%m%d}-{slug}` | `spec.md` | `intent`, `direction`, `integration` |
| `bugfix` | 2 for a defect: characterize, reproduce, fix, verify | `specs/{date:%Y-%m}/{date:%Y%m%d}-{slug}` | `spec.md` (`kind: bugfix`) | `intent`, `direction`, `integration` |
| `incubated-delivery` | 3 (local review) and 4 (team PR review): high uncertainty | `docs/proposals/PROP-{slug}` | `proposal.md` | `intent`, `direction` |

Each definition sets its own `layout`, so spec bundles and proposal bundles live where the document model expects them and `devkit workflow list` finds both. `devkit spec new <slug> [--workflow bugfix]` creates a spec bundle with its `SPEC`, `PLAN` and `TASKS` IDs and binds `spec.md` (default `direct-delivery`); `devkit spec proposal new <slug>` creates a proposal bundle bound to `incubated-delivery` ([Proposals](../proposals/overview.md)). `devkit workflow next --unit <dir>` names the current stage, its unmet checks and the skill to open (`[NEXT_SKILL]`), and `devkit workflow show <id>` renders a definition. `s-lane` has no unit: the executor reads its stages with `show` and follows them in the session.

## 2. Stages

`devkit workflow show <id>` is the authoritative list; in order:

- **`s-lane`**: `intent-session` (G1), `execute-verify`, `report-session`, `approval-session` (G3), `commit-session`, `merge`.
- **`direct-delivery`**: `intent` (G1), `direction` (G2), `specify`, `build-verify`, `review-refine`, `living-spec-draft`, `collect-feedback`, `final-change-report`, `integration-approval` (G3), `integrate`, `merge`.
- **`bugfix`**: `intent` (G1), `characterize`, `direction` (G2), `plan-tasks`, `reproduce`, `fix-verify`, then the stages of `direct-delivery` from `review-refine` on.
- **`incubated-delivery`**: `intent-proposal` (G1), `spike` (optional), `direction-handoff` (G2), `handoff`.

Every workflow also has the out-of-band `exception` stage (E). A stage id shared by several definitions has the same exit checks, gate, role, isolation, skills and artifacts in each; `devkit workflow validate` with no arguments reports a difference as `SHARED_STAGE_MISMATCH`. Stages delegate to the roles `reviewer` (`review-refine`), `reconciler` (`living-spec-draft`) and `scout` (`spike`); `challenger` is invoked through `sr-challenge`. Every role is optional: the Developer may run the procedure in the main session.

## 3. Gates and Project Policy

specrig's gates G1, G2 and G3 are the devkit gates `intent`, `direction` and `integration`, governed by `[workflow.approvals]` in `.devkit/config.toml`. Under `ask` a gate waits for a decision record (`devkit workflow answer --unit <dir> --request gate:<gate> --action accept`, written only after the user's explicit answer); under `auto` it passes by policy and `next` shows `source=policy`; `off` skips the stage. devkit defaults every gate to `ask`, while specrig defaulted `direction` to `auto`. To keep specrig's behavior, where G2 fires only for a new choice outside the approved scope:

```toml
# .devkit/config.toml
[workflow.approvals]
intent = "ask"        # G1: the user confirms goal, scope and verification
direction = "auto"    # G2: choices within the requested scope proceed with reported assumptions
integration = "ask"   # G3: one approval per integration unit (PR)

[workflow.stages]
# collect-feedback = "off"   # specrig's feedback.sweep = off
```

Under `direction = "auto"` the G2 of `incubated-delivery` also passes by policy; the executor still puts a direction outside the requested scope to the user. PR and branch policy is `[worktree]`; whether a route runs in a task worktree (`devkit worktree start|finish`) is `[tool.spec] worktree`. `devkit spec policy` prints all of it.

## 4. Check Mapping from specrig

| specrig check | devkit | Notes |
| --- | --- | --- |
| `spec-dir-exists` | `anchor-exists` | `file-exists(spec.md)` under the spec layout, `file-exists(proposal.md)` under the proposal layout. |
| `plan-exists` | `file-exists(plan.md)` | |
| `tasks-exists`, `tasks-all-checked`, `envelope-review-passed`, `lint-clean` | same names | devkit aliases and checks; `lint-clean` runs `devkit rules` (linter phase) on the unit's files. |
| `reconcile-resolved` | `frontmatter(reconcile.md status resolved)` | |
| `spec-status-completed` | `anchor-status-completed` | |
| `envelope-final-report-present` | `envelope-check-pass(final-report tests)`, `envelope-check-pass(final-report build)`, `envelope-check-pass(final-report lint)` | The three keys specrig's evaluator required. |
| `not-skeleton(<file>)`, `frontmatter(...)`, `envelope-check-pass(...)` | same primitives | devkit's skeleton marker is `<!-- devkit:skeleton -->`. |
| `intent-recorded`, `direction-chosen`, `approval-given` (human) | gates `intent`, `direction`, `integration` | No longer exit checks; `entry` lists that named them now name the gate stage's predecessor checks. |
| `exception-raised`, `exception-handled` (human) | declared `human` checks | Declared in each definition's `checks`. |
| `lint-ci-clean`, `merged` (runner) | declared `runner` checks | `lint-ci-clean` is `devkit rules check --ci --base <ref>` on the committed head; declare it and `merged` with `--given` (a runner binds them to CI and PR state). |

Other deviations from specrig:

- **The exception stage has no gate.** specrig marked it `human_gate: true`; in devkit an exception stage is never evaluated and a gate would add an `exception` approval key, so the `exception-handled` human check carries the decision.
- **G3 has no exit checks of its own.** The gate is asked as soon as `integration-approval` is current, that is once the final change report holds.
- **No `--development` mode.** Commits go through plain `git commit` and devkit's commit gate; intermediate commits follow existing commit authority, and the Living Spec reflection must be complete before G3.

## 5. Proposal Handoff

`incubated-delivery` ends at handoff and declares no `next` candidates: devkit's `devkit workflow handoff` rebinds a unit in place and refuses a candidate with another anchor (`HANDOFF_LAYOUT_MISMATCH`), so it cannot turn a proposal bundle into a spec bundle. Once the direction gate holds, `next` reports the proposal unit complete, and `devkit spec proposal handoff <slug>` does the cross-layout move: it creates `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` from the proposal and binds `spec.md` to the delivery workflow the proposal names in `handoff_workflow` (`bugfix`, default `direct-delivery`; `workflow` in `proposal.md` is the proposal unit's own binding). That workflow is then evaluated from its first stage; its G1 is the spec bundle's intent, normally confirmed by the accepted proposal. Skeleton files the handoff writes must carry devkit's `<!-- devkit:skeleton -->` line (specrig's marker was `<!-- specrig:handoff-skeleton -->`), which keeps `specify` (or `plan-tasks`) open until `sr-spec`, `sr-plan` and `sr-tasks` replace them.

## 6. Role Contracts

One Markdown contract per role, in devkit's [role contract format](https://github.com/mjkimR/devkit/blob/main/docs/distribution/agent-projections.md#role-contract-format): `role`, `title`, `description`, `skill` (the `sr-*` procedure) and a `hosts` block for `claude-code`, `codex` and `antigravity`. specrig-only metadata is kept as extension keys devkit does not interpret: `x-execution`, `x-invocation`, `x-model-profile` (`light-medium`, `general-high`, `high-reasoning`; never a host model name) and `x-git-actions` (`[read]` for every support role).

| Role | Skill | Writes | Envelope kind |
| --- | --- | --- | --- |
| `challenger` | `sr-challenge` | nothing | `challenger` |
| `reconciler` | `sr-sync` | docs drafts and the bundle's `reconcile.md` | `reconciler` |
| `reviewer` | `sr-review` | nothing | `review`, `reverify` |
| `scout` | `sr-scout` | nothing, or the proposal's `materials/` on request | `scout` |

A role returns the fields of a devkit envelope; the Developer records them with `devkit workflow envelope new --unit <dir> --kind <kind> ...` and checks them with `devkit workflow envelope check --unit <dir>`. specrig's `docs_impact` block has no envelope key in devkit: the reconciler writes the docs impact into the draft `reconcile.md`, where it already lived. No role stages or commits.
