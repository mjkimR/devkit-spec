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

## 3. Routes and Workflows

`spec` chooses the route by uncertainty, contract impact and risk:

- **Route 1, S-Lane**: low uncertainty and low risk, done within the session; workflow `s-lane`, no planning files.
- **Route 2, direct delivery**: known direction, contract impact; workflow `direct-delivery`, or `bugfix` for a
  defect with contract impact or uncertainty.
- **Route 3, incubated**: high uncertainty, local review; a proposal (`devkit spec proposal new`), then handoff to a
  spec (`devkit spec proposal handoff`). **Route 4** is the same with team review through a pull request. Both use
  workflow `incubated-delivery` until handoff.

Route 2 and above write `spec.md`, `plan.md` and `tasks.md` before production code. Stage order, checks, gates and
returns come from the workflow definitions, never an ad-hoc sequence: `devkit workflow next --unit <dir>` diagnoses the
stage, `devkit workflow show --unit <dir>` shows the definition.

Read `devkit spec policy` before routing, gate and Git decisions. `ask` gates wait for the user's answer: `intent` and
`direction` are recorded with `devkit workflow answer --by user`, the `integration` OK is asserted with `--given
integration` on the `devkit workflow next` runs after it (`ADR-integration-approval-asserted`); `auto` delegates the
decision within existing authority and the assumptions are reported. Records name the authority (`user` or `policy`)
and never carry the conversation: no quotes, paraphrase or dates of it in decision notes, envelopes, assumptions or
feedback; a decline note states the reason as a decision. Neither grants new commit, merge, publication or
deletion authority, and the intent gate always needs the user's intent. Report stages the policy switched off as
skipped. Before formal worktree work read the `spec` skill's `references/worktree.md`; before completion or Git
actions its `references/completion.md`. Explicit user instructions take precedence.

Sessions run in direct mode: the host implements. The user-invoked `spec-orchestrate` skill switches a session to
orchestration mode, where the host coordinates worker subagents building independent units in their own worktrees,
until the user returns it to direct mode.

## 4. Verification and Completion

Every route compares the final diff, the agreed requirements, the check results and the Living Spec impact before
reporting completion (`spec-review`, `spec-sync`). Fix implementation defects rather than rewriting documentation to
endorse them. Reconcile behavior, capability and constraint changes into the affected Living Spec, and recheck after
further changes.

Formal specs keep a resolved `reconcile.md` and stay in place when completed; S-Lane needs no planning or reconcile
file but reports its document-impact reasoning. `devkit rules check` runs the spec rules; commits run them through the
commit gate (`devkit rules check --staged`), and CI runs `devkit rules check --ci --base <ref>`. Completion, commit,
integration and ending the session are separate events.

## 5. Templates and Policy Files

- Templates for new documents: `.devkit/managed/spec/templates/{capability,story,decision,proposal}.md`.
- Project policy lives in `.devkit/config.toml` (`[workflow.approvals]`, `[workflow.stages]`, `[worktree]`,
  `[tool.spec]`); read it through `devkit spec policy`, never by parsing the file.
- Managed files under `.devkit/managed/` are never edited; project changes go through `devkit override` or the
  project's own bundle.
