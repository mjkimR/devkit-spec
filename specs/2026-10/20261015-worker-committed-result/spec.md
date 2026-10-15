---
id: SPEC-worker-committed-result
title: Workers deliver committed, self-contained results
summary: "Changes the worker role contract so a worker commits its unit's build on the unit branch, complete and passing the commit gate, and the host validates the committed range instead of an unstaged diff, so local and pull-request-based orchestration share one contract."
status: in-progress
created: 2026-10-15
related_capabilities:
  - CAP-DLV-delivery-workflows
related_stories: []
workflow: direct-delivery
workflow_hash: sha256:6fe2644b9464ea860e6d6928748778b4ffd7a255e92ddea5fe10eba59138f287
---

# [SPEC-worker-committed-result] Workers deliver committed, self-contained results

## 1. Problem Statement & Motivation

The `worker` role leaves its build unstaged; the host validates the working-tree diff, then fixes what the worker may
not touch (the spec status `RULE-spec-progress` asks for, a code-table row a test requires under `docs/`) and commits.
That only works when host and worker share a machine. In pull-request-based orchestration (cloud workers) the worker's
branch and its checks run before any host can step in, so a result that needs host repair fails there, and the host
ends up finishing work it delegated. The first orchestration pilot hit all three gaps
(`FB-worker-checkbox-leaves-spec-status-to-host`, `FB-worker-scope-excludes-code-documentation`,
`FB-worker-manual-check-writes-outside-worktree`). The principle adopted here: a worker hands over a committed,
complete unit of work that passes the commit gate; a result that fails validation is blocked, never discarded.

## 2. User Stories

- **US-1**: As a host coordinating units, I want each worker to return a committed result that already passes its
  checks and the commit gate, so that I only validate and integrate it, wherever the worker ran.

## 3. Non-Goals

1. **Scope Excluded**: other roles (`scout`, `challenger`, `reviewer`, `reconciler`) gaining Git write actions.
2. **Scope Excluded**: pushing, opening or merging pull requests from the worker; the execution environment does that.
3. **Scope Excluded**: a workflow check or devkit feature that enforces the block; the host procedure and the worker
   envelope carry it.
4. **Scope Excluded**: Codex or Antigravity worker support (`PROP-worktree-host-compatibility`).

## 4. Acceptance Criteria & Behavioral Contracts

### [AC-01] The worker commits a complete result on its unit branch
- **Given** the worker role contract
- **When** a test reads its frontmatter and body
- **Then** `x-git-actions` is `[read, commit]`, and the body requires the worker to stage only write-scope paths, commit
  on the unit branch through the commit gate, leave the worktree clean, and return the head commit id, and forbids
  push, merge, rebase, reset, amend, stash and checkout

### [AC-02] The worker's result is self-contained
- **Given** the worker role contract and the `spec-tasks` skill
- **When** a test reads them
- **Then** the contract lets the worker set the spec's status only through `devkit rules fix <unit>/spec.md`, write a
  `docs/` path only when a task's `_Boundary:` names it, and keep throwaway data in pytest's `tmp_path` or an ignored
  path inside the worktree; `spec-tasks` says a worker task's `_Boundary:` names the `docs/` paths its checks require

### [AC-03] Other roles stay read-only
- **Given** the `scout`, `challenger`, `reviewer` and `reconciler` contracts
- **When** a test reads their frontmatter
- **Then** each `x-git-actions` is `[read]`

### [AC-04] The host validates the committed range and blocks a failure
- **Given** the `spec-delegate` skill
- **When** a test reads its worker validation and fold-back steps
- **Then** they validate the cumulative range from the last accepted head (initially the head recorded before
  spawning) to the returned head: a descendant, every changed path in the write scope, `spec.md` changed in its
  `status` only, a clean worktree and an unchanged base; a failure is recorded as a `failed` worker envelope that
  blocks the unit, keeps the commits (no reset, a pull request stays open and blocked) and is fixed by further commits

### [AC-05] Orchestration mode follows the committed-result contract
- **Given** the `spec-orchestrate` skill
- **When** a test reads its per-unit loop
- **Then** the worker commits its build, the host validates the committed range and records the envelope, and a
  blocked unit does not proceed to review or integration

### [AC-06] The decision is recorded
- **Given** `docs/decisions/`
- **When** `devkit spec resolve ADR-worker-delivers-committed-result` runs
- **Then** it resolves to an `accepted` decision stating the principle, the worker's Git actions, the range validation
  and the block-not-discard rule
