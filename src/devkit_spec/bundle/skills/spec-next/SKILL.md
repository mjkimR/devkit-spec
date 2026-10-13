---
name: spec-next
description: Entry skill for orientation; inspect repository state and active specifications to navigate and recommend the next concrete engineering action.
---

# spec-next: Engineering Workflow Navigator

Use this skill to orient at session start or choose the next action. It diagnoses state and recommends one concrete step with evidence.

---

## 1. Operating Invariant: No Automatic Execution

> [!IMPORTANT]
> **Pure Recommendation Only (`MUST NOT` auto-execute)**:
> `spec-next` MUST only diagnose state and explain the recommended next step. The agent MUST NOT automatically start implementing, creating files, or executing code without the user's explicit approval.

---

## 2. Diagnosis Workflow

Follow this diagnostic checklist sequentially:

### Step 0: Ask the CLI for the current stage
When a unit directory is known (or Step 2 or 3 names one), run:

```bash
devkit workflow next --unit specs/<YYYY-MM>/<YYYYMMDD>-<slug>     # a spec bundle
devkit workflow next --unit docs/proposals/PROP-<slug>            # a proposal bundle
```

It evaluates the stage schema of the workflow the unit is bound to against the files on disk and prints one tagged line per fact. Use `[STAGE]` as the diagnosed stage in §3, `[UNMET]` as the evidence and `[NEXT_SKILL]` as the skill the stage names; Steps 1-3 add the Git, spec and proposal context the CLI does not see. When the output has any other line (`[GATE]`, `[WAITING]`, `[REQUEST]`, `[DELEGATE]`, `[SKIPPED]`, an error line, ...) or an advisory, read [workflow signals](references/workflow-signals.md) for what it means and what to recommend. For the whole flow run `devkit workflow show --unit <dir>`; the workflow document body holds only gate rules, not the stage list.

### Step 1: Check Working Tree & Git State
Run `git status -s` to inspect uncommitted changes:
- Are there uncommitted files or unstaged changes?
- Are you on a feature branch, a task worktree or the base branch?
- `[GIT_POLICY: worktree=yes]` in `devkit spec policy`: report leftovers from `devkit worktree status`, each as `devkit worktree finish <slug>` or user-authorized removal, per the Leftovers section of the `spec` skill's `references/worktree.md`; never remove any unasked.

### Step 2: Check Active Change Specs (`specs/`)
Run `devkit spec list spec` (completed bundles are left out unless `--history`; follow any `[NEXT_CMD]`), then inspect only the listed directories (`specs/<YYYY-MM>/<YYYYMMDD>-<slug>/`). Completed specs are work history: do not read them for orientation; pass `--history --status completed` only when a task explicitly needs one.
- Is there an active specification in progress?
- Check `tasks.md`: How many tasks are completed vs pending?
- Check `reconcile.md`: prioritize pending required reconciliation after implementation review. Distinguish verified/uncommitted, PR review, reconciliation pending, and integrated states. Spec status `completed` does not prove integration; inspect Git/PR state.

### Step 3: Check Incubating Proposals (`docs/proposals/`)
Run `devkit spec list proposal`:
- Are there proposals in `reviewing` or `accepted` status waiting for handoff?
- Is there an accepted proposal ready for `devkit spec proposal handoff <slug>`?

### Step 4: Check Open Feedback
Run `devkit spec list feedback --status open` and read each item's `severity`.

---

## 3. Decision Matrix & Action Guidance

**Critical feedback first.** If open feedback with `severity: critical` exists, the first recommendation is a feedback hygiene pass on those items now (through the `devkit-playbook` skill when the project has a playbook for it); the stage recommendation below follows as the second item. Open feedback with lower severity is mentioned in one line and left for the next hygiene session.

Match the diagnostic findings to one of the following states. Stage names, entry/exit checks and human gates come from the bound workflow (`devkit workflow show --unit <dir>`); this matrix only maps repository evidence onto those stages.

Map `[STAGE]` ids onto these rows with the stage table in [workflow signals](references/workflow-signals.md); the `intent` and `direction` gates are presented as it describes.

| Diagnosed State | Status Criteria | Recommended Next Action | Associated Skill / Tool |
| :--- | :--- | :--- | :--- |
| **Shaping (Proposal Hand-off)** | Proposal is `status: accepted`, or its direction was chosen and `next` reports it complete | Run handoff to move the proposal into `specs/`, then the post-handoff link check (§3.1) | `devkit spec proposal handoff <slug>` |
| **Shaping (Proposal Incubation)** | Proposal is in `draft` or `reviewing` | Review hypothesis, add research to `materials/`, or draft a PADR; for a spike, delegate `scout`/`challenger` | `devkit spec proposal padr <slug> <title>`, `spec-delegate` |
| **Specification (Drafting)** | Spec folder exists, `spec.md` incomplete | Complete user stories, non-goals, and Given/When/Then criteria | `spec-specify` |
| **Specification (Planning)** | `spec.md` approved, `plan.md` incomplete | Review architecture invariants and define component contracts | `spec-plan` |
| **Specification (Tasks)** | `plan.md` approved, `tasks.md` incomplete | Decompose plan into verifiable tasks with `_Boundary:` and `_Requirements:` | `spec-tasks` |
| **Building (Implementation)** | `tasks.md` has unchecked tasks | Pick the next pending task, respect declared `_Boundary:`, and verify | Implement and run the tests |
| **Building (Verification Review)** | All tasks in `tasks.md` checked | Inspect git diff, check for stray files, verify boundary isolation | `spec-review` |
| **Reconcile (Living Spec Sync)** | Review passed, pending docs sync | Reconcile into `docs/capabilities/`, `docs/stories/`, and write `reconcile.md` | `spec-sync` |
| **Collect feedback (Sweep)** | Reconcile done, no `envelopes/feedback-NN.yaml` with `checks.swept` passing (stage not `[SKIPPED]`) | Sweep the session for unrecorded observations, write the files and the sweep envelope | `spec-feedback` |
| **Awaiting G3 (Integration Approval)** | Review and reconcile done, final change report not yet approved | Present the final change report and wait for the user's OK (recorded with `devkit workflow answer`) or PR ready state | `spec` |
| **Integration (Post-Approval)** | G3 held (recorded OK, PR ready state, or `source=policy`), not yet integrated with base or merged | Integrate base, re-verify changed parts, confirm reconcile, run `devkit rules check --ci --base <ref>`, report | `spec-integrate` |
| **Idle / Clean Working Tree** | No active specs, working tree clean | Ready for new feature request, bugfix, or proposal brainstorming | `/spec <intent>` |

### 3.1 Post-handoff link check

Run it immediately after every `devkit spec proposal handoff <slug>`, in the same change: [post-handoff link check](references/post-handoff.md) (fix the `[UNRESOLVED_LINK]` lines, reread the rewritten references, search for leftover links to the deleted bundle, run `devkit rules check`).

---

## 4. Output Standard

Provide a concise, high-density summary to the user:

```markdown
### Current Status & Next Action Diagnosis

- **Active Stage**: Building (Implementation)
- **Active Feature**: `SPEC-feature-name` (specs/2026-10/20261004-feature-name/)
- **Progress**: 2 / 5 tasks completed in `tasks.md`

#### Recommended Next Step:
**Implement Task 2.3: Wire CLI handler**
- **Boundary**: `src/app/cli.py`
- **Verification**: the project's test command

*(Type `proceed` or give instructions to begin this task)*
```
