---
reconcile_id: REC-orchestration-mode
feature: SPEC-orchestration-mode
status: resolved
targets:
  - file: docs/capabilities/delivery/CAP-DLV-delivery-workflows.md
    resolution: modified
  - file: docs/capabilities/harness/CAP-HARN-agent-guidance.md
    resolution: modified
  - file: docs/architecture/ARCH-05-1-containers.md
    resolution: modified
  - file: docs/glossary.md
    resolution: modified
---

# Reconciliation: Orchestration mode for delegated implementation

The delivery capability lists the `worker` role, its envelope kind, host statuses and its use only in orchestration
mode, with rule 14 unchanged: the host stages and commits. The guidance capability counts 13 skills and five role
contracts, adds `spec-orchestrate` to the skill table and `spec-delegate/references/payload.md` to the references.
The container view and the glossary follow; the glossary defines direct and orchestration mode.

Existing code entrypoints (`src/devkit_spec/bundle/bundle.toml`) already cover the new assets; no new declarations
are required.

Deferred work: portable worktree access for workers on Codex and Antigravity, and the choice among host access
configuration, an in-repository worktree, a worker process per worktree or host-native isolation, is retained in
`PROP-worktree-host-compatibility`.
