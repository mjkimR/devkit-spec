---
reconcile_id: REC-worker-committed-result
feature: SPEC-worker-committed-result
status: resolved
targets:
  - file: docs/capabilities/delivery/CAP-DLV-delivery-workflows.md
    resolution: modified
  - file: docs/proposals/PROP-worktree-host-compatibility/proposal.md
    resolution: modified
---

# Reconciliation: `SPEC-worker-committed-result`

- `ADR-worker-delivers-committed-result` (new, accepted) was written before implementation, as the constitution
  requires for a changed MUST, and committed with build Task 1; the branch's cumulative `devkit rules check --ci`
  covers it. It is not a target here because the commit gate checks each target against this commit's diff.
- `CAP-DLV-delivery-workflows`: business rule 14 makes the worker the one role with `commit`; section 4.6 states
  `x-git-actions` per role, the worker row, and the worker paragraph (complete committed result, range validation from
  the last accepted head, block without discarding); the envelope table records worker envelopes as the host's
  validations.
- `PROP-worktree-host-compatibility`: Q1 now covers write access to the Git common directory, since workers commit.
  Its dated material keeps the earlier assumption as history.
- No story changes: no story describes the worker. No architecture changes: roles and their contracts are described
  in `CAP-DLV-delivery-workflows`.
- No deferred work is retained: mechanical enforcement of the block (a workflow check) is a non-goal of this spec.
