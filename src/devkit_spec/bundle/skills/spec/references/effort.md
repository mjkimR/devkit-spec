# activity-effort

How thoroughly one activity of a slug is done: `low`, `medium` (the default) or `high`, chosen when the activity starts and passed to its executor as run input, never stored in the Unit or the configuration. Backlog and inline Planning have no effort: Backlog's work is fixed and inline Planning is the intent agreement only.

**Always propose it.** When an activity starts, state the effort you propose and why, and let the user confirm it; never apply the default silently. A proposal's Planning effort is proposed in its `plan-intent` request ([classification](classification.md) §1). `medium` is the default proposal. Propose `high` when the work reverses an upstream or accepted decision (a strategy-layer rule, an ADR, an accepted proposal), creates a contract or a document kind, or affects more than one package (devkit, devkit-spec, autohub, or several packages of a monorepo); propose `low` only for work whose direction leaves nothing to criticize.

| Activity | `low` | `medium` | `high` |
| --- | --- | --- | --- |
| Planning (`proposal`) | questions only; no `scout` or `challenger` | one `challenger` pass always; `scout` when the direction needs evidence | two or more options compared, `challenger` required, re-review after changes |
| Development (`session`) | the author's self-review | one `reviewer` subagent pass, then reverification of the fixes | `reviewer` subagent review, re-review after the fixes |
| Development (Unit path) | the author's self-review and self-checked reconcile | one `reviewer` pass plus reverification of the fixes; the reviewer also checks the reconcile result | `reviewer` with re-review after fixes; a separate `reconciler` verifies the reconcile independently |

Rules:

- **The floor stays.** Gates, the workflow's exit checks and `required` policies hold at every effort; effort sets only the optional procedure above them. On the Unit path the review envelope is recorded before `dev-integration` even at `low`; a `session` task reviews at every effort but records no envelope.
- **Review and evidence are separate.** `medium` and `high` always review in a subagent, for neutrality: a context other than the author's. A worker runs it nested (Host → worker → reviewer); a `session` task's Host or Cloud Agent runs it directly. The reviewer returns its fields as a message: on the Unit path the caller records them as the envelope, and a `low` self-review says so in its envelope; a `session` task reports the review method and result in its final response or PR body.
- **Reconcile is Unit-path only.** At every effort the implementer writes the Living Spec reflection and `reconcile.md` and completes them. The check is recorded by the implementer as a `reconcile-check` envelope (its self-check at `low`, the reviewer's returned check at `medium`, the `reconciler`'s at `high`); `living-spec-draft` exits only on the latest one with no open finding. A finding is fixed in the reconcile and checked again, never by reopening the review.
- **Effort and integration policy are independent.** `dev-integration = auto` applies at `low` too, once the path's self-review, required checks and completion conditions hold; `low` adds no human approval.
- **Where it is recorded.** A worker writes the effort it applied in its `worker` envelope (`--effort`); a `session` task reports it in its final response or PR body. Model and reasoning settings are outside this axis.
