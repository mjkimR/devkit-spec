---
reconcile_id: REC-hook-driven-integration-cleanup
feature: SPEC-hook-driven-integration-cleanup
status: resolved
targets:
  - file: docs/capabilities/delivery/CAP-DLV-delivery-workflows.md
    resolution: modified
  - file: docs/capabilities/delivery/CAP-DLV-project-policy.md
    resolution: modified
  - file: docs/capabilities/delivery/CAP-DLV-proposal-incubation.md
    resolution: modified
  - file: docs/capabilities/collaboration/CAP-COLL-work-scope-registry.md
    resolution: modified
  - file: docs/capabilities/harness/CAP-HARN-agent-guidance.md
    resolution: modified
---

# Reconcile: `SPEC-hook-driven-integration-cleanup`

## 1. Living Spec Reflection

- `CAP-DLV-delivery-workflows`: Added `src/devkit_spec/integration.py` to `entrypoints`, documented the `devkit.integration.readiness` provider (`spec`) for Unit (`sdd-spec-feature`, `sdd-spec-bugfix`, `sdd-proposal`) and `session` (`sdd-session-feature`, `sdd-session-bugfix`) tasks in §4.8, and added `devkit worktree finish <branch> [--merge [--local-only]]` to §4.7.
- `CAP-DLV-project-policy`: Documented `[integration] provider = "spec"` in `.devkit/config.toml` and clarified that `pull_request = "required"` refuses both `devkit worktree finish --merge` and `IntegrationService.prepare` (`WORKTREE_PR_POLICY`).
- `CAP-DLV-proposal-incubation`: Updated §4.8 (`Prune`) to document `ScopedCleanup` (`proposal-prune` target, `SPEC_POST_FINISH_CLEANUP` notices, and `integration_resume` recovery) alongside classic `after_finish`.
- `CAP-COLL-work-scope-registry`: Added `src/devkit_spec/cleanup.py` to `entrypoints`, updated Rule 9 and §4.6 for dual-mode `after_finish` (`ScopedCleanup` with `<mode>:<namespace>:<revision>` scope-record targets and `proposal-prune` targets), and added `SPEC_POST_FINISH_CLEANUP` to §4.8 (`Codes`).
- `CAP-HARN-agent-guidance`: Updated §4.4 (`Skills`) for `spec-integrate`, `spec/references/worktree.md`, and `spec/references/completion.md` covering the approval-bound MCP integration tools (`integration_prepare`, `integration_integrate`, `integration_status`, `integration_resume`) and `devkit worktree finish --local-only` CLI fallback.
- Existing decisions (`ADR-integration-approval-asserted`, `ADR-cleanup-after-worktree-finish`, `ADR-worktree-and-pull-request-levels`) remain valid without modification.

## 2. Deferred Follow-Up Handoff

Retained follow-up scope from `SPEC-hook-driven-integration-cleanup` Non-Goal 3 is tracked in the backlog:
- `FB-auto-integration-dispatch`: Automatic integration dispatch under `dev-integration = "auto"` once `ask`-mode integration has operational mileage (`specs/2026-10/20261017-hook-driven-integration-cleanup/feedback/auto-integration-dispatch.md`).
- `FB-pr-remote-and-squash-integration`: Remote/PR merge operations and squash/rebase worktree cleanup (`specs/2026-10/20261017-hook-driven-integration-cleanup/feedback/pr-remote-and-squash-integration.md`).
- `FB-multi-host-integration-ergonomics`: Host confirmation adapters and ergonomics beyond Codex MCP elicitation (`specs/2026-10/20261017-hook-driven-integration-cleanup/feedback/multi-host-integration-ergonomics.md`).
