---
name: spec
description: Main entry skill for development intent; conversational router and pair programmer. Routes intent across the spec-driven delivery workflows and, on request, operational playbooks.
---

# spec: Conversational Router & Pair Programmer

Use this skill for any development task, feature request, troubleshooting, or operational workflow. `spec` is the **central human-agent router**: it directs each intent to the spec-driven delivery skill or operational playbook that fits, using **progressive disclosure**.

Read `devkit spec policy` before routing work. Use the effective approval and Git policy with [completion](references/completion.md). Explicit user instructions and authorization already given take precedence; `auto` removes an additional gate question inside the requested scope, without granting authority for new Git or external actions. A policy command error stops policy-dependent work.

---

## 1. Operating Invariants

1. **No Session Hijacking (`MUST NOT`)**:
   - The agent MUST NOT unilaterally declare the user's session finished or stop working on active tasks without user direction.
2. **Contextual Retrospective Reminder (`SHOULD`)**:
   - Under `FEEDBACK_POLICY reminder=contextual`, reusable observations from completed work SHOULD prompt an optional `/spec-feedback` sweep. Under `reminder=off`, omit reminders. Routine completions, proposal additions and wording edits alone need no reminder.
3. **Progressive Disclosure (`SHOULD`)**:
   - Load only the instructions for the current phase rather than every template, instruction or playbook up front.

---

## 2. Two-Tier Routing Workflow

When the user enters `/spec <intent>` or asks a general engineering question:

### Tier 1: Route Selection
Check the nature of the request against the routes of the spec constitution (`devkit get-context spec`). Before any bundle or edit, settle the worktree per `GIT_POLICY` ([worktree](references/worktree.md)):

| Intent Category | Selected Route | Action / Sub-Skill |
| :--- | :--- | :--- |
| **Low uncertainty + Low risk** (<15m) | **Route 1: S-Lane** → workflow `s-lane` | Direct modification without planning artifacts (`devkit workflow show s-lane`; there is no unit, so follow its stages in the session). Run relevant checks and mandatory Living Spec reconciliation. A small, low-risk defect takes this lane too. |
| **New feature / high contract impact** | **Route 2: Direct delivery** → workflow `direct-delivery` | `devkit spec new <slug> --title "..." --summary "..."` creates and binds `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/`, then run `spec-specify` ➔ `spec-plan` ➔ `spec-tasks`. |
| **Defect with contract impact or uncertainty** (observed behavior contradicts an existing contract; larger than an S-Lane fix) | **Formal bugfix** (Route 2 weight) → workflow `bugfix` | `devkit spec new <slug> --workflow bugfix`, then `spec-specify` (its bugfix reference: characterize, reproduce with a `red` envelope, fix and verify with a `green` envelope) ➔ `spec-plan` ➔ `spec-tasks`. |
| **High uncertainty + local review** | **Route 3: Incubated** → workflow `incubated-delivery` | `devkit spec proposal new <slug>` scaffolds `docs/proposals/PROP-<slug>/` bound to `incubated-delivery` (`--handoff-workflow bugfix` for a defect). On acceptance, run `devkit spec proposal handoff <slug>` (`--direction-chosen` when the user chose a `draft` or `reviewing` proposal's direction); it binds the new spec bundle to the proposal's `handoff_workflow`, default `direct-delivery`. Then run the `spec-next` skill's post-handoff link check. |
| **High uncertainty + team PR review** | **Route 4: Full RFC** → workflow `incubated-delivery` | Draft the proposal bundle on a PR branch before spec handoff. Handoff and the post-handoff link check follow Route 3. |
| **Feature planning & architecture** | Planning | Trigger `spec-plan`. |
| **Task implementation** | Building | Follow `tasks.md` boundaries and run incremental tests. |
| **Pre-merge review & rule check** | Verification | Trigger `spec-review`. |
| **Living spec reconciliation** | Sync | Trigger `spec-sync`. |
| **Entrypoints from a spec bundle** | Sync | Trigger `spec-entrypoints`: derive docs-code links, review, apply. |
| **Spike, independent review, or docs draft in an isolated context** | Optional Support Role | Trigger `spec-delegate` (roles `scout` and `challenger`; `reviewer` runs `spec-review`, `reconciler` the `spec-sync` draft steps). Optional by route, risk and request. |
| **Integration after G3 authorization** | Integration | Trigger `spec-integrate`: base integration, re-verify changed parts, confirm reconcile, final checks. |

Each route uses one workflow (`s-lane`, `direct-delivery`, `bugfix`, `incubated-delivery`), without conditional stages. Read its stage order, checks, gates (`intent` G1, `direction` G2, `integration` G3; the `exception` stage E) and returns with `devkit workflow show --unit <dir>`, or `devkit workflow show <workflow-id>` for work without a bundle; `devkit spec new` defaults to `direct-delivery`. External runners use the same definition; follow it.

Gates follow `GATE_POLICY`. `intent` always needs the user's intent (goal, scope, verification). `direction` under `auto` delegates choices within the requested scope with reported assumptions; under `ask` it confirms concrete new direction choices, reusing existing agreement. Unresolved requirements and exceptions need input. Under `ask`, `devkit workflow next` prints `[WAITING: human gate:<gate>]` with a `[REQUEST]`; after the user's explicit answer only, record a G1 or G2 answer with `devkit workflow answer --unit <dir> --request gate:<gate> --action accept|decline --by user`; a G3 OK is not recorded but passed as `--given integration` to every later `next`.

`devkit spec new` and proposal handoff bind the bundle; a bundle made otherwise is bound with `devkit workflow bind --unit <dir> --workflow <id>`. `devkit workflow next --unit <dir>` refuses `WORKFLOW_DRIFT` when the bound schema changed; rebind after review. An approval is never inferred or hand-written; `--given` asserts the G3 OK or a runner check (`lint-ci-clean`, `merged`) per run. Under `auto` report the policy delegation (`source=policy`) as the authority, never as a human approval. Go back with `devkit workflow return --unit <dir> --to <stage>` (voiding later approvals, envelopes). Formal envelopes live under the bundle's `envelopes/` directory ([envelope](references/envelope.md)).

### Tier 2: Operational Playbooks
When the user asks for an operational procedure that is not standard feature development (onboarding, weekly release, database migration, incident recovery), read [playbooks](references/playbooks.md).

---

## 3. Completion & Retrospective Guidance

Read [completion](references/completion.md) when approaching review or completion; reuse its classification in every route. Before G3, run the `collect-feedback` sweep the workflow names (`spec-feedback`; report it as skipped under `[STAGE_POLICY: collect-feedback state=off]`), then present the final change report in the [envelope](references/envelope.md) format (diff scope, checks, assumptions). After G3 authorization (the user's explicit OK under `ask`, or policy delegation under `auto`), run `spec-integrate` and report code-review completion and integration completion as separate facts. PR and worktree choices follow [completion](references/completion.md). When a commit is requested, commit with plain `git commit`; the commit gate runs the staged checks.

The §1 retrospective reminder is optional; it is not a completion or merge gate.
