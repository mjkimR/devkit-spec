# Classification, Backlog, depth changes and close

Read this when you classify a request, run Backlog or inline Planning, find that a task's depth is wrong, or must end Development without a merge.

## 1. Classify (Backlog)

Decide in this order and propose the result; the user confirms `task-kind` and `planning-depth` at `plan-intent`, `activity-effort` when the activity starts.

| Axis | Values | Criterion |
| --- | --- | --- |
| `task-kind` | `feature` (default), `bugfix` | `bugfix` only for a defect against an agreed contract; it adds the characterization (spec depth) and the Red then Green evidence. Provisional until `plan-accept` or the spec Unit's creation. |
| `planning-depth` | `session`, `spec`, `proposal` | What must be settled before implementation, not size. Nothing (no design choice, no contract impact, verifiable in the session): `session`. The contract, with a clear direction: `spec`. The direction, with options to compare: `proposal`. Large but clear work is `spec`; small work whose direction is open is `proposal`. |
| `activity-effort` | `low`, `medium` (default), `high` | How thorough this activity's review and verification are; propose another value only when the activity needs it. Never lowers gates, exit checks or `required` policies. |

- **Backlog is `direct`.** Manage the GitHub issue and milestone, classify, and for `proposal` depth add the draft (`devkit spec proposal new <slug> --task-kind ... [--milestone ...]`) and ask the user to confirm it: that confirmation is `plan-intent`, recorded with `devkit workflow answer --unit docs/proposals/PROP-<slug> --request gate:plan-intent --action accept --by user`.
- **A request that must be split is not classified yet.** Split it in Backlog into drafts or `session`/`spec` issues; a draft you do not split now carries `needs_decompose: true` (`--needs-decompose`). Planning never starts from such a draft, and one proposal hands off to exactly one spec.
- **Draft proposals may be added from any activity** without policy limits (Backlog work is outside the worktree and PR `required` policies); they land in the current checkout. A follow-up found during other work is reported as feedback by default; adding a draft is also allowed. Backlog edits, splits or deletes only a `draft` whose `plan-<slug>` branch does not exist: run `devkit spec proposal check <slug>` before each such change (fetch first to see a branch made elsewhere) and stop on `SPEC_PROPOSAL_IN_PLANNING`. A listing that shows it `reviewing` is no check.

## 2. Inline Planning (`session`, `spec`) and the problem rule

- **`spec`**: start the `dev-<slug>` branch (`devkit worktree start dev-<slug>`, with `--no-worktree` when `GIT_POLICY` needs no worktree; [branches](branches.md)), `devkit spec new <slug>` on it (`--workflow sdd-spec-bugfix` for a bugfix; on any other branch it is refused, `SPEC_WRONG_BRANCH`), agree the intent with the user and record `plan-intent`, commit. That committed state is Development's input; handing it to a worker or a cloud run passes the branch and the Unit on (`--existing-branch dev-<slug> --unit <dir>`, [branches](branches.md) §3).
- **`session`**: agree the intent in the conversation, no Unit. With a PR the work runs on `dev-<slug>`, else on the current branch (on the base under `ask` integration: `dev-<slug>` or the OK first). A `session` task runs in `direct` or the `cloud-pr` general PR path only; in `local-orchestrated` handle it yourself in `direct`.
- **Development decides inside the agreement.** A choice inside the agreed goal, scope and contract is made with the recommended option and recorded. Only a problem that cannot be solved without changing the agreement, or that cannot be solved at all, stops the work: a worker records it (`--problem`, `--tried`, `--recovery`) in its `worker` envelope, commits (an emergency commit, which alone may use `--no-verify`) and ends ([worker records](worker-records.md)); a `session` task reports it in the conversation or the cloud run's problem report and does not integrate. You decide within the approved scope, with strong autonomy: fix, revert (`git revert`, never reset), finish it yourself or hand it to a new worker; whoever fixes it records a `resolution` naming the problem. A problem you find yourself while validating a worker's range goes in your own `worker` envelope the same way. A change of scope needs the user and a close (§4).

## 3. Raising the depth

Raising is yours to decide (`[ROUTING_POLICY: depth_escalation=auto]`); under `ask` confirm it with the user first. Lowering never happens except through a proposal's handoff. Workers and Cloud Agents never raise it: they report the need as a problem.

- Before Development: change the classification only.
- **`session` → `spec` during Development** keeps the work: in the current work environment add a spec Unit (`devkit spec new <slug>`, on `dev-<slug>`; without that branch, create and switch to it in this checkout with `devkit worktree start dev-<slug> --no-worktree`, which keeps the uncommitted work), record the agreed intent and the work so far, and continue from the workflow's next stage. No close, no new slug, no new worktree; the agreement is asked again only if goal or scope change. Record the spec's `plan-intent` on the strength of the session's approval: `devkit workflow answer --unit <dir> --request gate:plan-intent --action accept --by user --note "approved in the session; depth session -> spec: <reason>"` (under `depth_escalation = ask`, name the user's confirmation too). Raise it when a lasting design record, a contract change or a Living Spec change is needed; a higher review effort alone never raises the depth.
- **To `proposal`** (the direction must be decided first) is a close by depth escalation (§4).

## 4. Close (end Development without a merge)

Development never returns to Planning. Only a party that can talk to the user closes; a worker or Cloud Agent leaves a problem instead.

| Close | When | Steps | Who decides |
| --- | --- | --- | --- |
| Depth escalation | A `session` or `spec` task needs its direction decided first | Add a draft proposal under a **new slug**, carrying what the attempt learned in its `materials/`; close its dev PR and drop its branch if it has them | You (`depth_escalation = ask`: the user confirms) |
| Supersede | An accepted proposal's direction is wrong | Add a draft proposal under a new slug with `--supersedes PROP-<old>` and the attempt's material in `materials/`; delete the old accepted proposal from the base in the same commit; close the dev PR and drop the branch | The user: it reverses `plan-accept` |
| Abandon | The accepted work is dropped | Write a rejection ADR and delete the accepted proposal from the base; close the dev PR and drop the branch | The user |

- **Drop the branch with `devkit worktree finish dev-<slug> --discard`** from the base checkout, once what it learned is copied out: it removes the worktree (refused while it has uncommitted changes, never forced), deletes the unmerged branch (`git branch -D`, the only place it is allowed) and releases the task's scope record. The decider in the table is its authority; no other path force-deletes a branch. Close the remote branch and PR yourself (`gh pr close`, `git push <remote> --delete dev-<slug>`).
- A close commit is Backlog work: commit it to the base directly (no worktree or PR policy).
- A new draft starts over: `plan-intent` is asked again in Backlog and Planning runs anew.
- A rejected proposal (Planning's rejection, status only, the user's reason in the commit message) is cleaned up by a later hygiene pass: write the rejection ADR outside the proposal directory, referencing the proposal and the rejection commit, and delete the proposal in the same commit. `devkit rules check -p hygiene` lists each one still waiting (`SPEC_PROPOSAL_REJECTED_PENDING`). Questions still open from the last Planning run are closed in the rejection commit with an `answer` envelope giving each `choice: null` and the rejection as its decision; otherwise they hold the Planning branch's merge. The same closing answer ends a Planning returned to Backlog for decomposition.
