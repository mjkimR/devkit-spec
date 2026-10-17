---
id: SPEC-hook-driven-integration-cleanup
title: Approval-driven integration and worktree cleanup
summary: Provide the devkit-spec SDD readiness provider, scoped post-finish cleanup contract, and agent guidance for devkit's approval-bound local integration and worktree cleanup.
status: in-progress
created: 2026-10-17
related_capabilities:
  - CAP-DLV-delivery-workflows
  - CAP-DLV-project-policy
  - CAP-DLV-proposal-incubation
  - CAP-COLL-work-scope-registry
  - CAP-HARN-agent-guidance
related_stories:
  - US-route-development-intent
  - US-run-parallel-work-safely
workflow: sdd-spec-feature
workflow_hash: sha256:20b913108a194572244fd42f0587ce3fe7fecfb7610c8afb52fa6b35e79fb0e0
---

# [SPEC-hook-driven-integration-cleanup] Approval-driven integration and worktree cleanup

## 1. Problem Statement & Motivation

Handed off from proposal `SPEC-hook-driven-integration-cleanup` on 2026-10-17.
- **Preserved Materials**: [codex-spike-evidence.md](../../../docs/materials/2026-10/20261017-hook-driven-integration-cleanup/codex-spike-evidence.md)

Integrating a completed task branch and cleaning up its linked worktree has two operational failure modes when driven through ad-hoc shell commands: an agent may re-ask the user for the same business approval (`dev-integration`) after a host permission prompt interrupts a multi-step command sequence, or it may invoke `devkit worktree finish --merge`, which fetches and pushes the base upstream even when only local integration was authorized.

The upstream `devkit` package (`devkit.integration`, `devkit.host`, `devkit.worktree`) now provides an SDD-agnostic approval-bound local integration service (`IntegrationService`) and Codex native MCP confirmation bridge (`integration_prepare`, `integration_integrate`, `integration_status`, `integration_resume`) alongside `devkit worktree finish --local-only`. However, `devkit.integration` fails closed until the methodology package supplies:
1. A `devkit.integration.readiness` entry point (`spec`) that deterministically verifies SDD policy, branch-to-unit correspondence, workflow stage and envelope completion, and cumulative `Phase.CI` governance rules at the exact committed `source_sha` and `target_sha` for both Unit (`spec` and `proposal`) and `session` tasks.
2. A `ScopedCleanup` implementation on the `devkit.post_finish` entry point (`devkit_spec.cleanup:after_finish`) that plans, validates, and executes exact package-owned cleanup targets (empty handed-off proposal directories and finished worktree scope records at their exact revisions) without discovering unapproved targets at execution time.
3. Updated `spec` bundle guidance (`spec-integrate` and `spec` worktree/completion references), repository configuration (`.devkit/config.toml`), and tracked follow-up records for deferred items from the proposal.

### Assumptions
- `devkit` owns the generic request schema, MCP confirmation transport, Gitcommon-dir lock, and fast-forward/worktree/branch executor; `devkit-spec` consumes only `devkit`'s public surface (`devkit.integration`, `devkit.worktree`, `devkit.workflow`, `devkit.rules`, `devkit.core`, `devkit.advisory`).
- `Readiness.evidence` must be a non-empty tuple of `Evidence(code, value)` entries even when `Readiness.reasons` is non-empty, because `devkit.integration.providers.check` validates the evidence shape before raising `ReadinessError` (`INTEGRATION_NOT_READY`).
- Because `IntegrationService` re-invokes `check(context)` immediately before merging and requires exact equality (`providers.check(provider, request.context) == request.readiness`), all readiness evidence and reasons must be 100% deterministic from committed Git trees (`source_sha` and `target_sha`) and never include wall-clock timestamps or mutable runtime state.

## 2. User Stories

- **US-1** (`US-route-development-intent`): As an AI coding agent or developer running SDD in a repository with `[integration] provider = "spec"`, I want `devkit_spec.integration` to verify Unit (`sdd-spec-feature`, `sdd-spec-bugfix`, `sdd-proposal`) and `session` (`sdd-session-feature`, `sdd-session-bugfix`) completion readiness from committed Git state and structured session claims, so that `devkit integration prepare` and `integration_integrate` refuse incomplete, held, or rule-violating branches before confirmation and before merge.
- **US-2** (`US-run-parallel-work-safely`): As an AI coding agent or developer finishing an approved task branch, I want `devkit_spec.cleanup:after_finish` to implement `ScopedCleanup` alongside its classic post-finish callable contract, so that `IntegrationService` binds exact proposal-directory and scope-record targets (`task_id` and `revision`) to the approval request, validates them before mutation, and can resume partial post-finish cleanup without re-merging or broadening scope.
- **US-3** (`US-route-development-intent`, `US-run-parallel-work-safely`): As an AI coding agent following `CAP-HARN-agent-guidance`, I want `spec-integrate` and the `spec` skill references to document the approval-bound local integration path (`integration_integrate`, `integration_resume`, `integration_status`, and `devkit worktree finish --local-only`) and track deferred follow-up scope, so that agents recover cleanly from partial progress or host permission failures without repeating business approvals or triggering unintended network operations.

