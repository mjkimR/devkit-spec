---
name: spec
description: Main entry skill for development intent; conversational router and pair programmer. Classifies the work (task-kind, planning-depth, activity-effort), runs Backlog and inline Planning, drives the spec-driven delivery workflows and, on request, operational playbooks.
---

# spec: Conversational Router & Pair Programmer

Use this skill for any development task, feature request, troubleshooting, or operational workflow. `spec` is the **central human-agent router**: it directs each intent to the spec-driven delivery skill or operational playbook that fits, using **progressive disclosure**.

Read `devkit spec policy` before classifying work. Use the effective approval and Git policy with [completion](references/completion.md). Explicit user instructions and authorization already given take precedence; `dev-integration = auto` removes the integration question once the required checks pass, without granting authority for new Git or external actions. A policy command error stops policy-dependent work.

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

### Tier 1: Classification and Planning
Classify the request on the three axes of the spec constitution (`devkit get-context spec`): `task-kind`, then `planning-depth`, then per activity the mode and `activity-effort` ([effort](references/effort.md)). Propose the classification against the criteria and let the user confirm it at `plan-intent`. Backlog work, inline Planning, depth changes and closes follow [classification](references/classification.md). Before any bundle or edit, settle the branch and worktree per `GIT_POLICY` ([worktree](references/worktree.md); a branch without a worktree, an existing branch: [branches](references/branches.md)):

| Classification | Workflow | Planning and start |
| :--- | :--- | :--- |
| `session` × `feature` | `sdd-session-feature` | Inline Planning: agree the intent in the conversation, no Unit. Implement, verify, review at the effort, report in the final response or PR body (`devkit workflow show sdd-session-feature`; there is no unit, so follow its stages in the session). |
| `session` × `bugfix` | `sdd-session-bugfix` | Same, with the expected behavior agreed; write a failing reproduction test first (Red), then fix it (Green), and report both. |
| `spec` × `feature` | `sdd-spec-feature` | Inline Planning on `dev-<slug>`: `devkit spec new <slug> --title "..." --summary "..."`, record `plan-intent`, commit; Development then runs `spec-specify` ➔ `spec-plan` ➔ `spec-tasks` and the later stages. |
| `spec` × `bugfix` | `sdd-spec-bugfix` | Same with `--workflow sdd-spec-bugfix`; Development characterizes the defect (`spec-specify`, bugfix reference), reproduces with a `red` envelope and verifies with a `green` one. |
| `proposal` (either kind) | `sdd-proposal`, then `sdd-spec-<task_kind>` | Backlog: `devkit spec proposal new <slug> --task-kind feature\|bugfix`; the user's confirmation of the draft is `plan-intent`. Planning (its own activity) runs on `plan-<slug>` to `plan-accept`; Development starts on `dev-<slug>` with `devkit spec proposal handoff <slug>` (refused on any other branch) and the `spec-next` skill's post-handoff link check. |
| Spike, independent review, or reconcile verification in an isolated context | Optional support role | `spec-delegate` (`scout`, `challenger`, `reviewer`, `reconciler`), as the `activity-effort` asks. |
| Integration after `dev-integration` authorization | Integration | `spec-integrate`: base integration, re-verify changed parts, confirm reconcile, final checks. |

Read a workflow's stage order, checks, gates (`plan-intent`, `plan-accept`, `dev-integration`; the `exception` stage) and returns with `devkit workflow show --unit <dir>`, or `devkit workflow show <workflow-id>` for work without a bundle. External runners use the same definition; follow it.

Gates: `plan-intent` and `plan-accept` are always the user's decision, recorded after the user's explicit answer only with `devkit workflow answer --unit <dir> --request gate:<gate> --action accept|decline --by user`. `dev-integration` follows `GATE_POLICY`: under `ask` the OK is not recorded but passed as `--given dev-integration` to every later `next`; under `auto` report the policy delegation (`source=policy`), never a human approval. There is no Development direction gate: decide choices inside the agreed intent with the recommended option and record the reason; report a non-blocking improvement as feedback (a follow-up draft proposal is also allowed); stop only for a problem that breaks the agreement (§2 of [classification](references/classification.md)). An approval is never inferred or hand-written; `--given` also asserts a runner check (`lint-ci-clean`, `merged`) per run.

`devkit spec new` and proposal handoff bind the bundle; a bundle made otherwise is bound with `devkit workflow bind --unit <dir> --workflow <id>`. `devkit workflow next --unit <dir>` refuses `WORKFLOW_DRIFT` when the bound schema changed; rebind after review. Go back within Development with `devkit workflow return --unit <dir> --to <stage>` (voiding later approvals, envelopes); never back to Planning. Envelopes live under the bundle's `envelopes/` directory ([envelope](references/envelope.md)); a run's questions, problems, answers and resolutions follow [worker records](references/worker-records.md); a `session` task writes none.

### Tier 2: Operational Playbooks
When the user asks for an operational procedure that is not standard feature development (onboarding, weekly release, database migration, incident recovery), read [playbooks](references/playbooks.md).

---

## 3. Completion & Retrospective Guidance

Read [completion](references/completion.md) when approaching review or completion; reuse its knowledge classification for every task. Before `dev-integration`, run the `collect-feedback` sweep the workflow names (`spec-feedback`; report it as skipped under `[STAGE_POLICY: collect-feedback state=off]`), then present the final change report in the [envelope](references/envelope.md) format (diff scope, checks, assumptions). After `dev-integration` authorization (the user's explicit OK under `ask`, or policy delegation under `auto`), run `spec-integrate` and report code-review completion and integration completion as separate facts. PR and worktree choices follow [git policy](references/git-policy.md). Commits are plain `git commit`; the commit gate runs the staged checks.

The §1 retrospective reminder is optional; it is not a completion or merge gate.
