---
reconcile_id: REC-git-policy-levels
feature: SPEC-git-policy-levels
status: resolved
targets:
  - file: docs/capabilities/delivery/CAP-DLV-project-policy.md
    resolution: modified
  - file: docs/capabilities/delivery/CAP-DLV-proposal-incubation.md
    resolution: modified
  - file: docs/capabilities/collaboration/CAP-COLL-work-scope-registry.md
    resolution: modified
  - file: docs/stories/collaboration/US-run-parallel-work-safely.md
    resolution: modified
  - file: docs/stories/delivery/US-route-development-intent.md
    resolution: modified
  - file: docs/architecture/ARCH-03-context.md
    resolution: modified
  - file: docs/architecture/ARCH-06-runtime-view.md
    resolution: modified
  - file: docs/architecture/ARCH-08-cross-cutting.md
    resolution: modified
  - file: docs/glossary.md
    resolution: modified
  - file: docs/development/workflow.md
    resolution: modified
  - file: docs/decisions/2026-10/20261015-worktree-and-pull-request-levels.md
    resolution: modified
---

# Reconciliation: Worktree and pull request policy levels

The project policy capability states the `auto` and `required` levels, their defaults, validation and the Git policy
output; `ADR-worktree-and-pull-request-levels` records the decision. The proposal incubation and work-scope registry
capabilities key the handoff guard and registration on a linked worktree. Stories, architecture views, the glossary
and the development guide follow the levels; this repository sets `worktree = "required"` and `pull_request = "auto"`.
Existing code entrypoints already cover the changed modules; no entrypoint declarations change.

Deferred work: the orchestration mode, the worker role contract and the `spec-delegate` extension are retained in
`PROP-orchestration-mode`.
