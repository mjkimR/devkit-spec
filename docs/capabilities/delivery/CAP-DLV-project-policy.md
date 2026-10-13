---
id: CAP-DLV-project-policy
title: Project Policy
summary: The effective delivery policy of a project (approval gates, switched-off stages, task worktrees and pull request integration) printed by devkit spec policy from devkit's tables and the [tool.spec] extension table of .devkit/config.toml, including the validation of [tool.spec].
area: delivery
status: active
created_at: 2026-10-13
stories:
  - US-route-development-intent
  - US-run-parallel-work-safely
entrypoints:
  - src/devkit_spec/config.py
  - src/devkit_spec/cli/policy.py
---

# [CAP-DLV-project-policy] Project Policy

## 1. Summary

A project decides how delivery runs: which approval gates wait for a person, which stages are switched off, whether
formal work runs in a task worktree, and how it is integrated. Policy devkit already models stays in devkit's tables
(`[workflow.approvals]`, `[workflow.stages]`, `[worktree]`); devkit-spec adds only what is specific to spec-driven
development, under the `[tool.spec]` extension table that devkit passes through unread. Agents read the effective
policy with one command, `devkit spec policy`, before routing, gate and Git decisions. Rationale:
`ADR-policy-in-the-tool-spec-table`.

## 2. Scope & Boundary

- **In-Scope**: `devkit spec policy` (text and JSON), the `[tool.spec]` table and its validation
  (`devkit_spec.config.read_spec_config`), the defaults the command reports, and the `[tool.spec]` tables of devkit's
  commented config template (`devkit_spec.config.template`).
- **Out-of-Scope**:
  - The meaning of `[[tool.spec.namespaces]]`: `CAP-DOCS-namespaces`.
  - The meaning of `[tool.spec.scope]`: `CAP-COLL-work-scope-registry`. This capability owns their validation only.
  - How gates and stage switches act on a workflow: `CAP-DLV-delivery-workflows` and devkit's workflow engine.
  - Executing worktree and integration steps (`CAP-HARN-agent-guidance`): devkit's `devkit worktree` and the `spec`
    skill's worktree procedure.
- **Non-Goals**:
  - **Scope Excluded**: writing policy. The command only reads; the project edits `.devkit/config.toml`.
  - **Scope Excluded**: granting authority. No policy value grants commit, merge, publication or deletion authority
    the user has not given.

## 3. Business Rules & Policies

1. **Read through the command**: agents MUST read policy through `devkit spec policy`, never by parsing
   `.devkit/config.toml`; a policy command error stops policy-dependent work.
2. **devkit tables first**: a policy devkit models (approvals, stage switches, pull requests, branch cleanup, worktree
   setup) MUST live in devkit's table; `[tool.spec]` holds only keys devkit has no table for.
3. **Defaults**: a gate the project does not set is `ask` with `source=default` (devkit's default for every gate);
   `[tool.spec] worktree` defaults to `true`; `[worktree]` values are devkit's defaults (`pull_request = false`,
   `delete_branch = true`, no `setup`).
4. **Gate order**: the spec workflows' gates `intent`, `direction`, `integration` come first, then any other gate the
   project configures, in sorted order.
5. **Strict table**: `[tool.spec]` MUST be a table with only the keys `worktree`, `namespaces` and `scope`; anything
   else is `SPEC_CONFIG_INVALID`, raised by every command that reads the table.
6. **Worktree routing**: `worktree = true` means Route 2 and above (formal specs, proposals, bugfix) run in a task
   worktree; Route 1 always stays in the current checkout. An explicit user request naming the checkout overrides it
   for that task only, recorded in the final change report's assumptions.
7. **Template at the defaults**: `template()` MUST describe every `[tool.spec]` key at the default
   `read_spec_config` applies (an example for a key unset by default and for the namespaces), so the commented
   tables `devkit config template` writes read back as the defaults once uncommented.

## 4. Interfaces & Data Contracts

### 4.1 Command

```bash
uv run devkit spec policy [-w/--workspace-root DIR] [--format text|json] [-q] [-v] [--strict]
```

```text
[GATE_POLICY: intent policy=ask source=default]
[GATE_POLICY: direction policy=auto source=config]
[GATE_POLICY: integration policy=ask source=default]
[STAGE_POLICY: collect-feedback state=off]
[GIT_POLICY: worktree=yes pull_request=no delete_branch=yes setup="uv sync"]
```

