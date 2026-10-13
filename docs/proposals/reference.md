# Proposals Reference

Commands over the proposal lifecycle and new spec bundles ([overview](overview.md)): `devkit spec proposal new|padr|handoff` and `devkit spec new`. Every command takes `-w/--workspace-root` (default: the devkit project containing the current directory), `--format text|json` and devkit's output options (`-q`, `-v`, `--strict`). Paths are relative to the workspace root.

## Usage

```bash
uv run devkit spec proposal new fast-engine --title "Fast Engine" --target-area capabilities/governance/
uv run devkit spec proposal new fast-engine --milestone "Phase 1" --with-target-docs
uv run devkit spec proposal padr fast-engine "Use AST parser"   # decisions/PADR-use-ast-parser.md
uv run devkit spec proposal handoff fast-engine                 # status: accepted
uv run devkit spec proposal handoff fast-engine --direction-chosen  # draft/reviewing; the user chose the direction
uv run devkit spec new login-flow --title "Login flow"     # spec bundle without a proposal (direct-delivery)
uv run devkit spec new crash-on-save --workflow bugfix     # kind: bugfix; --date YYYY-MM-DD sets the bundle date
uv run devkit spec proposal new rate-limits --namespace api  # namespace: api, carried to spec.md on handoff
```

| Option | Command | Meaning |
| --- | --- | --- |
| `--title/-t` | `new` | Title (default: the slug). |
| `--target-area/-a` | `new` | Capability area the proposal targets (default `capabilities/<area>/`); also the owned boundary. |
| `--milestone/-m` | `new` | Milestone, phase or release; carried to `spec.md`. |
| `--handoff-workflow` | `new` | Write `handoff_workflow: <id>`, the workflow the spec follows after handoff (default at handoff: `direct-delivery`). |
| `--namespace` | `new`, `spec new` | Write `namespace: <name>`: `global` or a namespace registered in `[[tool.spec.namespaces]]` of `.devkit/config.toml`, else `ARGUMENT_INVALID` with the valid names in `[FIX]`. Omitted, no field is written and the bundle is global. Handoff carries a proposal's `namespace` to `spec.md`. |
| `--with-target-docs` | `new` | Also write `target-docs.md`. |
| `--direction-chosen` | `handoff` | Hand off a `draft` or `reviewing` proposal whose direction the user chose explicitly. |
| `--title/-t` | `spec new` | Spec title (default: the slug). |
| `--workflow` | `spec new` | Workflow `spec.md` is bound to (default `direct-delivery`; `bugfix` adds `kind: bugfix` and writes `spec.md` only). |
| `--date` | `spec new` | Bundle date `YYYY-MM-DD` (default: today): the directory and `created`. |

## Output

```text
[PROPOSAL: PROP-fast-engine path=docs/proposals/PROP-fast-engine/proposal.md dir=docs/proposals/PROP-fast-engine target_docs=- workflow=incubated-delivery]
[NEXT_CMD: devkit workflow next --unit docs/proposals/PROP-fast-engine]
[PADR: PADR-use-ast-parser path=docs/proposals/PROP-fast-engine/decisions/PADR-use-ast-parser.md proposal=PROP-fast-engine]
[HANDOFF: PROP-fast-engine spec=SPEC-fast-engine dir=specs/2026-10/20261013-fast-engine workflow=direct-delivery]
[TARGET_DOCS: specs/2026-10/20261013-fast-engine/target-docs.md]
[MATERIALS: docs/materials/2026-10/20261013-fast-engine]
[PROMOTED_ADR: ADR-use-ast-parser path=docs/decisions/2026-10/20261013-use-ast-parser.md padr=PADR-use-ast-parser]
[REWRITTEN: docs/stories/core/US-x.md:5 kind=id from=PROP-fast-engine to=SPEC-fast-engine]
[REWRITTEN: docs/stories/core/US-x.md:9 kind=link from=../../proposals/PROP-fast-engine/proposal.md to=../../../specs/2026-10/20261013-fast-engine/spec.md]
[UNRESOLVED_LINK: docs/stories/core/US-x.md:9 kind=link target=../../proposals/PROP-fast-engine/decisions/ reason=unmapped]
[NEXT_CMD: devkit workflow next --unit specs/2026-10/20261013-fast-engine]
[SPEC: SPEC-login-flow path=specs/2026-10/20261013-login-flow workflow=direct-delivery]
[NEXT_CMD: devkit workflow next --unit specs/2026-10/20261013-login-flow]
```

