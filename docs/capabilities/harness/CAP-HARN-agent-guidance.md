---
id: CAP-HARN-agent-guidance
title: Agent Guidance Assets
summary: The agent-facing content of the spec bundle that devkit sync deploys (constitution, instructions, the AGENTS.md guidance pointer, the spec* skills and their references, role contracts, playbooks, document templates and the opt-in docs skeleton) and the core and docs-skeleton presets that select it.
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
4. **Routing**: the `spec` skill MUST choose the route by uncertainty, contract impact and risk, after reading
   `devkit spec policy`, and drive one workflow per route (`CAP-DLV-delivery-workflows`). Route 2 and above write
   `spec.md`, `plan.md` and `tasks.md` before production code. Explicit user instructions take precedence.
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
| `core` | Automatic on `devkit sync` (`auto_select`) | Instructions, the guidance pointer, the eight rules, `templates`, the 12 skills, the four workflows, the four role contracts, the two playbooks. |
| `docs-skeleton` | Opt-in: `devkit add spec:docs-skeleton` (or `[presets] spec = ["core", "docs-skeleton"]`) | The `docs-skeleton` seed. |

A project opts out of the bundle with `[presets] spec = false` in `.devkit/config.toml`. The constitution
(`AGENTS.md` at the bundle root) is deployed to `.devkit/managed/spec/AGENTS.md` whatever the presets.

| Asset kind | Assets |
| --- | --- |
| `instruction` | `contract-authoring`, `living-spec-writing` |
| `guidance` | `spec-pointer` |
| `rule` | `document-reference`, `id-convention`, `spec-format`, `traceability-link`, `task-coverage`, `spec-lifecycle`, `reconcile-contract`, `document-summary`, `code-entrypoints` (`CAP-GOV-spec-rules`) |
| `skill` | the 12 skills of 4.4 |
| `workflow` | `s-lane`, `direct-delivery`, `bugfix`, `incubated-delivery` |
| `subagent` | `challenger`, `reconciler`, `reviewer`, `scout` |
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
3. **Routes and Workflows**: Route 1 S-Lane (`s-lane`), Route 2 direct delivery (`direct-delivery`, or `bugfix`),
   Routes 3 and 4 incubated (`incubated-delivery` until handoff); gate policy read through `devkit spec policy`.
4. **Verification and Completion**: compare diff, requirements, check results and Living Spec impact before
   reporting completion; formal specs keep a resolved `reconcile.md`.
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
| `spec` | Entry router: classify intent, choose the route, drive the workflow; Tier 2 routes operational requests to playbooks. | `policy`, `new`, `proposal new`, `proposal handoff` |
| `spec-next` | Orientation: diagnose the stage of work under way and the next action. | `policy`, `list spec\|proposal\|feedback`, `proposal padr`, `proposal handoff` |
| `spec-specify` | Write `spec.md` (feature or bugfix reference); creates the bundle with `devkit spec new`. | `new`, `list`, `refs`, `search`, `policy` |
| `spec-plan` | Write `plan.md`: design, interfaces, verification plan. | `list`, `refs`, `search` |
| `spec-tasks` | Write `tasks.md` with `_Boundary:` and `_Requirements:`. | `list spec`, `scope update` |
| `spec-review` | Verify the change against the spec, the diff and the checks before completion. | |
| `spec-sync` | Reconcile the change into the Living Spec and resolve `reconcile.md`. | `list`, `refs`, `search`, `proposal new`, `scope update` |
| `spec-integrate` | Integrate after G3: conflicts, re-verification, reconcile confirmation, cumulative check, cleanup. | `policy`, `scope sweep`, `proposal prune` |
| `spec-delegate` | Delegate a stage to a role contract and record its envelope. | |
| `spec-rule` | Author or tune a project rule for `devkit rules` in the project's own bundle. | |
| `spec-feedback` | Record and sweep feedback observations (`specs/<YYYY-MM>/feedback/`). | `list feedback`, `resolve`, `policy` |
| `spec-entrypoints` | Derive capability and story entrypoints from spec bundles, review and apply them. | `entrypoints derive`, `list capability` |

Skill references, each read at the moment it names: `spec/references/completion.md` (completion classification,
policy, reconcile record, checks and commits), `spec/references/envelope.md` (delegation input and return envelope,
final change report), `spec/references/worktree.md` (task worktree start, work, integrate and finish, leftovers),
`spec/references/playbooks.md` (Tier 2 operational playbook routing),
`spec-next/references/post-handoff.md` (follow-up of `[REWRITTEN]` and `[UNRESOLVED_LINK]` lines),
`spec-next/references/workflow-signals.md` (`devkit workflow next` lines and advisories),
`spec-delegate/references/hosts.md` (spawning a role on each host), `spec-specify/references/feature.md` and
`bugfix.md`, `spec-feedback/references/sweep.md` and `template.md`, `spec-rule/references/config.md` and
`templates.md`.

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