- `GATE_POLICY`: one line per gate; `policy` is `ask`, `auto` or `off`
  ([devkit approval gates](https://github.com/mjkimR/devkit/blob/main/docs/workflow/overview.md#3-approval-gates));
  `source` is `config` when `.devkit/config.toml` sets it, else `default`.
- `STAGE_POLICY`: one line per stage the project switched off (`state=off`), sorted.
- `GIT_POLICY`: `worktree` (`[tool.spec] worktree`), then devkit's `[worktree]` settings `pull_request`,
  `delete_branch` and `setup` (`-` when unset).

JSON: `{"approvals": {<gate>: {"policy", "source"}}, "stages_off": [...], "git": {"worktree", "pull_request",
"delete_branch", "setup"}}` (`setup` is `null` when unset).

### 4.2 Configuration

```toml
# .devkit/config.toml
[workflow.approvals]
intent = "ask"              # G1: the user confirms goal, scope and verification
direction = "auto"          # G2: choices within the requested scope proceed with reported assumptions
integration = "ask"         # G3: one approval per integration unit (PR)

[workflow.stages]
collect-feedback = "off"    # switch a stage off by id

[worktree]
pull_request = true         # integrate through pull requests (default false: merge locally)
delete_branch = true        # delete the merged branch
setup = "uv sync"           # run in each new worktree

[tool.spec]
worktree = true             # Route 2 and above (formal specs, proposals) run in a task worktree

[[tool.spec.namespaces]]    # monorepo packages with their own Living Spec under docs/packages/<name>/
name = "api"
path = "services/api"

[tool.spec.scope]           # the work-scope registry (devkit spec scope); every key is optional
shared_path = "/srv/scope"  # absolute or starting with ~; default: devkit-spec-scope/ in the Git common directory
namespace = "team"          # default: a hash of the Git common directory
timeout = 10                # whole seconds per registry command, 1 to 300
```

| Key | Type | Default | Validation |
| --- | --- | --- | --- |
| `tool.spec.worktree` | boolean | `true` | `true` or `false`. |
| `tool.spec.namespaces` | array of tables | `[]` | Each entry exactly `name` and `path`; `name` lowercase words joined by `-`, not `global`; `path` a safe workspace-relative directory without trailing `/`; no name or path registered twice. |
| `tool.spec.scope.shared_path` | string | Git common dir `devkit-spec-scope/` | Absolute after `~` expansion. |
| `tool.spec.scope.namespace` | string | common-dir hash | Letters, digits, `.`, `_`, `-`, not starting with `.`. |
| `tool.spec.scope.timeout` | integer | `10` | Whole seconds from 1 to 300 (a boolean is rejected). |

`devkit config template` writes the `[tool.spec]` tables into `.devkit/config.toml` as comments, from
`devkit_spec.config.template`, the `devkit.config_template` entry point `spec`: every key at its default, an example
for `shared_path`, `namespace` and the namespaces, uncommented in place to change a value. devkit adds only the
tables the file does not mention yet and never changes a line.

`direction = "auto"` lets G2 fire only for a new choice outside the approved scope, for `direct-delivery`, `bugfix`
and `incubated-delivery` alike. `collect-feedback = "off"` makes the delivery workflows skip the feedback sweep; the
executor reports it as skipped.

### 4.3 Library

```python
from devkit_spec.config import read_spec_config

config = read_spec_config(root)  # SpecConfig(worktree, namespaces: tuple[Namespace, ...], scope: ScopeConfig)
tables = template()               # list[devkit.core.TemplateTable]: [tool.spec], its namespaces and scope tables
```

`Namespace` has `name`, `path` and `docs` (`docs/packages/<name>`); `ScopeConfig` has `shared_path` (`Path` or
`None`), `namespace` (`str` or `None`) and `timeout`.

### 4.4 Codes

| Code | Level | Class | Condition |
| --- | --- | --- | --- |
| `SPEC_CONFIG_INVALID` | `ERROR` (`INPUT_ERROR`) | `SpecConfigError` | `[tool.spec]` is not a table, has an unknown key, `worktree` is not a boolean, or a namespace entry is malformed (keys other than `name` and `path`, an invalid or `global` name, an unsafe path, a name or path registered twice), or `[tool.spec.scope]` is not a table, has an unknown key, a relative `shared_path`, a `namespace` that is not a plain name, or a `timeout` outside 1 to 300 whole seconds. |

devkit's own errors pass through: `CONFIG_INVALID` (an unreadable file), `WORKFLOW_CONFIG_INVALID`,
`WORKTREE_CONFIG_INVALID`.
