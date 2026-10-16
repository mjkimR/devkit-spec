---
id: CAP-DLV-spec-bundles
title: Spec Bundles
summary: Creating a feature spec bundle under specs/<YYYY-MM>/<YYYYMMDD>-<slug>/ with devkit spec new, its layout, the SPEC/PLAN/TASKS skeletons marked for devkit's not-skeleton check, and how spec.md is bound to a delivery workflow.
area: delivery
status: active
created_at: 2026-10-13
stories:
  - US-route-development-intent
  - US-incubate-and-hand-off-a-proposal
entrypoints:
  - src/devkit_spec/proposals/specs.py
  - src/devkit_spec/proposals/binding.py
  - src/devkit_spec/cli/specs.py
---

# [CAP-DLV-spec-bundles] Spec Bundles

## 1. Summary

A spec bundle is the work unit of `spec`-depth work and of every handed-off proposal: a directory
`specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` whose `spec.md` is the anchor of a devkit workflow unit. `devkit spec new`
creates one without a proposal, writing the document IDs the spec rules expect (`devkit workflow new` would write an
`id` the rules reject) and binding `spec.md` to a delivery workflow. The same skeleton writer serves
`devkit spec proposal handoff` (`CAP-DLV-proposal-incubation`), which fills it from the proposal body.

## 2. Scope & Boundary

- **In-Scope**: `devkit spec new` (`create_spec`), the bundle layout and directory naming, the `spec.md`, `plan.md`
  and `tasks.md` skeletons and their skeleton marker, the workflow binding of `spec.md` and the `sdd-spec-bugfix` variant.
- **Out-of-Scope**:
  - Proposals and handoff: `CAP-DLV-proposal-incubation`.
  - The stages that fill the skeletons and their checks: `CAP-DLV-delivery-workflows`.
  - Format, lifecycle, task coverage and reconcile rules over bundle files: `CAP-GOV-spec-rules`.
  - Namespace registration and resolution: `CAP-DOCS-namespaces`.
- **Non-Goals**:
  - **Scope Excluded**: filling a bundle's content. The skeletons carry placeholders; `spec-specify`, `spec-plan`
    and `spec-tasks` write the real content and remove the marker.
  - **Scope Excluded**: binding to a workflow that does not resolve. An explicit `--workflow` that does not resolve
    or validate is refused; only the default may fall back to an unbound bundle.

## 3. Business Rules & Policies

1. **Validate before writing**: `devkit spec new` MUST check the slug, `--namespace`, `--summary`, slug availability
   and an explicit `--workflow` before it writes anything; any refusal leaves the workspace unchanged.
