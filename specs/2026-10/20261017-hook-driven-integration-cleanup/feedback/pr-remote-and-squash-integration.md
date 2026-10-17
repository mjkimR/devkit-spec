---
id: FB-pr-remote-and-squash-integration
title: Extend integration service and worktree cleanup for PR remote operations and squash/rebase merges
scope: unknown
kind: suggestion
category: missing-capability
target: devkit.integration.IntegrationService and devkit worktree finish
skill: spec-sync
agent: antigravity
origin: agent
severity: workaround
recurring: false
status: open
created_at: 2026-10-17
---

# [FB-pr-remote-and-squash-integration] Extend integration service and worktree cleanup for PR remote operations and squash/rebase merges

## 2. Suggestion / Change Request (suggestion, change-request)

- **Current Procedure**: `IntegrationService` (`SPEC-hook-driven-integration-cleanup`) enforces `network = "forbid"`, refuses `pull_request = "required"` (`WORKTREE_PR_POLICY`), and executes only local `--ff-only` merges. When a branch is merged via a pull request using squash or rebase, `devkit worktree finish <branch>` reports `WORKTREE_UNMERGED` because its merge check is a commit-ancestry test.
- **Proposed Procedure**: Once local approval-bound integration is established, design an explicit remote/PR integration and post-PR cleanup contract that (1) separates local-only integration from explicit remote push/PR merge authority and (2) verifies squash/rebase PR completion against recorded PR state or tree/patch equivalence before removing the linked worktree and branch.
- **Expected Benefit**: Allows repositories with `pull_request = "required"` or squash/rebase PR merge policies to use deterministic, approval-bound post-merge worktree, branch, and scope-record cleanup without manual branch removal.
- **Cost & Risk**: Network operations (`fetch`, `push`, PR API calls) and non-ancestor branch deletion carry higher irreversibility than local `--ff-only` merges; the confirmation schema must explicitly disclose remote targets and verify squash/rebase provenance so unmerged work is never discarded.
- **Attempted**: Deferred by design in `SPEC-hook-driven-integration-cleanup` Non-Goal 3 (`ADR-worktree-and-pull-request-levels`).

## Diagnostic Details

- **Reproduction**: not applicable
- **Expected / Actual**: `IntegrationService.prepare` raises `PullRequestPolicyError` (`WORKTREE_PR_POLICY`) when `[worktree] pull_request = "required"` and excludes `fetch`/`push`/PR operations by design (`network_operations = "excluded"`).
- **Versions**: `devkit-agt` `0.1.0` (`b510601d7cbe`), `devkit-spec` `0.1.0`.
- **Conditions**: Repositories using `[worktree] pull_request = "required"` or merging PRs via squash/rebase.
- **Workarounds Attempted**: Push the branch, merge through the PR platform, then run `devkit worktree finish <branch>` (or remove squash-merged worktree/branch after explicit user confirmation).
- **Related Assets**: `SPEC-hook-driven-integration-cleanup`, `ADR-worktree-and-pull-request-levels`, `CAP-DLV-project-policy`, `src/devkit_spec/bundle/skills/spec/references/worktree.md`.

## Evidence

```text
SPEC-hook-driven-integration-cleanup AC-06 & Non-Goal 3:
"Scope Excluded: Automatic dev-integration=auto hook dispatch, remote/PR merge operations, squash/rebase cleanup, or non-Codex host adapters in this release."
"pull_request = 'required' fails closed with WORKTREE_PR_POLICY."
```
