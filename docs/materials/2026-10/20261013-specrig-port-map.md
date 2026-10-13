---
id: MAT-specrig-port-map
title: specrig port map
summary: Dated record of where each specrig component went when specrig was rebuilt on devkit, whether into devkit, into the spec bundle or devkit spec commands of devkit-spec, or dropped.
created_at: 2026-10-13
---

# [MAT-specrig-port-map] specrig port map

> **Purpose**: a record, as of 2026-10-13, of the component mapping behind `ADR-rebuild-specrig-on-devkit`. specrig
> (the Go predecessor, private repository `mjkimR/specrig`) is the reference for behaviour being ported; this table is
> where each of its components went. The current contracts are the capabilities, not this record.

"devkit" means the capability already exists in devkit and nothing is ported. "Dropped" means no successor.

## 1. Commands and Engines

| specrig | Destination | Notes |
| --- | --- | --- |
| `init`, `installation`, `project`, release bootstrap, `installation.json` schema 4 | devkit distribution | `devkit sync`, `add`, `remove`, `status`, the receipt, projections, overrides. `.specrig/{managed,local,overrides}` become `.devkit/managed`, in-repository bundles and `.devkit/overrides`. |
| `lint` and the Go rule runner | devkit rules | `devkit rules check` (`--staged`, `--ci`). |
| SDD rules id-convention, spec-format, spec-lifecycle, task-coverage, traceability-link, document-reference | `spec` bundle, `kind = "rule"` | Ported from Go to Python; the document index they share is `devkit_spec.documents` (`ADR-rules-implemented-in-the-package`). |
| SDD rule workflow-shared-stage | devkit workflow | `devkit workflow validate` reports `SHARED_STAGE_MISMATCH`. |
| (new in devkit-spec) | `spec` bundle, `kind = "rule"` | `RULE-reconcile-contract`, `RULE-code-entrypoints`, `RULE-document-summary`. |
| RULE-markdown-link, RULE-file-length | devkit | Built-in rules. |
| RULE-rule-implementation | dropped | It checked the layout of Go rule modules. |
| skill-authoring preset, RULE-skill-document-size | devkit `authoring` bundle | |
| git-commits preset | devkit `git-commits` bundle | |
| github-milestones preset | `spec` bundle preset (planned) | SDD-specific; not shipped as of this record. |
| `commit` | devkit gate | `verify-commands` running `devkit rules check --staged`. |
| `workflow` (`next`, `show`, `bind`, `validate`, `checks`, `envelope`) | devkit workflow | |
| Workflows s-lane, direct-delivery, bugfix, incubated-delivery | `spec` bundle, `kind = "workflow"` | specrig-specific checks become devkit check primitives or declared checks (`CAP-DLV-delivery-workflows`). |
| `worktree start`, `finish`, `status` | devkit worktree | |
| Scope comparison, registry and journal (`scope`) | `devkit spec scope` | Same contract with a Python local file adapter; the skills call `update`, `release` and `sweep` where specrig's `workflow next --scope-ack` and `worktree finish` did, and `proposal handoff` registers in a task worktree (`ADR-scope-maintenance-through-skills`). |
| Proposal cleanup on `worktree finish` | `devkit spec proposal prune` | Run by the skills in the base after `devkit worktree finish`; removes the empty proposal directories a merged handoff left. |
| `git.worktree` route policy | `spec` bundle guidance, `[tool.spec] worktree` | Which routes run in a worktree. |
| `config show`, `.specrig/config.yml` | `devkit spec policy`, `.devkit/config.toml` | Approvals to `[workflow.approvals]` (gates `intent`, `direction`, `integration`), the feedback sweep to `[workflow.stages]`, `pull_request` and branch cleanup to `[worktree]`, `git.worktree` to `[tool.spec]` (`ADR-policy-in-the-tool-spec-table`). |
| `list`, `resolve`, `refs` (document catalog) | `devkit spec list`, `resolve`, `refs` | |
| `search` (BM25, go-potion dense, hybrid) | `devkit spec search` on `devkit.search` | devkit-spec keeps the search policy: scopes, namespaces, exact-ID pinning, glossary. |
| `proposal new`, `padr`, `handoff` | `devkit spec proposal`, `devkit spec new` | Handoff is its own cross-layout move (`ADR-handoff-workflow-key`); `devkit spec new` creates a spec bundle without a proposal. |
| `entrypoints derive` | `devkit spec entrypoints derive` | |
| `list feedback`, feedback capture | `devkit spec list feedback`, the `spec-feedback` skill | Feedback documents are indexed like any document; `list --where` filters by `severity`, `scope` or `kind`, and feedback is ordered by severity (`SPEC-feedback-list-filters`). |
| `list playbooks`, `playbook new` | devkit `devkit playbook search` | Authoring a playbook needs no command. |
| `cache`, `serve`, `sync`, `reading` | dropped | The derived-data cache, the removed web viewer, and two commands specrig never implemented. |

## 2. Agent Assets

| specrig | Destination | Notes |
| --- | --- | --- |
| Skills `sr`, `sr-*` | `spec` bundle, `kind = "skill"`, renamed `spec`, `spec-*` | `sr-spec` became `spec-specify` (`ADR-skills-named-spec`); rewritten against devkit and `devkit spec` commands. |
| Subagents challenger, reconciler, reviewer, scout | `spec` bundle, `kind = "subagent"` role contracts | |
| Instructions contract-authoring, living-spec-writing | `spec` bundle, `kind = "instruction"` | |
| Instruction guidance-architecture | devkit | Superseded by devkit's resource taxonomy. |
| Templates capability, story, decision, proposal, feedback, playbook | `spec` bundle, `kind = "document"` | capability, story, decision and proposal are ported (the decision template gains the frontmatter real ADRs carry); the feedback template lives in the `spec-feedback` skill (`references/template.md`); playbook is devkit's. |
| `template/docs` skeleton, `glossary.yaml` | `spec` bundle, seeded `document` `docs-skeleton` in its own preset | Opt-in (`ADR-docs-skeleton-is-opt-in`); `glossary.yaml` moved to `docs/glossary.yaml`, the search synonyms of `devkit spec search`. |
| Playbooks brownfield-adoption, feedback-hygiene | `spec` bundle, `kind = "playbook"` | |
| Playbooks harness-maintenance, cache-ops | dropped | Installation upkeep is devkit's; the cache is gone. |
| Managed `SPECRIG:START/END` block in `AGENTS.md` | `guidance` fragments | devkit writes the one `DEVKIT:START/END` block. |
| Constitution `.specrig/AGENTS.md` | `spec` bundle `AGENTS.md` | Returned by `devkit get-context spec`. |
