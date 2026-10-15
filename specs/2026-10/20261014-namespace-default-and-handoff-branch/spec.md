---
id: SPEC-namespace-default-and-handoff-branch
title: Namespace default from the current directory and the handoff branch guard
summary: Defaults the namespace of new proposals and specs to the current directory's package and refuses a proposal handoff in a worktree of another task.
status: completed
created: 2026-10-14
related_capabilities:
  - CAP-DLV-spec-bundles
  - CAP-DLV-proposal-incubation
  - CAP-DOCS-namespaces
related_stories:
  - US-incubate-and-hand-off-a-proposal
  - US-run-parallel-work-safely
workflow: direct-delivery
workflow_hash: sha256:6fe2644b9464ea860e6d6928748778b4ffd7a255e92ddea5fe10eba59138f287
---

# [SPEC-namespace-default-and-handoff-branch] Namespace default from the current directory and the handoff branch guard

## 1. Problem Statement & Motivation

An audit of feature behavior found two behaviors missing without a record.

- **Namespace of new bundles.** Earlier implementations recorded the namespace of the package the current directory
  lies in. `devkit spec new` and `devkit spec proposal new` write a `namespace` only when `--namespace` is given, and
  no bundle skill passes it, so in a monorepo every new bundle silently becomes global while `list` and `search`
  already select by the current directory (`CAP-DOCS-namespaces`). Earlier guidance also told the agent to read a
  package's `glossary.md` together with the root glossary; no bundle asset keeps that rule.
- **Handoff in the wrong worktree.** Earlier implementation refused a handoff in a linked worktree whose branch was not the slug.
  With `[tool.spec] worktree = true` the `spec` skill hands off inside the slug's worktree, and nothing stops a
  handoff in another task's worktree, which puts the new spec bundle on that task's branch.

G2 direction (decision 02): infer the namespace for both commands and restore the glossary guidance; guard the
handoff by branch only.

## 2. User Stories

- **US-1**: As an agent in a monorepo (`US-incubate-and-hand-off-a-proposal`), I want a bundle created from a
  package's directory to belong to that package, so that browsing from the package finds it without remembering
  `--namespace`.
- **US-2**: As an agent running parallel tasks (`US-run-parallel-work-safely`), I want a handoff in another task's
  worktree refused before it writes, so that the spec bundle lands on its own branch.

## 3. Non-Goals

1. **Scope Excluded**: comparing the proposal in the base checkout with the worktree's copy (uncommitted
   proposal check). The `spec` skill's worktree reference already requires committing the proposal before
   `devkit worktree start`.
   - **When to Reconsider**: when a handoff of a stale proposal is observed.
2. **Scope Excluded**: indexing Markdown under `docs/materials/` that declares no ID. Materials stay free-form and
   are reached by path and link (`CAP-DOCS-document-model`).
3. **Scope Excluded**: changing the selection of `list` and `search`, the namespace a handoff carries, or the
   namespace of existing bundles.
4. **Scope Excluded**: a handoff guard in the base checkout or with `[tool.spec] worktree = false`; with that
   setting a project may use worktrees named however it likes.

## 4. Acceptance Criteria & Behavioral Contracts

The fixtures register namespace `api` (`path = "services/api"`, docs root `docs/packages/api`) in
`[[tool.spec.namespaces]]` unless a scenario says otherwise.

### [AC-01] A new spec takes the namespace of the current directory
- **Given** the current directory is `services/api/src` of the workspace
- **When** the agent runs `devkit spec new rate-limits` without `--namespace`
- **Then** `spec.md` has `namespace: api`, the text output is
  `[SPEC: SPEC-rate-limits path=<dir> workflow=direct-delivery namespace=api]`, the JSON output has
  `"namespace": "api"`, and the command exits `0`

### [AC-02] A new proposal takes the namespace of the current directory
- **Given** the current directory is `docs/packages/api` of the workspace
- **When** the agent runs `devkit spec proposal new rate-limits` without `--namespace`
- **Then** `proposal.md` has `namespace: api` and the `[PROPOSAL: ...]` line ends with `namespace=api`; a later
  handoff writes `namespace: api` to `spec.md`

### [AC-03] Outside every package the bundle stays global
- **Given** the current directory is the workspace root, or a directory outside the workspace with `-w <root>`
- **When** the agent runs `devkit spec new` or `devkit spec proposal new` without `--namespace`
- **Then** no `namespace` field is written, the text line ends with `namespace=global` and JSON has
  `"namespace": "global"`; in a workspace without registered namespaces the text line has no `namespace=` field and
  JSON has `"namespace": null`

### [AC-04] An explicit --namespace wins over the current directory
- **Given** the current directory is `services/api`
- **When** the agent passes `--namespace global` to either command
- **Then** `namespace: global` is written and reported (`namespace=global`); an unregistered name is still
  `ARGUMENT_INVALID` with exit `2`

### [AC-05] A handoff in another task's worktree is refused before writing
- **Given** `[tool.spec] worktree = true`, an accepted proposal of slug rate-limits, and the workspace is a linked worktree on
  branch `other-task` (or a detached HEAD)
- **When** the agent runs `devkit spec proposal handoff rate-limits`
- **Then** the command reports `SPEC_PROPOSAL_WRONG_WORKTREE` naming the branch and the slug with a `[FIX]` to run the
  handoff in the slug's worktree, exits `2`, prints nothing on stdout, and leaves the proposal and `specs/` unchanged

### [AC-06] The guard applies only to a linked worktree under the worktree policy
- **Given** an accepted proposal of slug rate-limits
- **When** the agent hands it off in a linked worktree on branch `rate-limits`, in the base checkout on any branch,
  in a linked worktree with `[tool.spec] worktree = false`, or in a directory outside Git
- **Then** each handoff succeeds (exit `0`, a `[HANDOFF: ...]` line)

### [AC-07] Bundle guidance names the package glossary and the namespace default
- **Given** the `spec` bundle
- **When** an agent reads the `living-spec-writing` instruction and the `spec-specify` skill
- **Then** the instruction says to read a package document's `docs/packages/<name>/glossary.md` together with the
  root glossary, its redefinitions applying to that package only, and the skill says to create a package's bundle
  from the package directory or with `--namespace <name>`
