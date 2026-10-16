---
id: CAP-HARN-agent-guidance
title: Agent Guidance Assets
summary: "Agent guidance deployed by the spec bundle: constitution, skills, instructions, roles, playbooks, templates and optional docs skeleton, including configurable repository-first feedback capture and hygiene."
area: harness
status: active
created_at: 2026-10-13
stories:
  - US-route-development-intent
  - US-adopt-in-an-existing-repository
entrypoints:
  - src/devkit_spec/bundle/bundle.toml
  - src/devkit_spec/bundle/AGENTS.md
  - src/devkit_spec/bundle/guidance/
  - src/devkit_spec/bundle/instructions/
  - src/devkit_spec/bundle/skills/
  - src/devkit_spec/bundle/playbooks/
  - src/devkit_spec/bundle/templates/
  - src/devkit_spec/bundle/seed/
---

# [CAP-HARN-agent-guidance] Agent Guidance Assets

## 1. Summary

The `spec` bundle (`src/devkit_spec/bundle/`, registered through the `devkit.bundles` entry point `spec`) is the
half of devkit-spec an agent reads: it tells every session how spec-driven delivery works, which route a request
takes and which procedure each stage runs. devkit distributes it like any content package
([Manifest Specification](https://github.com/mjkimR/devkit/blob/main/docs/distribution/manifest-spec.md)): `devkit
sync` copies the assets to `.devkit/managed/spec/`, projects skills and role contracts into each agent host's native
directories and writes the guidance pointer into the root `AGENTS.md` block.

## 2. Scope & Boundary

- **In-Scope**: the bundle manifest and presets, the constitution, the two instructions, the guidance pointer, the 12
  `spec*` skills and their references, the two playbooks, the document templates and the docs skeleton; the role
  contracts as deployed assets.
- **Out-of-Scope**:
  - Workflow definitions and role contract semantics: `CAP-DLV-delivery-workflows`.
  - The eight rule assets and their guides: `CAP-GOV-spec-rules`.
  - The commands the guidance invokes: `CAP-HARN-command-mount` and the capabilities it lists.
  - Distribution, projection, context loading and playbook search themselves: devkit.
- **Non-Goals**:
  - **Scope Excluded**: host-specific content. Skills and role contracts are written once, host-neutral; devkit
    projects them per host (`.claude/`, `.agents/`, `.codex/`).
  - **Scope Excluded** (`ADR-docs-skeleton-is-opt-in`): seeding `docs/` by default. An existing `docs/` tree never
    receives files it did not ask for.

## 3. Business Rules & Policies

1. **Context first**: an agent MUST read the constitution (`devkit get-context spec`) once per agent context before
   development work, including work started without a skill, and read each relevant instruction body before the
   action it governs. An instruction never overrides a mandatory check; a conflict is reported, not resolved by
   picking one.
2. **One pointer in `AGENTS.md`**: the bundle adds exactly one line to the root `AGENTS.md` guidance block (the
   `spec-pointer` fragment); everything else is reached through `devkit get-context spec` and the skills.
3. **Managed files are read-only**: files under `.devkit/managed/` and projected agent files are never edited;
   project changes go through `devkit override` or the project's own bundle.
4. **Classification**: the `spec` skill MUST classify work on `task-kind`, then `planning-depth`, then per activity
   the mode and `activity-effort`, after reading `devkit spec policy`, propose the classification for the user to
   confirm at `plan-intent`, and drive the one workflow `sdd-<planning-depth>[-<task-kind>]`
   (`CAP-DLV-delivery-workflows`). `planning-depth` follows what must be settled before implementation, not size.
   Unit depths write `spec.md`, `plan.md` and `tasks.md` before production code; a `session` task writes no Unit,
   envelope, gate record file or reconcile document. The Host raises the depth on its own judgment (`[tool.spec]
   depth_escalation = "ask"`: after the user's confirmation), never lowers it, and a `session` → `spec` raise keeps
   the work by adding a spec Unit; Development never returns to Planning, and a wrong direction is a close (depth
   escalation, supersede or abandon) under a new slug. The mode is chosen per activity: `direct` by default,
   `local-orchestrated` and `cloud-pr` only on the user's instruction. Explicit user instructions take precedence.
5. **Progressive disclosure**: a skill loads only the instructions and references of the current phase; a reference
   names the moment to read it ("Read this before ...").
6. **No session hijacking**: agents MUST NOT unilaterally terminate the user's session or stop active work without
   user direction.
7. **Playbooks on request only**: playbooks are occasional procedures found through `devkit playbook search` when
   the user asks for one; they are not part of routine delivery.
8. **Templates by path**: new documents start from `.devkit/managed/spec/templates/<kind>.md`; seeded files are
   written once where absent and are project-owned afterwards.
9. **Skill names**: every skill of the bundle is named `spec` or `spec-<procedure>`. Rationale:
   `ADR-skills-named-spec`.

## 4. Interfaces & Data Contracts

### 4.1 Manifest and Presets

`bundle.toml`: `schema = 1`, `name = "spec"`, `version`, `default_preset = "core"`, `auto_select = true`.

| Preset | Selection | Assets |
| --- | --- | --- |
| `core` | Automatic on `devkit sync` (`auto_select`) | Instructions, the guidance pointer, the eight rules, `templates`, the 13 skills, the four workflows, the five role contracts, the two playbooks. |
| `docs-skeleton` | Opt-in: `devkit add spec:docs-skeleton` (or `[presets] spec = ["core", "docs-skeleton"]`) | The `docs-skeleton` seed. |

A project opts out of the bundle with `[presets] spec = false` in `.devkit/config.toml`. The constitution
(`AGENTS.md` at the bundle root) is deployed to `.devkit/managed/spec/AGENTS.md` whatever the presets.

| Asset kind | Assets |
| --- | --- |
| `instruction` | `contract-authoring`, `living-spec-writing` |
| `guidance` | `spec-pointer` |
| `rule` | `document-reference`, `id-convention`, `spec-format`, `traceability-link`, `task-coverage`, `spec-lifecycle`, `reconcile-contract`, `document-summary`, `code-entrypoints` (`CAP-GOV-spec-rules`) |
| `skill` | the 13 skills of 4.4 |
| `workflow` | `sdd-session-feature`, `sdd-session-bugfix`, `sdd-spec-feature`, `sdd-spec-bugfix`, `sdd-proposal` |
| `subagent` | `challenger`, `reconcile-reviewer`, `code-reviewer`, `scout`, `planning-worker`, `development-worker` |
| `playbook` | `brownfield-adoption`, `feedback-hygiene` |
| `document` | `templates`; `docs-skeleton` (`seeded = true`, `target = "docs"`) |

### 4.2 Constitution

`devkit get-context spec` returns `{"bundle": "spec", "constitution": <text>, "instructions": [{"path", "header"}]}`.
The constitution's sections:

1. **Context**: read it once per agent context; instructions hold judgment and policy, playbooks occasional
   procedures, rules deterministic checks.
2. **Living Spec and Scope**: `docs/` holds the current contract; feature specs are `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/`;
   namespaces under `docs/packages/<name>/`; English `summary`; references by full ID; Non-Goals and
   `_Boundary:` are the expected scope.
3. **Classification and Workflows**: the three axes, the five workflows, the gates `plan-intent`, `plan-accept` and
   `dev-integration`, no Development direction gate, and the modes per activity; policy read through
   `devkit spec policy`.
4. **Verification and Completion**: compare diff, requirements, check results and Living Spec impact before
   reporting completion; spec Units keep a resolved `reconcile.md`, a `session` task reports in its final response
   or PR body.
5. **Templates and Policy Files**: template paths, policy tables, managed files.

### 4.3 Instructions and Guidance Pointer

| Asset | Read before |
| --- | --- |
| `contract-authoring` | Authoring or reviewing specifications, acceptance criteria, policies, instructions, rules or workflows: RFC 2119 wording, measurable contracts, Non-Goals, examples, policy exceptions. |
| `living-spec-writing` | Authoring, editing or reviewing `docs/` or `specs/`: current-state writing, history placement, completed specs, traceability, summaries, ID references. |

The `spec-pointer` line in the root `AGENTS.md` block: run `uv run devkit get-context spec` once per agent context
before development work; start work with `/spec <intent>`, orient with `/spec-next`; `docs/` is the current-state
Living Spec and `specs/` holds feature specs.

### 4.4 Skills

| Skill | Purpose | devkit-spec commands it runs |
| --- | --- | --- |
| `spec` | Entry router: classify the work, run Backlog and inline Planning, raise the depth and close, drive the workflow; Tier 2 routes operational requests to playbooks. | `policy`, `new`, `proposal new`, `proposal handoff` |
| `spec-next` | Orientation: diagnose the stage of work under way and the next action. | `policy`, `list spec\|proposal\|feedback`, `proposal padr`, `proposal handoff` |
| `spec-specify` | Write `spec.md` (feature or bugfix reference); creates the bundle with `devkit spec new`. | `new`, `list`, `refs`, `search`, `policy` |
| `spec-plan` | Write `plan.md`: design, interfaces, verification plan. | `list`, `refs`, `search` |
| `spec-tasks` | Write `tasks.md` with `_Boundary:` and `_Requirements:`. | `list spec`, `scope update` |
| `spec-review` | Verify the change against the spec, the diff and the checks before completion. | |
| `spec-sync` | Reconcile the change into the Living Spec and resolve `reconcile.md`. | `list`, `refs`, `search`, `proposal new`, `scope update` |
| `spec-integrate` | Integrate after `dev-integration`: conflicts, re-verification, reconcile confirmation, cumulative check, cleanup. | `policy`, `scope sweep`, `proposal prune` |
| `spec-delegate` | Delegate to a role contract as the `activity-effort` asks, record its envelope, validate a worker's committed range and handle its questions and problems. | |
| `spec-orchestrate` | User-invoked `local-orchestrated` mode per activity: one-shot Planning and Development workers in their own worktrees, the Host keeping preparation, validation, questions, problems and integration; a plain instruction returns to `direct`. | `new`, `scope register`, `scope query`, `scope update` |
| `spec-rule` | Author or tune a project rule for `devkit rules` in the project's own bundle. | |
| `spec-feedback` | Record and sweep feedback observations (`specs/<YYYY-MM>/feedback/`). | `list feedback`, `resolve`, `policy` |
| `spec-entrypoints` | Derive capability and story entrypoints from spec bundles, review and apply them. | `entrypoints derive`, `list capability` |

Skill references, each read at the moment it names: `spec/references/completion.md` (completion classification,
policy, reconcile record, checks and commits), `spec/references/envelope.md` (delegation input and return envelope,
final change report), `spec/references/git-policy.md` (worktree, pull request and branch cleanup levels), `spec/references/worktree.md` (task worktree start, work, integrate and finish, leftovers),
`spec/references/playbooks.md` (Tier 2 operational playbook routing),
`spec-next/references/post-handoff.md` (follow-up of `[REWRITTEN]` and `[UNRESOLVED_LINK]` lines),
`spec-next/references/workflow-signals.md` (`devkit workflow next` lines and advisories),
`spec-delegate/references/hosts.md` (spawning a role on each host), `spec-delegate/references/payload.md` (payload
fields and rows per role), `spec-specify/references/feature.md` and
`bugfix.md`, `spec-feedback/references/sweep.md` and `template.md`, `spec-rule/references/config.md` and
`templates.md`.

### Feedback capture policy

`spec-feedback` reads `FEEDBACK_POLICY` from `devkit spec policy` (`CAP-DLV-project-policy`). Repository-owned
rules, skills, instructions, playbooks, workflows, roles, script/CLI tools, templates, overrides and Living Spec
documents are the base targets. `coverage=repo-and-upstream` additionally covers upstream tools used in the
session, including devkit and devkit-spec. Users describe the observation; agents never require tool ownership
classification or frontmatter from them.

- `capture=observed` records concrete observations autonomously; `requested-only` records only explicit requests.
  Enabled workflow sweeps under requested-only write a passing policy-skip envelope without recording observations;
  A `session` task reports the skip without an envelope. Stages switched off produce no sweep envelope.
- Explicit observation and session sweep requests override autonomous capture, coverage and stage restrictions;
  requested sweeps write no envelope.
- `detail=brief` keeps context, observed result or proposed change, assessment and Evidence; `standard` fills the
  kind-specific template. `detailed` adds reproduction, expected/actual results, versions, conditions, attempted
  workarounds and related assets. Missing information is `unknown`; facts are never invented. Detailed capture
  is not constrained by the brief/standard one-minute writing budget.
- `reminder=contextual` suggests an optional sweep when reusable observations warrant it; `off` disables optional
  reminders without changing required stages.

Feedback uses `scope: repo | upstream | unknown`, determined by ownership rather than product name. An asset
developed in this repository is `repo`, even if it is shipped to other repositories; an installed upstream copy
is `upstream`. Uncertain ownership or cross-tool causes use `unknown` and stay eligible for recording. The
observed `target` is separate from the eventual resolution destination. Deduplication covers the open backlog
across all namespaces, including completed specs.

Hygiene determines ownership and proposes local fixes or upstream report drafts; one observation may link several
resolution destinations. External submission requires explicit authorization, and `forwarded` requires an actual
report location. Pending ownership or submission leaves feedback open. Capture never changes feedback status.

### 4.5 Playbooks

| Playbook | Procedure |
| --- | --- |
| `brownfield-adoption` | Adopt spec-driven delivery in a repository that already has code and docs: install, take the baseline, contain legacy Markdown under `docs/materials/_legacy/` and record any deferral as a commented `.devkit/config.toml` entry the user decided, then migrate legacy content through normal work. |
| `feedback-hygiene` | Triage open feedback in one batch: group by target, order by severity and recurrence, promote to rules, playbooks, decisions or spec work, or dismiss or forward, with the user's decision. |

### 4.6 Templates

`.devkit/managed/spec/templates/{capability,story,decision,proposal}.md`: frontmatter with a required English
`summary`, the H1 `# [<ID>] <Title>` convention and the section skeleton of each document kind (`devkit spec proposal
new` and `padr` write the proposal and PADR shapes themselves; `CAP-DLV-proposal-incubation`).

### 4.7 Docs Skeleton

The `docs-skeleton` asset seeds `docs/`, each file written once where absent and then project-owned:

```text
docs/
├── README.md, glossary.md, glossary.yaml     # entry, terms, search synonyms
├── architecture/                              # README.md and arc42 chapters ARCH-01, 03, 05-1, 05-2, 06, 07, 08
├── capabilities/README.md, stories/README.md, decisions/README.md, materials/README.md, proposals/README.md
└── development/setup.md, workflow.md, ci-cd.md
```

The directory READMEs state each directory's naming and authoring conventions and point at `devkit spec list` for
discovery instead of catalog tables.
