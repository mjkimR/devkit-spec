---
name: spec-integrate
description: Integration stage after G3 approval and before merge. Integrate the base branch, resolve conflicts, re-verify only what changed, confirm reconcile.md as resolved and the spec as completed, run the cumulative Git evidence check and CI, and report code-review completion and integration completion separately.
---

# spec-integrate: Post-Approval, Pre-Merge Integration Workflow

Use this skill once G3 (`integration` gate) authorization exists: the user's OK recorded with `devkit workflow answer` or the PR ready state under `ask`, or explicit policy delegation under `auto` after required review and reconciliation. Read `devkit spec policy` and the `spec` skill's `references/completion.md` before proceeding. `devkit workflow next --unit <dir>` names this stage (`integrate`) once the approval is held. Integration is a stage, not a persona: the main-session Developer runs it, or an agent an external runner delegates. Stage definition: `devkit workflow show --unit <dir>` (the workflow the bundle is bound to). Reconciliation contract: the `spec` skill's `references/completion.md`.

---

## 1. Entry conditions and inputs

- Implementation, review and fixes complete; implementation checks passed; G3 authorization held (recorded OK, PR ready state, or reported `integration` policy `auto` delegation shown as `source=policy`).
- Inputs: approved change and its spec directory, the review envelope and check results, docs impact and reconcile targets, the current base branch.
- Base contract: `reconcile.md` is already `resolved` and the spec `completed` before G3. Intermediate commits may have carried a pending record, but that does not satisfy this entry condition or the final cumulative check. If a draft was prepared by the `reconciler` role, it has been reviewed and staged by the Developer.

## 2. Authority

| Scope | Allowed | Not allowed |
| :--- | :--- | :--- |
| Code | Conflict resolution needed to integrate the approved change with the base, and the fixes and verification that resolution requires | New features, refactors, lowering AC, documenting a defect instead of fixing it |
| Docs | Capability, story, architecture and ADR reflection the approved change requires; `reconcile.md` record | Adopting a new policy (separate decision), editing other features' specs |
| Git | Stage agreed paths; `git commit` when authorized (the commit gate runs the staged checks) | Bypass flags (`--no-verify`), `git add .`, force operations |

Trust the prior review: do not restart code review. Re-verify only what conflict resolution and docs reflection changed.

---

## 3. Procedure

With `[GIT_POLICY: worktree=yes]` the task lives in its worktree (the `spec` skill's `references/worktree.md`): Steps 1 to 4 run there, Step 5 merges into the base checkout, and Step 6 cleans up only after the merge is confirmed.

### Step 1: Integrate the base branch
```bash
git -C <base> pull --ff-only
git merge <base-branch>   # the base checkout's branch (it may be ahead of origin); or rebase
```
Resolve conflicts within the approved intent. If a conflict needs a design choice the approval does not cover, stop and return to G2 (`devkit workflow return --unit <dir> --to direction`; hold the PR, report the choice).

### Step 2: Re-verify what changed
- List the paths changed by conflict resolution (`git diff --name-only <pre-merge-head> HEAD`).
- Run the tests and checks that cover those paths; run `spec-review` Step 1 and Step 3 on the changed part only.
- A defect beyond integration scope returns to the Developer (the build stage: `build-verify`, or `fix-verify` in workflow `bugfix`); integration is not reported complete.

### Step 3: Confirm reconciliation
- Re-check `reconcile.md` targets against the new impact after conflict resolution; add targets if resolution touched contracts.
- Apply the docs reflection the approved change requires. Confirm `status: resolved` only when every target is in the comparison diff or has a substantive waiver (never for a required contract mismatch). Confirm `spec.md` is `status: completed` (set by `spec-sync` before G3).
- Shared Living Spec files should be written in integration order; on a shared checkout, serialize docs writing and committing. If the index or HEAD changed during a check, re-run the check.

### Step 4: Final checks
```bash
devkit rules check --ci --base <base-ref>    # cumulative Git evidence, merge-base..HEAD
```
plus the repository CI (tests, static checks). A plain `devkit rules check` does not count. Unresolved reconciliation means no merge.

### Step 5: Report, merge and hand over
Produce the integration result report (the `spec` skill's `references/envelope.md`, section 4) in the conversation, not as a file: base integrated, conflicts resolved, what was re-verified, and two separate facts: code review completed (latest review round or reverify) and integration completed. Run `devkit rules check --ci --base <ref>` locally on the committed head (Step 4) and state the result; it is trusted without a file. Repository CI re-runs it as the final gate (`lint-ci-clean`); `devkit workflow next` shows `[WAITING: runner lint-ci-clean]` until it is declared. Under `pull_request=no` there is no CI run for the branch: after the local cumulative check passes, declare it (`--given lint-ci-clean`) and say so in the report.

Who merges follows the policy. `pull_request=yes`: push the branch and open the PR; the person or the runner merges there under existing merge authority. `pull_request=no`: the executor merges locally, and the G3 authorization is the authority for that merge. With `worktree=yes`, `devkit worktree finish <slug> --merge` (Step 6) performs the fast-forward and pushes the base to its upstream; integrate the base into the branch first when it moved (Step 1). With `worktree=no`, in the base checkout, `git merge --ff-only <branch>` (a merge commit when the base moved) and push the base branch to its upstream (`git push`). Rerun the cumulative check on the result; with no runner to report the merge, declare it yourself (`devkit workflow next --unit <dir> --given lint-ci-clean --given merged`). If head, base or approval changed before merge, return to Step 1.

### Step 6: Clean up after the confirmed merge
- In the base checkout: `devkit worktree finish <slug>` (with `--merge` when `pull_request=no` and the merge is still to be done). It fast-forwards and pushes the base branch to its upstream when asked, removes the worktree, and deletes the branch when `delete_branch=yes`. A refusal (`WORKTREE_DIRTY`, `WORKTREE_UNMERGED`, `WORKTREE_MERGE_NOT_FF`, `WORKTREE_BASE_DIRTY`, `WORKTREE_BASE_BEHIND`, `WORKTREE_BRANCH_UNPUSHED`) stops the step that cannot proceed, and the same command resumes once it is resolved. A push that fails (`push=failed`, `WORKTREE_PUSH_FAILED`) or is rejected (`push=rejected`, `WORKTREE_PUSH_REJECTED`) does not stop the cleanup; `push=no-upstream` means nothing was pushed. Report what could not be removed or pushed and why.
- The finish's post-finish extension removes the task's scope record and empty proposal directories (`[NOTICE]` lines). A failed cleanup is its own warning (`SPEC_SCOPE_TIMEOUT`, `SPEC_CONFIG_INVALID`, `SPEC_PROPOSAL_CLEANUP_FAILED`, ...): run its `[FIX]` (`devkit spec scope sweep --apply` or `devkit spec proposal prune <slug>`) once resolved; on `POST_FINISH_EXTENSION_FAILED` run both.

### Returns
- Design choice not covered by the approval → G2 (`direction`).
- Implementation defect beyond integration scope → Developer (the build stage).
- Retry cap exceeded, tool or execution failure, unresolved semantic conflict → E (`exception`): hold the work, report cause and evidence. Do not create a new task to bypass a cap.

---

## 4. Definition of Done

- [ ] Base integrated; conflicts resolved inside the approved intent.
- [ ] Changed parts re-verified; no full re-review performed.
- [ ] `reconcile.md` resolved with evidence; spec completed.
- [ ] `devkit rules check --ci --base <ref>` and repository CI passed on the final head.
- [ ] Integration result report issued with code-review and integration completion stated separately.