## 3. Non-Goals

1. **Scope Excluded**: Bypassing host permission enforcement, disabling finish guards, force-cleaning dirty or locked worktrees, or deleting branches and scope records outside the approved integration request.
   - **Rationale**: Workflow approval (`dev-integration`) is business authorization for the exact request scope, not an override of host sandbox boundaries or safety guards.
2. **Scope Excluded**: Weakening required PR, review, test, reconcile, or blocked/question checks, or delegating `plan-intent` and `plan-accept` to `auto`.
   - **Rationale**: `CAP-DLV-delivery-workflows` and `CAP-DLV-project-policy` require human decisions for `plan-intent` and `plan-accept` and full stage/check verification before integration.
3. **Scope Excluded**: Automatic `dev-integration=auto` hook dispatch, remote/PR merge operations, squash/rebase cleanup, or non-Codex host adapters in this release.
   - **Rationale**: These are explicitly retained follow-ups that depend on first verifying the local `dev-integration=ask` provider and scoped cleanup contracts.
   - **When to Reconsider**: Once the tracked follow-up items (FB-auto-integration-dispatch, FB-pr-remote-and-squash-integration, FB-multi-host-integration-ergonomics) meet their restart conditions.
4. **Scope Excluded**: A durable cross-process retry journal or autonomous background recovery runner.
   - **Rationale**: Main-agent recovery uses `IntegrationResult` step statuses, `integration_resume` within the active MCP server process, and `devkit worktree status` / `devkit worktree finish --local-only` after process restarts.

## 4. Acceptance Criteria & Behavioral Contracts

### Scenario 1: [AC-01] Unit task readiness verification for completed spec and accepted proposal units
- **Given** a repository with `[integration] provider = "spec"` and `dev-integration = "ask"`, and a committed `dev-<slug>` branch whose `specs/<YYYY-MM>/<YYYYMMDD>-<slug>` unit (`sdd-spec-feature` or `sdd-spec-bugfix`) has all pre-integration stages satisfied (including `review-refine`, `living-spec-draft` with `reconcile.md` `status: resolved` and `spec.md` `status: completed`, `collect-feedback` or stage-off, `final-change-report` with passing `tests`/`build`/`lint`, no envelope hold, and `Phase.CI` rules passing between `target_sha` and `source_sha`), or a committed `plan-<slug>` branch whose `docs/proposals/PROP-<slug>` unit (`sdd-proposal`) is `status: accepted` with `gate:plan-intent` and `gate:plan-accept` accepted, `collect-feedback` satisfied, no envelope hold, and `Phase.CI` rules passing
- **When** `devkit_spec.integration.check(context)` is called with `Task(kind="unit", id=..., unit=...)`
- **Then** it returns a `Readiness` instance binding `context.finish.source_sha` and `context.finish.target_sha` with `reasons == ()`, deterministic non-empty `Evidence` entries (`TASK_KIND`, `WORKFLOW`, `UNIT`, `SOURCE_SHA`, `TARGET_SHA`, `STAGE_STATUS`, `HOLD_STATUS`, `CI_RULES`), and identical output across repeated calls on the same commits.

### Scenario 2: [AC-02] Unit task readiness refusal on incomplete stages, held envelopes, mismatch, or CI rule violations
- **Given** a unit task on a branch whose slug or activity prefix does not match the unit, or whose `task.id` does not match the unit's document ID or slug, or whose workflow has unmet pre-integration checks (such as unchecked tasks, missing review/reconcile/final-report envelopes, `spec.md` not `completed`, or `proposal.md` not `accepted`), or whose envelopes have a blocked problem or pending question, or whose committed tree has a `Phase.CI` rule violation or `[tool.spec]` / `[workflow.approvals]` configuration error
- **When** `devkit_spec.integration.check(context)` is called (or `IntegrationService(base).prepare(branch, task)` runs)
- **Then** `check(context)` returns a `Readiness` with non-empty coded `evidence` and non-empty `reasons` naming each unmet condition, causing `IntegrationService.prepare` to fail closed with `INTEGRATION_NOT_READY` without mutating Git state.

