---
id: PLAN-namespace-default-and-handoff-branch
spec: SPEC-namespace-default-and-handoff-branch
---

# Technical Plan: `SPEC-namespace-default-and-handoff-branch` Namespace default from the current directory and the handoff branch guard

## 1. Constitution & Invariant Review

`CAP-DLV-spec-bundles` (business rule 7, "without `namespace` the bundle is global") and the `--namespace` rows of
`CAP-DLV-proposal-incubation` and `CAP-DOCS-namespaces` change to the current-directory default the user chose at G2
(decision 02); `spec-sync` rewrites them. The new refusal adds one code, `SPEC_PROPOSAL_WRONG_WORKTREE`, documented in
`CAP-DLV-proposal-incubation` (`tests/test_documented_codes.py`). No MUST of `docs/architecture/` changes, so no ADR.

## 2. Architecture Overview & Impact

- **Impacted Components**:
  - `src/devkit_spec/proposals/scaffold.py`: `bundle_namespace(root, namespace, cwd)` replaces the module-internal
    `require_namespace`; `create_proposal` takes `cwd` and records the namespace on `CreatedProposal`.
  - `src/devkit_spec/proposals/specs.py`: `create_spec` takes `cwd`; `CreatedSpec` records the namespace.
  - `src/devkit_spec/proposals/handoff.py`: `_check_worktree(root, slug)` before any read of the proposal.
  - `src/devkit_spec/errors.py`: `ProposalWrongWorktreeError`.
  - `src/devkit_spec/cli/specs.py`, `src/devkit_spec/cli/proposals.py`: pass `Path.cwd()`, print `namespace=`.
  - `src/devkit_spec/bundle/instructions/living-spec-writing.md`, `src/devkit_spec/bundle/skills/spec-specify/SKILL.md`:
    the package glossary and the namespace default.
  - Living Spec, reconciled after review: `CAP-DLV-spec-bundles`, `CAP-DLV-proposal-incubation`, `CAP-DOCS-namespaces`.
- **New Dependencies**: None.

## 3. Component & Interface Design

```python
def bundle_namespace(root: Path, namespace: str | None, cwd: Path | None) -> tuple[str | None, str | None]:
    """(field written, namespace reported): an explicit name is checked as before; without one, the namespace
    ``cwd`` lies in (devkit_spec.namespaces.detect), none outside every package or without ``cwd``. Reported: the
    field, else ``global`` in a project that registers namespaces, else ``None``."""


@dataclass
class CreatedSpec:  # likewise CreatedProposal
    ...
    namespace: str | None = None  # the reported namespace
```

- The reported namespace is the written field, or `global` when nothing was written in a workspace that registers
  namespaces; `None` for a global bundle without registered namespaces. Text adds `namespace=<name>` only when it is not `None`; JSON
  always carries the key.
- `_check_worktree`: `git rev-parse --path-format=absolute --git-common-dir --git-dir` in `root`; a nonzero exit (not
  a repository) or equal directories (the base checkout) returns. Otherwise, when `read_spec_config(root).worktree`,
  `git symbolic-ref --quiet --short HEAD` must print the slug, else `ProposalWrongWorktreeError` (`INPUT_ERROR`,
  `[FIX]`: `devkit worktree start <slug>`, `cd` to the printed path, rerun the handoff). A `GitError` without an
  exit status (Git missing, timeout) propagates, as in `devkit_spec.scope.location.locate`.

## 4. Error Handling & Edge Cases

- `-w <root>` from a directory outside the workspace: `detect` returns `None`, the bundle is global.
- A malformed `[tool.spec]` now fails `new` without `--namespace` in a workspace with `[tool.spec]` tables
  (`SPEC_CONFIG_INVALID`), as `list` and `search` already do, and fails a handoff in a linked worktree.
- Detached HEAD in a linked worktree: `symbolic-ref` exits nonzero, reported as branch `-`.

## 5. Verification & Test Plan

- `tests/proposals/`: AC-01..AC-04 (`CliRunner` with `monkeypatch.chdir`, text and JSON), AC-05 and AC-06 with real
  `git worktree add` fixtures.
- AC-07: `rg` over the two assets; `tests/test_bundle_budgets.py`.
- `just ci`; `uv run --no-active devkit sync` and `devkit rules check`.
