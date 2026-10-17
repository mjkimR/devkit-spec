---
id: FB-auto-integration-dispatch
title: Add automatic integration dispatch under dev-integration=auto once ask-mode integration is validated
scope: unknown
kind: suggestion
category: missing-capability
target: devkit.integration.IntegrationService and devkit_spec.integration
skill: spec-sync
agent: antigravity
origin: agent
severity: workaround
recurring: false
status: open
created_at: 2026-10-17
---

# [FB-auto-integration-dispatch] Add automatic integration dispatch under dev-integration=auto once ask-mode integration is validated

## 2. Suggestion / Change Request (suggestion, change-request)

- **Current Procedure**: `SPEC-hook-driven-integration-cleanup` implements approval-bound local integration under `dev-integration = ask`, requiring an interactive MCP confirmation (`authority="mcp-elicitation"`) via `integration_integrate` (or manual `devkit worktree finish --merge --local-only` after user approval). Under `[workflow.approvals] dev-integration = "auto"`, no automatic post-completion dispatch hook invokes `IntegrationService` without interactive elicitation.
- **Proposed Procedure**: After `SPEC-hook-driven-integration-cleanup` is validated in real `dev-integration = ask` workflows, extend `devkit.integration` and `devkit_spec.integration` with an explicit `policy=auto` authority mode (`authority="policy-auto"`) that verifies `[workflow.approvals] dev-integration == "auto"`, all pre-integration readiness evidence (`check(context)`), and scoped cleanup targets before executing the same local fast-forward and worktree/branch/scope cleanup without interactive elicitation.
- **Expected Benefit**: Enables unattended or local-orchestrated runs configured with `dev-integration = "auto"` to complete local integration and worktree cleanup deterministically without waiting for an interactive MCP confirmation prompt.
- **Cost & Risk**: Auto-dispatch mutates the base branch and deletes the linked worktree and activity branch without an interactive prompt; any gap in readiness verification or scope-target validation would take effect immediately. Keeping it deferred until `dev-integration = ask` has operational mileage avoids premature automation risk.
- **Attempted**: Deferred by design in `SPEC-hook-driven-integration-cleanup` Non-Goal 3 (`ADR-integration-approval-asserted`, `ADR-cleanup-after-worktree-finish`).

## Diagnostic Details

- **Reproduction**: not applicable
- **Expected / Actual**: Under `dev-integration = "ask"`, `IntegrationService.integrate` requires interactive MCP confirmation (`mcp-elicitation`); `dev-integration = "auto"` automatic hook dispatch is intentionally deferred as a follow-up item from `SPEC-hook-driven-integration-cleanup`.
- **Versions**: `devkit-agt` `0.1.0` (`b510601d7cbe`), `devkit-spec` `0.1.0`.
- **Conditions**: Repositories configuring `[workflow.approvals] dev-integration = "auto"` with `[integration] provider = "spec"`.
- **Workarounds Attempted**: Run `integration_integrate` with interactive confirmation or `devkit worktree finish <branch> --merge --local-only` from the base checkout.
- **Related Assets**: `SPEC-hook-driven-integration-cleanup`, `ADR-integration-approval-asserted`, `ADR-cleanup-after-worktree-finish`, `CAP-DLV-delivery-workflows`, `CAP-DLV-project-policy`.

## Evidence

```text
SPEC-hook-driven-integration-cleanup Non-Goal 3:
"Scope Excluded: Automatic dev-integration=auto hook dispatch, remote/PR merge operations, squash/rebase cleanup, or non-Codex host adapters in this release.
Rationale: These are explicitly retained follow-ups that depend on first verifying the local dev-integration=ask provider and scoped cleanup contracts.
When to Reconsider: Once the tracked follow-up items (FB-auto-integration-dispatch, FB-pr-remote-and-squash-integration, FB-multi-host-integration-ergonomics) meet their restart conditions."
```