### Scenario 3: [AC-03] Session task readiness verification and refusal without inventing a unit
- **Given** a `dev-<slug>` branch with `Task(kind="session", id=<id>, unit=None, claims_json=...)`
- **When** `devkit_spec.integration.check(context)` is called with valid session claims (`task_kind` in `feature` or `bugfix`, `effort` in `low`, `medium`, or `high`, `review` passed, `tests` and `lint` passed, and for `bugfix` `reproduced` and `resolved` true), no held or incomplete spec/proposal unit on the branch, and `Phase.CI` rules passing between `target_sha` and `source_sha`
- **Then** `check(context)` returns `Readiness` with `reasons == ()` and deterministic coded `evidence` (including `SESSION_CLAIMS` and `CI_RULES`); whereas if the branch is `plan-<slug>`, or `claims_json` is missing required session verification fields, or the branch modifies an incomplete or held unit, or `Phase.CI` rules fail, `check(context)` returns non-empty `reasons` and `IntegrationService.prepare` raises `INTEGRATION_NOT_READY`.

### Scenario 4: [AC-04] Scoped post-finish cleanup planning, validation, execution, and partial-failure resume
- **Given** `devkit_spec.cleanup:after_finish` registered under `devkit.post_finish` with `integration_local_only = True`, a base repository deploying `.devkit/managed/spec`, an empty or handed-off `docs/proposals/PROP-<slug>` directory in the base, and a registered work-scope record for the task worktree (or base checkout for a `--no-worktree` branch)
- **When** `integration_plan(context)` and `integration_validate(context, targets)` run before merge, and `integration_run(context, finish_result, targets)` runs after merge
- **Then** `integration_plan` returns exact `CleanupTarget` entries (`kind="proposal-prune"` for `docs/proposals/PROP-<slug>` and `kind="scope-record"` with `identity=<task_id>` and `revision="worktree:<namespace>:<revision>"` or `"base:<namespace>:<revision>"`), `integration_validate` raises `StaleRequestError` (`INTEGRATION_REQUEST_STALE`) if an approved scope record's revision changed or a new unapproved record appeared for that worktree while allowing already-removed targets on resume, and `integration_run` removes only the approved targets, returning `CleanupResult(done=True, notices=...)` on success or `CleanupResult(done=False, notices=...)` on target failure so `IntegrationService.resume` retries only the remaining cleanup target.

### Scenario 5: [AC-05] Classic post-finish callback compatibility and non-spec repository no-op
- **Given** a repository with or without `.devkit/managed/spec`
- **When** classic `after_finish(base, result)` is called by `devkit worktree finish`, or `integration_plan`/`integration_run` is called in a repository without `.devkit/managed/spec`
- **Then** `after_finish(base, result)` preserves its existing return contract (`list[str | AdvisoryError] | None`) and notice messages, and in a repository without `.devkit/managed/spec` `integration_plan` returns `()` and `integration_run` returns `CleanupResult(done=True, notices=())`.

### Scenario 6: [AC-06] End-to-end approval-bound integration, non-approval no-op, stale-scope invalidation, and policy guards
- **Given** `IntegrationService` configured with `[integration] provider = "spec"` and `devkit_spec`'s installed entry points (`devkit.integration.readiness` and `devkit.post_finish`)
- **When** `integrate` is invoked across affirmative approval, non-approval (`approve=False`, `decline`, `cancel`), post-preparation source/target/cleanup mutation, `delete_branch = false`, and `pull_request = "required"`
- **Then** affirmative approval fast-forwards the base, removes the linked worktree, deletes or retains the branch per `delete_branch`, prunes the empty proposal directory, and removes the approved scope record with zero network operations (`fetch`, `push`, `ls-remote`); non-approval and stale scope perform zero mutations; and `pull_request = "required"` fails closed with `WORKTREE_PR_POLICY`.

### Scenario 7: [AC-07] Agent guidance, project configuration, and deferred follow-up handoff
- **Given** the `spec` bundle assets in `src/devkit_spec/bundle/`, `.devkit/config.toml`, and the three retained follow-up items from the proposal
- **When** `devkit sync`, `devkit rules check`, and `pytest` (including bundle size budget and documented-code tests) run
- **Then** `.devkit/config.toml` configures `[integration] provider = "spec"`, `spec-integrate` and `spec` references document the MCP integration tools (`integration_prepare`, `integration_integrate`, `integration_status`, `integration_resume`) and `devkit worktree finish --local-only` within the 12,288-byte skill document budget, all three deferred follow-up items are tracked as feedback records in the spec bundle and cited by `FB-...` ID in `reconcile.md`, and all governance rules and tests pass with exit code `0`.