- `new` prints one `[PROPOSAL: ...]` line (`target_docs` is `-` without `--with-target-docs`, `workflow=-` when `proposal.md` is unbound), then `[NEXT_CMD: ...]` when it is bound to `incubated-delivery`.
- `padr` prints one `[PADR: ...]` line.
- `handoff` prints `[HANDOFF: ...]` (`workflow=-`: `spec.md` is unbound), then `[TARGET_DOCS: ...]` and `[MATERIALS: ...]` when the bundle had them, one `[PROMOTED_ADR: ...]` per PADR, one `[REWRITTEN: <path>:<line> ...]` per rewritten link (`kind=link`) or ID reference (`kind=id`), one `[UNRESOLVED_LINK: <path>:<line> ...]` per link or reference left as it was (`reason`: `unmapped`, `removed`, `ambiguous`, `unreadable`, `unwritable`; line `0` for a whole file), `[SCOPE: SPEC-<slug> namespace= ... token=]` when it registered the bundle in the [work-scope registry](../scope.md) (a handoff inside a linked worktree with `[tool.spec] worktree = true`; a failure is a `SPEC_SCOPE_REGISTER_FAILED` warning), and `[NEXT_CMD: ...]` when `spec.md` is bound to a workflow.

- `spec new` prints `[SPEC: SPEC-<slug> path=<bundle dir> workflow=<id|->]`, then `[NEXT_CMD: ...]` when `spec.md` is bound.

JSON: `new`: `id`, `dir`, `path`, `target_docs`, `workflow`, `next_command`, `notices`; `spec new`: `id`, `dir`, `workflow`, `next_command`, `notices`; `padr`: `id`, `path`, `proposal`; `handoff`: `proposal`, `spec`, `dir`, `workflow`, `target_docs`, `materials`, `decisions` (`id`, `path`, `padr`), `rewritten_files`, `rewritten` (`path`, `line`, `kind`, `from`, `to`), `unresolved` (`path`, `line`, `kind`, `target`, `reason`), `next_command`, `notices`, `scope` (`record`, `token`, `namespace`, `shared_path`, or `null`).

## Error Codes

`0` success; `2` refused or failed (nothing was handed off). Warnings exit `0` (`1` under `--strict`).

