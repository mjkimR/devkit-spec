# Spec-Driven Delivery

This project develops through spec-driven delivery: `docs/` is the durable Living Spec, feature specs in `specs/`
carry each change, and completed work is reconciled into `docs/` before it is reported done. Start development work
with the `spec` skill (`/spec <intent>`); `/spec-next` orients in work already under way. Agents MUST NOT unilaterally
terminate the user's session.

## 1. Context

- Read this guide once per agent context before development work, including work started without a skill.
- The instructions listed below come with it: read each relevant body before the action it governs. Instructions hold
  judgment and policy, playbooks (`devkit-playbook`) occasional procedures, rules (`devkit rules`) deterministic
  checks. An instruction never overrides a mandatory check; report a conflict instead of picking one.
- Spec-driven delivery assumes good-faith work with possible mistakes, omissions and context loss. A new rule or check
  addresses an identifiable failure or a reusable practice at proportionate cost.

## 2. Living Spec and Scope

- `docs/` holds the current contract: capabilities, stories, architecture and decisions. Rewrite changed statements
  in place; history belongs in Git, ADRs and dated materials. Temporary checklists and task lists belong in `specs/`.
- A feature spec is `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` with `spec.md`, `plan.md` and `tasks.md`. Completed specs stay
  as work history; read current contracts and active specs (`devkit spec list spec`) before drafting new work.
- In a monorepo, packages may keep their own Living Spec under `docs/packages/<name>/` (namespaces). `list` and
  `search` default to the current directory's namespace plus the global documents; IDs, `resolve` and `refs` are
  repository-wide. Use `--all-namespaces` for cross-package impact.
- Documents carry an English `summary` in their frontmatter (one or two sentences; titles and bodies may use any
  language): `devkit spec search` finds documents by it.
- Refer to ID-bearing documents by full ID (`` `CAP-...` ``), never by Markdown path. `devkit spec resolve <ID>` gives
  the path, `devkit spec refs <ID> --direction out|in` the references.
- Agents MUST NOT implement Non-Goals or add unrequested features, refactors or speculative scope; unstated assumptions
  are not permissions. A lasting policy change or an exception to a MUST needs an ADR; a one-off exception within the
  approved scope is stated in the review or final report.
- A task's `_Boundary:_` is the expected scope: explain a necessary extension in the report. Write boundaries given to
  a delegated role are strict.

## 3. Classification and Workflows

Work is classified on three axes, by the agent against the criteria and confirmed by the user at `plan-intent`:

- **`task-kind`**: `feature` (new or changed behavior, the default) or `bugfix` (a defect against an agreed contract:
  reproduce first, Red then Green).
- **`planning-depth`**: what must be settled before implementation, not size. `session`: nothing (no design choice,
  no contract impact, verifiable in the session), no Unit. `spec`: the contract, direction clear; a spec Unit.
  `proposal`: the direction, options to explore; a proposal Unit, Planning, then handoff to a spec.
- **`activity-effort`**: `low`, `medium` (default) or `high`, chosen per activity; it sets how thorough review and
  verification are, never lowers gates, exit checks or `required` policies.

The workflow is `sdd-<planning-depth>[-<task-kind>]`: `sdd-session-feature`, `sdd-session-bugfix`, `sdd-spec-feature`,
`sdd-spec-bugfix` and `sdd-proposal` (handed off to `sdd-spec-<task_kind>`). A team review is `proposal` depth plus PR
policy. The axes are not stored: the Unit's kind and bound workflow show them. Depth is raised by the Host
(`[tool.spec] depth_escalation`), never lowered except by a proposal's handoff, and never by a worker.

Unit depths write `spec.md`, `plan.md` and `tasks.md` before production code. Stage order, checks, gates and returns come
from the workflow definitions, never an ad-hoc sequence: `devkit workflow next --unit <dir>` diagnoses the stage,
`devkit workflow show --unit <dir>` shows the definition. A `session` task follows its definition in the session and
creates no Unit, envelope, gate record file or reconcile document.

Read `devkit spec policy` before classification, gate and Git decisions. `plan-intent` (goal, scope, verification,
expected behavior for a bugfix, `task-kind` and `planning-depth`) and `plan-accept` (a proposal's direction) are always
the user's and are recorded with `devkit workflow answer --by user`; `dev-integration` follows its policy: under `ask`
the user's OK is asserted with `--given dev-integration` on the `devkit workflow next` runs after it
(`ADR-integration-approval-asserted`), under `auto` it is delegated once the path's review, checks and reconcile pass.
There is no Development direction gate: inside the agreed intent choices are made with the recommended option and
recorded; only a problem that breaks the agreement stops the work. Records name the authority (`user` or `policy`) and
never carry the conversation: no quotes, paraphrase or dates of it in decision notes, envelopes, assumptions or
feedback; a decline note states the reason as a decision. Neither grants new merge, publication or deletion authority.
Report stages the policy switched off as skipped. Before formal worktree work read the `spec` skill's
`references/worktree.md`; before completion or Git actions its `references/completion.md`. Explicit user instructions
take precedence.

The mode is chosen per activity of a slug: `direct` (the default: the Host implements), `local-orchestrated` (the Host
coordinates one-shot workers in their own worktrees; user-invoked `spec-orchestrate`) or `cloud-pr` (a Cloud Agent
runs it from a PR). Heavier modes are the user's choice; a `session` task always runs in `direct` or the `cloud-pr`
general PR path.

## 4. Verification and Completion

Every task compares the final diff, the agreed requirements, the check results and the Living Spec impact before
reporting completion (`spec-review`, `spec-sync`). Fix implementation defects rather than rewriting documentation to
endorse them. Reconcile behavior, capability and constraint changes into the affected Living Spec, and recheck after
further changes.

Spec Units keep a resolved `reconcile.md` and stay in place when completed; a `session` task writes no planning or
reconcile file and reports the change, effort, review result, verification and remaining constraints in its final
response or PR body (a needed Living Spec change raises it to `spec`). `devkit rules check` runs the spec rules;
commits run them through devkit's `rules-check` commit gate (on by default; `devkit rules check --staged` reproduces
it), and CI runs `devkit rules check --ci --base <ref>`. Completion, commit, integration and ending the session are
separate events.

## 5. Templates and Policy Files

- Templates for new documents: `.devkit/managed/spec/templates/{capability,story,decision,proposal}.md`.
- Project policy lives in `.devkit/config.toml` (`[workflow.approvals]` with `dev-integration` only,
  `[workflow.stages]`, `[worktree]`, `[tool.spec]`); read it through `devkit spec policy`, never by parsing the file.
- Managed files under `.devkit/managed/` are never edited; project changes go through `devkit override` or the
  project's own bundle.
