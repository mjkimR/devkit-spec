---
id: SPEC-git-policy-levels
title: Worktree and pull request policy levels
summary: "Replace the boolean worktree and pull request policies with auto and required levels, defaulting to auto, and key handoff checks on running in a linked worktree."
status: completed
created: 2026-10-15
related_capabilities:
  - CAP-DLV-project-policy
  - CAP-DLV-proposal-incubation
  - CAP-COLL-work-scope-registry
related_stories: []
workflow: direct-delivery
workflow_hash: sha256:6fe2644b9464ea860e6d6928748778b4ffd7a255e92ddea5fe10eba59138f287
---

# [SPEC-git-policy-levels] Worktree and pull request policy levels

## 1. Problem Statement & Motivation

`[tool.spec] worktree` and devkit's `[worktree] pull_request` are on/off switches. Projects need a different shape:
use a worktree or a pull request when the task needs one (`auto`), or always, as a management policy (`required`).
devkit now reads `pull_request` as `"auto" | "required"` and rejects booleans; devkit-spec still pins a devkit that
reads a boolean, keeps `worktree` boolean with the default `true`, and its skills branch on `yes`/`no`. The handoff
branch guard and the handoff scope registration are switched off by `worktree = false`, so under a default that no
longer forces worktrees they would stop protecting work that does run in one.

## 2. User Stories

- As a maintainer, I want worktrees and pull requests used when a task needs them by default, and always when I
  require them, so isolation and review overhead follow the work instead of a fixed switch.
- As an agent, I want the effective levels and what each one asks of me, so I decide and report a worktree or pull
  request choice the same way in every route.

## 3. Non-Goals

1. **Scope Excluded**: the orchestration mode skill, a worker role contract and `spec-delegate` changes. They are
   the next phase of the same plan and build on these levels.
2. **Scope Excluded**: a per-unit execution-context record, and value-source fields (`config`/`default`) for the Git
   policy in `devkit spec policy`.
3. **Scope Excluded**: changes to devkit, pushing branches or opening pull requests from code, and Auto Hub.

## 4. Acceptance Criteria & Behavioral Contracts

### [AC-01] Worktree level parsing and template

- **Given** a project whose `[tool.spec]` table omits `worktree`, sets it to "auto" or "required", or sets it to
  true, false or "yes"
- **When** `read_spec_config` runs, or `devkit spec policy` runs, or the commented config template is rendered
- **Then** an omitted key reads as "auto"; "auto" and "required" read as given; any other value raises
  SPEC_CONFIG_INVALID and `devkit spec policy` exits 2; the template line is `worktree = "auto"` with the kind
  `"auto" | "required"`, and uncommenting it reads back the defaults.

### [AC-02] Effective Git policy output

- **Given** a project with `[tool.spec] worktree` and devkit's `[worktree] pull_request` at any valid level
- **When** `devkit spec policy` runs in text and in JSON mode
- **Then** the text line is `[GIT_POLICY: worktree=<level> pull_request=<level> delete_branch=yes|no setup=...]` with
  the level strings "auto" or "required", and JSON `git.worktree` and `git.pull_request` hold the same strings; a
  boolean `pull_request` exits 2 with WORKTREE_CONFIG_INVALID.

### [AC-03] Handoff branch guard in any linked worktree

- **Given** a linked worktree whose branch is not the proposal slug (or a detached HEAD), under worktree "auto" or
  "required"
- **When** `devkit spec proposal handoff <slug>` runs there
- **Then** it exits 2 with SPEC_PROPOSAL_WRONG_WORKTREE and changes no file; in the base checkout or outside Git no
  branch check runs at either level.

### [AC-04] Handoff scope registration in any linked worktree

- **Given** a linked worktree on the slug's branch, under worktree "auto" or "required"
- **When** the handoff succeeds
- **Then** the new spec bundle is registered in the work-scope registry and the output carries one `[SCOPE: ...]`
  line; a handoff in the base checkout registers nothing.

### [AC-05] Agent guidance for the levels

- **Given** the bundled skills, references, workflows and playbooks
- **When** an agent reads the Git policy guidance
- **Then** it states: worktree "required" runs every Route 2, Route 3, Route 4 and bugfix task in its own worktree
  and never applies to S-Lane; "auto" leaves the choice to the agent, names when a worktree is needed, and asks for
  the choice and its reason in the final change report's assumptions; pull_request "required" integrates every
  route, S-Lane included, through a pull request; a task that integrates through a pull request runs in a worktree
  at either worktree level. Searching `src/devkit_spec/bundle` for `worktree=yes`, `worktree=no`,
  `pull_request=yes` or `pull_request=no` finds no match.

### [AC-06] Repository adoption

- **Given** this repository after the change
- **When** `devkit spec policy` runs in its base checkout and the bundle tests run
- **Then** the policy line shows `worktree=required pull_request=auto`, `uv.lock` pins a devkit-agt commit that
  reads `pull_request` levels, and `tests/test_bundle_budgets.py` passes.