| Code | Level | Class | Condition |
| --- | --- | --- | --- |
| `SPEC_PROPOSAL_SLUG_INVALID` | `ERROR` (`INPUT_ERROR`) | `ProposalSlugError` | The slug, or a PADR title, keeps no letter or digit after normalization. |
| `SPEC_PROPOSAL_EXISTS` | `ERROR` (`INPUT_ERROR`) | `ProposalExistsError` | `new`: the bundle or `PROP-<slug>.md` exists. `padr`: a document already declares the PADR ID; `[TARGET]` lists it. |
| `SPEC_PROPOSAL_SLUG_CONFLICT` | `ERROR` (`INTERACTION`) | `ProposalSlugConflictError` | `SPEC-<slug>` exists (`[TARGET]`); the user picks another slug or drops the duplicate. |
| `SPEC_PROPOSAL_NOT_FOUND` | `ERROR` (`INPUT_ERROR`) | `ProposalNotFoundError` | No bundle or single-file proposal has the slug (`padr`: no bundle). |
| `SPEC_PROPOSAL_INVALID` | `ERROR` (`MAINTENANCE`) | `ProposalInvalidError` | The proposal, its blueprint or a PADR cannot be read, or its frontmatter does not parse; or, at handoff, the proposal's `namespace` is not a string naming `global` or a registered namespace. |
| `SPEC_PROPOSAL_NOT_APPROVED` | `ERROR` (`INTERACTION`) | `ProposalNotApprovedError` | Status is not `accepted` (or `draft`/`reviewing` with `--direction-chosen`). |
| `SPEC_PROPOSAL_WORKFLOW_INVALID` | `ERROR` (`MAINTENANCE`) | `ProposalWorkflowError` | The proposal's `handoff_workflow` is not a string, or names a definition that does not resolve or validate; `[DETAIL]` carries devkit's code. |
| `SPEC_PROPOSAL_TARGET_EXISTS` | `ERROR` (`BLOCKED`) | `ProposalTargetExistsError` | The spec bundle, an ADR file or the materials directory exists, two PADRs map to one ADR, or another document declares a promoted ADR's ID. |
| `SPEC_PROPOSAL_HANDOFF_FAILED` | `ERROR` (`MAINTENANCE`) | `ProposalHandoffError` | A write failed; what was written is removed, the materials moved back, the proposal kept. |
| `SPEC_PROPOSAL_CLEANUP_FAILED` | `WARNING` | `ProposalCleanupWarning` | The handoff completed but the proposal could not be removed. |
| `SPEC_PROPOSAL_LINK_UNRESOLVED` | `WARNING` | `ProposalLinkUnresolvedWarning` | Links or references into the proposal were left as they were; the `[UNRESOLVED_LINK]` lines list them. |
| `SPEC_PROPOSAL_REFS_REWRITTEN` | `NOTICE` | `ProposalReferencesRewrittenNotice` | ID references now name the spec or the ADRs; reread each `[REWRITTEN ... kind=id]` sentence. |
| `SPEC_PROPOSAL_UNBOUND` | `NOTICE` | `ProposalUnboundNotice` | `new`: `incubated-delivery` is not available, `proposal.md` is unbound. `handoff`: the proposal names no `handoff_workflow` and `direct-delivery` is not available, `spec.md` is unbound. |
| `SPEC_SLUG_INVALID` | `ERROR` (`INPUT_ERROR`) | `SpecSlugError` | `spec new`: the slug keeps no letter or digit after normalization. |
| `SPEC_EXISTS` | `ERROR` (`INPUT_ERROR`) | `SpecExistsError` | `spec new`: a document declares `SPEC-<slug>` or `PROP-<slug>`, a proposal of the slug exists, or the bundle directory exists; `[TARGET]` lists them. |
| `SPEC_WORKFLOW_INVALID` | `ERROR` (`INPUT_ERROR`) | `SpecWorkflowError` | `spec new --workflow` names a workflow that does not resolve or validate; `[DETAIL]` carries devkit's code. |
| `SPEC_WRITE_FAILED` | `ERROR` (`MAINTENANCE`) | `SpecWriteError` | `spec new`: a write failed; what was written is removed. |
| `SPEC_UNBOUND` | `NOTICE` | `SpecUnboundNotice` | `spec new` without `--workflow`: `direct-delivery` is not available, `spec.md` is unbound. |
| `ARGUMENT_INVALID` | `ERROR` (`INPUT_ERROR`) | devkit's `ArgumentError` | `new`, `spec new`: `--namespace` is neither `global` nor a registered namespace. |
| `SPEC_CONFIG_INVALID` | `ERROR` (`INPUT_ERROR`) | `SpecConfigError` | A namespace other than `global` must be validated (`--namespace`, or a proposal's `namespace` at handoff) and `[tool.spec]` of `.devkit/config.toml` is malformed. |

## Library

```python
from devkit_spec.proposals import create_padr, create_proposal, create_spec, handoff_proposal

created = create_proposal(root, "fast-engine", title="Fast Engine", with_target_docs=True)  # CreatedProposal
create_padr(root, "fast-engine", "Use AST parser")  # CreatedDecision
result = handoff_proposal(root, "fast-engine", direction_chosen=False)  # HandoffResult
result.dir, result.workflow, result.decisions, result.rewritten, result.unresolved, result.notices
create_spec(root, "login-flow", workflow="bugfix")  # CreatedSpec: id, dir, workflow, next_command, notices
create_spec(root, "rate-limits", namespace="api")  # namespace: api in spec.md; create_proposal takes it too
```
