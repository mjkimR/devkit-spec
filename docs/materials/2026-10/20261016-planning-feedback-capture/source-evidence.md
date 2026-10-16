# Planning feedback source evidence

These observations support `SPEC-planning-feedback-capture`; they describe current implementation, not shipped changes.

| Source | Evidence | Design consequence |
| --- | --- | --- |
| `src/devkit_spec/bundle/subagents/planning-worker.md` | Purpose forbids writes outside the proposal; write boundaries allow its directory and follow-up drafts | Local feedback fits the existing root |
| `src/devkit_spec/bundle/skills/spec-feedback/SKILL.md` §2 | Destinations mention the spec bundle and global specs feedback; prohibits docs | Add the exact proposal-local exception |
| `src/devkit_spec/proposals/handoff.py`, `_plan_extras` | Unhandled bundle files go to preserved materials; records are excluded | Plan feedback separately and avoid a second generic carry |
| `src/devkit_spec/proposals/handoff.py`, `handoff_proposal` | Preflight destinations before writes; uses `written`, `moved`, `leftovers` for rollback/cross-filesystem moves | Include feedback in the same transaction and relocation map |
| `src/devkit_spec/rules/id_convention.py`, `_feedback`, `_targets` | Only specs feedback paths are recognized | Add proposal feedback paths and equivalent validation |
| `src/devkit_spec/documents/index.py`, `_files` | Index walks ID-bearing Markdown in docs and specs | Existing discovery can index proposal-local feedback |
| `src/devkit_spec/namespaces.py`, `_bundle_anchor` | Nested proposal files follow proposal.md's namespace | Preserve namespace through normal proposal-to-spec handoff |
| `src/devkit_spec/bundle/skills/spec-feedback/references/template.md` | Status is open, promoted, dismissed or forwarded; only hygiene changes it | Open is the transfer criterion; moves never change status |
| `src/devkit_spec/bundle/workflows/sdd-proposal.md` | Rejection starts no worker and changes state/answers only | Sweep before returning the run; retain files until later cleanup |
| devkit `docs/workflow/definition-and-checks.md`, Shared Stages | Shared IDs require equal exit, gate, role, isolation, skills, artifacts; entry is informational | Reuse collect-feedback exactly, with proposal-specific entry |
| `tests/test_workflows.py` | Shared-stage equality and current proposal gate behavior are tested | Add stage progression/policy coverage without relaxing the gate |
| workbench `docs/strategy-layer/01-master-flow.md` §6.2 | No feedback procedure yet; rejection must not invoke workers or Cloud Agents | Explicit upstream update is a handoff prerequisite |

Unverified: no production relocation or policy change has been implemented or executed. Collision, malformed-input,
symlink, rollback, namespace and round-freshness scenarios require Development verification. The current workflow has
no deterministic latest-run freshness check; the proposed per-run sweep is an executor procedure with recorded evidence.
