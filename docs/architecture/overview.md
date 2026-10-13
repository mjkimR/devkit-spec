# Architecture Overview

devkit-spec adds spec-driven development to [devkit](https://github.com/mjkimR/devkit). It is the successor of specrig: the same development model (a durable Living Spec in `docs/`, ephemeral feature specs in `specs/`, routed delivery workflows and reconciliation before completion), rebuilt as a layer on devkit instead of a standalone Go CLI.

## 1. Two Halves, One Package

| Half | Entry point | Reaches the project through |
| --- | --- | --- |
| The `spec` bundle (`src/devkit_spec/bundle/`) | `devkit.bundles`: `spec = "devkit_spec"` | `devkit sync`: managed copies, projected skills and subagents, seeded files, guidance fragments, rules, workflows and workflow checks, recorded in `.devkit/installation.json` |
| The `devkit spec` commands (`src/devkit_spec/cli.py`) | `devkit.commands`: `spec = "devkit_spec.cli:cli"` | devkit's root command group, which imports the module only when `devkit spec` runs ([Command Plugins](https://github.com/mjkimR/devkit/blob/main/docs/architecture/command-plugins.md)) |

The bundle declares `auto_select`: installing the package deploys its default preset `core` on the next `devkit sync`; a project opts out with `[presets] spec = false`.

**Why one executable.** Agents, hooks and CI already run `uv run devkit ...` from the project environment. Mounting `devkit spec` there gives devkit-spec devkit's startup path (lazy command loading), its output contract and its error boundary, and keeps one place to look for every command. A separate `devkit-spec` executable would duplicate the root group and invite drift between the two.

**Why no binary.** specrig shipped a Go executable per platform and built consumer rules with `go build`. devkit-spec is a pure Python wheel (`py3-none-any`): no platform builds, no Go toolchain in consumer projects, and no macOS runner minutes in this private repository's CI.

## 2. Boundary with devkit

devkit knows nothing about spec-driven development; devkit-spec knows nothing about distribution, rule evaluation, workflow state, commit hooks or ranking. When devkit-spec needs a generic capability, it is added to devkit first and used through its public surface. devkit-spec keeps:

- the document model: document kinds and their directories, the ID grammar, frontmatter fields, references between documents, namespaces;
- the methodology: routes, workflow definitions, stage skills, role contracts, templates, the docs skeleton, reconciliation;
- the policy that turns devkit's generic engines into SDD behavior: which rules run, which workflow checks gate a stage, how search scopes and pins documents, which tasks get a worktree.

## 3. specrig Port Map

Where each specrig component goes. "devkit" means the capability already exists there and nothing is ported.

| specrig | Destination | Notes |
| --- | --- | --- |
| `init`, `installation`, `project`, release bootstrap, `installation.json` schema 4 | devkit distribution | `devkit sync`/`add`/`remove`/`status`, the receipt, projections, overrides. `.specrig/{managed,local,overrides}` become `.devkit/managed`, in-repository bundles and `.devkit/overrides`. |
| `lint` and the Go rule runner | devkit rules | `devkit rules check` (`--staged`, `--ci`) |
| SDD rules: id-convention, spec-format, spec-lifecycle, task-coverage, traceability-link, document-reference, workflow-shared-stage | `spec` bundle, `kind = "rule"` | Ported from Go to Python rules; the document index they share becomes a devkit-spec module. |
| RULE-markdown-link, RULE-file-length | devkit | Built-in rules. |
| RULE-rule-implementation | dropped | It checked the layout of Go rule modules. |
| skill-authoring preset, RULE-skill-document-size | devkit `authoring` bundle | |
| git-commits preset | devkit `git-commits` bundle | |
| github-milestones preset | `spec` bundle preset | SDD-specific. |
| `commit` | devkit gate | `verify-commands` running `devkit rules check --staged`. |
| `workflow` (`next`, `show`, `bind`, `validate`, `checks`, `envelope`) | devkit workflow | |
| Workflows s-lane, direct-delivery, bugfix, incubated-delivery | `spec` bundle, `kind = "workflow"` | specrig-specific checks become `workflow-check` assets. |
| `worktree start\|finish\|status` | devkit worktree | |
| Scope registry and journal (`scope`), proposal cleanup on finish | `devkit spec scope` | Attached to the worktree lifecycle through `devkit.worktree`'s `before_remove`. |
| `git.worktree` route policy | `spec` bundle guidance | Which routes run in a worktree. |
| `config show`, `.specrig/config.yml` | `devkit spec policy`, `.devkit/config.toml` | Approvals map to `[workflow.approvals]` (gates `intent`, `direction`, `integration`), the feedback sweep to `[workflow.stages]`, `pull_request` and branch cleanup to `[worktree]`; SDD-only keys (`git.worktree`) go to `[tool.spec]`. [Policy](../policy.md). |
| `list`, `resolve`, `refs` (document catalog) | `devkit spec list\|resolve\|refs` | |
| `search` (BM25, go-potion dense, hybrid) | `devkit spec search` on devkit.search | devkit-spec keeps the search policy: scopes, namespaces, exact-ID pinning, glossary. |
| `proposal new\|padr\|handoff` | `devkit spec proposal`, `devkit spec new` | Handoff is its own cross-layout move (devkit's `devkit workflow handoff` rebinds a unit in place); `devkit spec new` creates a spec bundle without a proposal. [Proposals](../proposals/overview.md). |
| `entrypoints derive` | `devkit spec entrypoints` | |
| `list feedback`, feedback capture | `devkit spec list feedback`, the `spec-feedback` skill | Feedback documents are indexed like any document; specrig's scope, severity and kind filters are not ported. |
| `list playbooks`, `playbook new` | devkit `devkit playbook search` | Authoring a playbook needs no command. |
| `cache`, `serve`, `sync`, `reading` | dropped | Derived-data cache, the removed web viewer, and two commands specrig never implemented. |
| Skills `sr`, `sr-*` | `spec` bundle, `kind = "skill"`, renamed `spec`, `spec-*` (`sr-spec` became `spec-specify`) | Rewritten against devkit and `devkit spec` commands. |
| Subagents challenger, reconciler, reviewer, scout | `spec` bundle, `kind = "subagent"` role contracts | |
| Instructions contract-authoring, living-spec-writing | `spec` bundle, `kind = "instruction"` | contract-authoring is ported. |
| Instruction guidance-architecture | devkit | Superseded by devkit's resource taxonomy. |
| Templates (capability, story, decision, proposal, feedback, playbook) | `spec` bundle, `kind = "document"` | capability, story, decision and proposal are ported (the decision template gains the frontmatter real ADRs carry); feedback waits for the feedback decision, playbook is devkit's. |
| `template/docs` skeleton, `glossary.yaml` | `spec` bundle, seeded `document` `docs-skeleton` in its own preset | Opt-in (`devkit add spec:docs-skeleton`), so an existing `docs/` tree never receives files it did not ask for; written once where absent, then project-owned. `glossary.yaml` moved to `docs/glossary.yaml`, the search synonyms of `devkit spec search`. |
| Playbooks brownfield-adoption, feedback-hygiene | `spec` bundle, `kind = "playbook"` | |
| Playbooks harness-maintenance, cache-ops | dropped | Installation upkeep is devkit's; the cache is gone. |
| Managed `SPECRIG:START/END` block in `AGENTS.md` | `guidance` fragments | devkit writes the one `DEVKIT:START/END` block. |
| Constitution `.specrig/AGENTS.md` | `spec` bundle `AGENTS.md` | Returned by `devkit get-context spec`. |

## 4. Layout

```text
src/devkit_spec/
  __init__.py      # no side effects: devkit imports it to locate the bundle
  errors.py        # SPEC_ advisory codes
  documents/       # the document model: IDs, parser, Markdown scanner, index, reference rewrite
  rules/           # the spec rules (BaseRule subclasses), run by devkit rules through the bundle's rule files
  cli/             # the `devkit spec` group and its commands
  bundle/          # bundle.toml and asset sources: instructions, rule files and guides, templates
tests/
docs/
```

Rules live in the package, not in the rule files the bundle deploys: each deployed file
(`bundle/rules/<name>/<name>.py`) only subclasses the package's rule, because `devkit rules` instantiates the classes a
rule file defines, and carries the guide `devkit rules explain` prints. The rule code is tested and versioned with the
package; the deployed file stays a stable one-liner.

## 5. Documentation

- [Documents overview](../documents/overview.md) and [reference](../documents/reference.md): the document model and
  `devkit spec resolve|refs|list`.
- [Rules reference](../rules/reference.md): the rules the bundle ships.
- [Workflows overview](../workflows/overview.md): the four delivery workflows, their gates and the role contracts.
- [Document search](../search.md): `devkit spec search` and its policy.
- [Project policy](../policy.md): `devkit spec policy` and `[tool.spec]`.
- [Proposals overview](../proposals/overview.md) and [reference](../proposals/reference.md): proposals, PADRs and
  handoff (`devkit spec proposal`), and new spec bundles (`devkit spec new`).
