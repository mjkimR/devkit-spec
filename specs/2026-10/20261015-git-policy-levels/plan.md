---
id: PLAN-git-policy-levels
spec: SPEC-git-policy-levels
---

# Technical Plan: `SPEC-git-policy-levels` Worktree and pull request policy levels

## 1. Constitution & Invariant Review

`ADR-policy-in-the-tool-spec-table` keeps `worktree` in `[tool.spec]` and pull requests in devkit's `[worktree]`;
the location does not change. `CAP-DLV-project-policy` rule 3 (`worktree` defaults to `true`), rule 5 (boolean) and
rule 6 (worktree routing) change: the new levels, the `auto` default and the routing that follows them are a lasting
policy change, recorded in a new ADR (slug worktree-and-pull-request-levels) during reconciliation. Booleans are rejected without a
mapping under the repository's compatibility policy.

## 2. Architecture Overview & Impact

- **Impacted Components**:
  - `src/devkit_spec/config.py`: `WORKTREE_LEVELS = ("auto", "required")`; `SpecConfig.worktree: str = "auto"`;
    validation `config tool.spec.worktree: expected "auto" or "required", got <value>`; template key with
    `kind='"auto" | "required"'`; module docstring.
  - `src/devkit_spec/proposals/handoff.py` `_check_worktree`: drop the policy read; the guard runs in every linked
    worktree.
  - `src/devkit_spec/scope/flow.py` `auto_register`: drop the policy read; register in every linked worktree.
    `cli/proposals.py` docstring follows.
  - `src/devkit_spec/cli/policy.py`: no logic change; the level strings print bare through `fields_line`.
  - `uv.lock`: devkit-agt at the pushed commit that reads `pull_request` levels (`856f1af`).
  - `.devkit/config.toml`: `[worktree] pull_request = "auto"`, `[tool.spec] worktree = "required"`, and the
    commented template line at the new default.
  - Bundle guidance: `skills/spec/SKILL.md` (7653 of 7680 bytes, so wording moves into `references/worktree.md`),
    `skills/spec/references/worktree.md` (levels section, start and finish paths), `references/completion.md`
    (policy bullet; S-Lane contradiction with `s-lane.md`), `skills/spec-integrate/SKILL.md` (8152 of 8192 bytes:
    Step 5 and 6 policy wording points to `references/worktree.md` §3 instead of repeating it),
    `skills/spec-next/SKILL.md`, workflows `direct-delivery`, `bugfix`, `incubated-delivery`, `s-lane`, and
    `playbooks/brownfield-adoption/SKILL.md`.
- **New Dependencies**: None; devkit-agt moves within `>=0.1,<0.2`.

## 3. Component & Interface Design

### Level semantics (normative for the guidance)

| Key | `auto` (default) | `required` |
| --- | --- | --- |
| `[tool.spec] worktree` | The agent decides per task. A worktree is needed when the task integrates through a pull request, another task is in flight in this checkout, the user's uncommitted changes must stay untouched, the work is an isolated experiment, or the user asks; otherwise the current checkout. The choice and its reason go in the final change report's assumptions. | Every Route 2, Route 3, Route 4 and bugfix task runs in its own worktree. S-Lane is never required to. |
| devkit `[worktree] pull_request` | The agent decides per task: a pull request when the task needs platform review or CI, the base branch cannot be pushed directly, or the user asks; otherwise a local merge (`devkit worktree finish --merge`). | Every route, S-Lane included, integrates through a pull request; `finish --merge` is refused (`WORKTREE_PR_POLICY`). |

A request naming the checkout or the integration path still overrides the policy for that task and is reported.
A task that integrates through a pull request runs in a worktree at either worktree level, because the pull
request path ends with `devkit worktree finish`.

## 4. Error Handling & Edge Cases

- A boolean in either key: `SPEC_CONFIG_INVALID` from devkit-spec, `WORKTREE_CONFIG_INVALID` from devkit; every
  command that reads the table stops with exit 2. No mapping or warning path.
- The worktree is created before the lock and config change are in the base: the task itself runs under the base
  policy (`worktree=yes pull_request=no`) and finishes with `devkit worktree finish --merge`. After the merge the
  base needs `uv sync` before devkit reads the new config.

## 5. Verification & Test Plan

- Unit and CLI tests: `tests/test_cli_policy.py` (default line, levels, JSON strings, invalid values including
  booleans), `tests/test_package.py` (template line), `tests/test_config_template.py` (round trip),
  `tests/proposals/test_proposal_handoff_worktree.py` (guard at both levels, base checkout),
  `tests/scope/test_flow.py` (registration at both levels, base checkout).
- Guidance: `tests/test_bundle_budgets.py`; `rg -n "worktree=(yes|no)|pull_request=(yes|no)" src/devkit_spec/bundle`
  returns nothing.
- Commands: `just lint`, `just check`, `just test`, `just rules-check`, and `devkit spec policy` in the worktree.
