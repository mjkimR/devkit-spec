---
id: FB-multi-host-integration-ergonomics
title: Add host confirmation adapters and ergonomics beyond Codex MCP elicitation
scope: unknown
kind: suggestion
category: missing-capability
target: devkit.host.mcp and src/devkit_spec/bundle/skills/spec-integrate/SKILL.md
skill: spec-sync
agent: antigravity
origin: agent
severity: workaround
recurring: false
status: open
created_at: 2026-10-17
---

# [FB-multi-host-integration-ergonomics] Add host confirmation adapters and ergonomics beyond Codex MCP elicitation

## 2. Suggestion / Change Request (suggestion, change-request)

- **Current Procedure**: `devkit` ships the Codex native MCP confirmation bridge (`integration_prepare`, `integration_integrate`, `integration_status`, `integration_resume` via `ctx.elicit()`). On hosts that do not support MCP elicitation or do not project the `devkit` MCP server, `integration_integrate` fails closed with `INTEGRATION_CONFIRMATION_UNAVAILABLE`, and agents fall back to running `devkit worktree finish <branch> --merge --local-only` after obtaining conversational `dev-integration` approval.
- **Proposed Procedure**: Evaluate native confirmation surfaces on Claude Code, Antigravity, and OpenCode (such as host-native confirmation tools or signed single-use confirmation tokens bound to `request.id` and `(source_sha, target_sha)`), and add host adapters in `devkit.host` plus corresponding routing guidance in `spec-integrate`.
- **Expected Benefit**: Provides single-step, cryptographically bound `(source_sha, target_sha)` confirmation and local integration across all supported agent hosts, not only Codex MCP sessions.
- **Cost & Risk**: Each host has distinct permission and elicitation semantics; any adapter must preserve the invariant that the agent cannot self-approve a request without an explicit user action bound to the exact prepared request scope.
- **Attempted**: Deferred by design in `SPEC-hook-driven-integration-cleanup` Non-Goal 3 (`ADR-integration-approval-asserted`).

## Diagnostic Details

- **Reproduction**: not applicable
- **Expected / Actual**: Non-Codex hosts or sessions without MCP elicitation support receive `INTEGRATION_CONFIRMATION_UNAVAILABLE` and use the documented CLI fallback (`devkit worktree finish <branch> --merge --local-only`).
- **Versions**: `devkit-agt` `0.1.0` (`b510601d7cbe`), `devkit-spec` `0.1.0`.
- **Conditions**: Running `spec-integrate` on hosts where MCP `ctx.elicit()` is not available.
- **Workarounds Attempted**: Obtain conversational `dev-integration` approval from the user, then run `devkit worktree finish <branch> --merge --local-only` in the base checkout.
- **Related Assets**: `SPEC-hook-driven-integration-cleanup`, `ADR-integration-approval-asserted`, `CAP-HARN-agent-guidance`, `src/devkit_spec/bundle/skills/spec-integrate/SKILL.md`.

## Evidence

```text
SPEC-hook-driven-integration-cleanup Non-Goal 3 & spec-integrate/SKILL.md Step 5:
"Fallback / manual CLI recovery: when the host does not support interactive MCP confirmation (INTEGRATION_CONFIRMATION_UNAVAILABLE) or the user invokes the CLI directly after giving dev-integration approval, run devkit worktree finish <branch> --merge --local-only in the base checkout."
```