2. **Slug normalization**: a leading `SPEC-` is dropped, then the proposal normalization applies (a leading `PROP-`
   and trailing `.md` dropped, every run of characters other than letters, digits, `_` and `-` becomes `-`, outer
   dashes trimmed, lower-cased). A slug with no letter or digit left, or longer than 59 characters (its activity
   branches `plan-<slug>` and `dev-<slug>` must fit devkit worktree's 64), is `SPEC_SLUG_INVALID`.
3. **One slug, one unit**: the command MUST refuse (`SPEC_EXISTS`) a slug whose `SPEC-<slug>` or `PROP-<slug>` any
   document declares, a proposal bundle `docs/proposals/PROP-<slug>/` or file `docs/proposals/PROP-<slug>.md`, and an
   existing bundle directory; `[TARGET]` lists them.
4. **Skeleton marker**: every file written carries `<!-- devkit:skeleton -->` as its first body line, right after
   the frontmatter. devkit's `not-skeleton(<file>)` check keeps `specify` (or `plan-tasks`) open until the file is
   written for real and the line removed. A skeleton-marked `spec.md` is exempt from `RULE-document-summary` until it
   is written.
5. **Binding**: `spec.md` is bound with devkit's `write_binding` (`workflow`, `workflow_hash`) to `--workflow`,
   default `sdd-spec-feature`. The bound workflow is the only record of the work's `task-kind`: `spec.md` has no
   `kind` field. An explicit workflow that does not resolve or validate, or that names by path a
   definition other than the one discovered for its id (devkit's `WORKFLOW_NOT_BINDABLE`: the binding records only
   the id, so later lookups would find another definition or none), is `SPEC_WORKFLOW_INVALID` before writing; a default that is not available leaves `spec.md` unbound with a `SPEC_UNBOUND` notice, whose
   `[FIX]` is `devkit workflow bind --unit <dir> --workflow <id>`.
6. **Bugfix bundles start with `spec.md` only**: a bundle bound to `sdd-spec-bugfix` gets no `plan.md` or
   `tasks.md`: the workflow writes them in
   `plan-tasks`, and skeletons would have to match the characterized criteria at the `characterize` stage's
   `lint-clean` exit (`RULE-task-coverage` skips a spec without `tasks.md`). Rationale:
   `ADR-bugfix-bundles-start-with-spec-only`.
7. **Optional fields**: `summary` is written to `spec.md` only when `--summary` is given; without it the agent adds
   the field when removing the marker. `namespace` is written when `--namespace` is given, else when the current
   directory lies in a registered namespace (`CAP-DOCS-namespaces` section 3.3, rule 3, without the every-namespace
   fallback); otherwise no field is written and the bundle is global.
8. **Roll back on failure**: any failure while writing removes what was written. An advisory error (such as
   `FRONTMATTER_INVALID` binding `spec.md`) is reported with its own code, any other failure as `SPEC_WRITE_FAILED`.
   A roll-back that could not remove something is always `SPEC_WRITE_FAILED`, whose message says the roll-back was
   incomplete and whose `[DETAIL]` lists what is left.
9. **On the slug's Development branch**: in a Git checkout, linked or base, the command MUST refuse
   (`SPEC_WRONG_BRANCH`) to run on another branch than `dev-<slug>`, before writing: a spec unit is Development's and
   lives on its activity branch, which inline Planning starts first (`devkit worktree start dev-<slug>`, with
   `--no-worktree` to stay in the current checkout). A workspace outside Git is not checked.

## 4. Interfaces & Data Contracts

### 4.1 Command

```text
devkit spec new <slug> [--title/-t TEXT] [--summary TEXT] [--workflow <id>] [--namespace <name>]
                       [--date YYYY-MM-DD] [-w/--workspace-root DIR] [--format text|json] [-q] [-v] [--strict]
```

| Option | Meaning |
| --- | --- |
| `--title/-t` | Spec title (default: the slug). |
| `--summary` | Write `summary: <text>` into `spec.md`: one or two English sentences saying what the spec defines. Empty, or containing a letter outside the Latin script: `ARGUMENT_INVALID` (`[TARGET] --summary`), nothing written. |
| `--workflow` | Workflow `spec.md` is bound to (default `sdd-spec-feature`; `sdd-spec-bugfix` writes `spec.md` only). |
| `--namespace` | Write `namespace: <name>`: `global` or a namespace registered in `[[tool.spec.namespaces]]`, else `ARGUMENT_INVALID` with the valid names in `[FIX]`. Omitted: the namespace of the current directory, if any (rule 7). |
| `--date` | Bundle date (default: today): the directory name and `created`. |

```bash
uv run devkit spec new login-flow --title "Login flow"              # sdd-spec-feature
uv run devkit spec new crash-on-save --workflow sdd-spec-bugfix     # spec.md only
uv run devkit spec new login-flow --summary "Defines how users sign in with email and password."
```

Text output, then `[NEXT_CMD: ...]` only when `spec.md` is bound:

```text
[SPEC: SPEC-login-flow path=specs/2026-10/20261013-login-flow workflow=sdd-spec-feature]
[NEXT_CMD: devkit workflow next --unit specs/2026-10/20261013-login-flow]
```

`workflow=-` means unbound. The `[SPEC: ...]` line ends with `namespace=<name>` when the bundle reports a namespace:
the field written, else `global` in a workspace that registers namespaces; a global bundle in a workspace without
registered namespaces reports none (no field). JSON: `id`, `dir`, `workflow`, `namespace` (the same value, `null` when
none is reported), `next_command`, `notices`.

### 4.2 Bundle Layout

```text
specs/<YYYY-MM>/<YYYYMMDD>-<slug>/
├── spec.md          # SPEC-<slug>: the anchor; requirements, non-goals, acceptance criteria
├── plan.md          # PLAN-<slug>: design, interfaces, verification plan (bugfix: written in plan-tasks)
├── tasks.md         # TASKS-<slug>: tasks with _Boundary and _Requirements (bugfix: written in plan-tasks)
├── target-docs.md   # handoff only: the proposal's Living Spec blueprint
├── reconcile.md     # written by spec-sync; resolved before completion (CAP-GOV-spec-rules)
├── envelopes/       # devkit envelopes (CAP-DLV-delivery-workflows)
└── decisions/       # devkit gate decision records
```

### 4.3 Skeletons

- **`spec.md`**: frontmatter `id: SPEC-<slug>`, `title`, optional `summary`, `status: planned`,
  `created: <bundle date>`, optional `namespace` and `milestone`, `related_capabilities: []`,
  `related_stories: []`, then `workflow` and `workflow_hash` from the binding. H1 `# [SPEC-<slug>] <title>`; sections
  `1. Problem Statement & Motivation`, `2. User Stories`, `3. Non-Goals` (a `Scope Excluded` placeholder),
  `4. Acceptance Criteria & Behavioral Contracts` (one placeholder `### [AC-01] <scenario>` with Given/When/Then
  lines) and, after a handoff with leftover proposal sections, `5. Carried Proposal Notes`.
- **`plan.md`**: `id: PLAN-<slug>`, `spec: SPEC-<slug>`; sections `1. Architecture Overview & Impact` (target area,
  blueprint reference), `2. Component Breakdown & Interface Contracts` (planned and excluded boundaries from a
  proposal), `3. Verification & Test Plan` (a placeholder line).
- **`tasks.md`**: `id: TASKS-<slug>`, `spec: SPEC-<slug>`, `plan: PLAN-<slug>`; one `Task 1.1` whose `_Boundary` is the
  owned boundary (else the target area) and whose `_Requirements:` line lists every acceptance criterion ID, so
  `RULE-task-coverage` holds.

Only `spec.md` has a status. Without a proposal, the problem statement is a placeholder and the target area is
`<target area>`.

### 4.4 Library

```python
from devkit_spec.proposals import SKELETON_MARKER, CreatedSpec, create_spec, mark_skeleton, spec_files

create_spec(root, "login-flow", workflow="bugfix")  # CreatedSpec: id, dir, workflow, namespace, next_command, notices
create_spec(root, "rate-limits", namespace="api", summary="Defines request rate limits.", day=date(2026, 10, 13))
create_spec(root, "quotas", cwd=Path.cwd())  # the namespace of cwd when --namespace is omitted
```

`resolve_binding` (`devkit_spec.proposals.binding`) resolves and validates a workflow with devkit's `Workspace`
before anything is written; `DEFAULT_WORKFLOW` is `sdd-spec-feature`, `BUGFIX_WORKFLOW` `sdd-spec-bugfix`.

### 4.5 Codes

`0` success; `2` refused or failed. Notices do not change the exit code (warnings exit `1` under `--strict`).

| Code | Level | Class | Condition |
| --- | --- | --- | --- |
| `SPEC_SLUG_INVALID` | `ERROR` (`INPUT_ERROR`) | `SpecSlugError` | The slug keeps no letter or digit after normalization. |
| `SPEC_WRONG_BRANCH` | `ERROR` (`INPUT_ERROR`) | `SpecWrongBranchError` | In Git, the checkout is not on `dev-<slug>` (rule 9); `[FIX]` starts or continues that branch. Nothing written. |
| `SPEC_EXISTS` | `ERROR` (`INPUT_ERROR`) | `SpecExistsError` | A document declares `SPEC-<slug>` or `PROP-<slug>`, a proposal of the slug exists, or the bundle directory exists; `[TARGET]` lists them. |
| `SPEC_WORKFLOW_INVALID` | `ERROR` (`INPUT_ERROR`) | `SpecWorkflowError` | `--workflow` names a workflow that does not resolve or validate, or a definition path other than the one discovered for its id; `[DETAIL]` carries devkit's code (`WORKFLOW_NOT_BINDABLE` for the latter). |
| `SPEC_WRITE_FAILED` | `ERROR` (`MAINTENANCE`) | `SpecWriteError` | A write failed; what was written is removed. When the roll-back was incomplete, `[DETAIL]` lists what could not be removed. |
| `SPEC_UNBOUND` | `NOTICE` | `SpecUnboundNotice` | No `--workflow` and `sdd-spec-feature` is not available: `spec.md` is unbound. |
| `ARGUMENT_INVALID` | `ERROR` (`INPUT_ERROR`) | devkit's `ArgumentError` | `--namespace` is neither `global` nor registered, or `--summary` is empty or not English. |
| `SPEC_CONFIG_INVALID` | `ERROR` (`INPUT_ERROR`) | `SpecConfigError` | `[tool.spec]` is malformed and the namespace is not `--namespace global` (it is validated or detected; `CAP-DLV-project-policy`). |
