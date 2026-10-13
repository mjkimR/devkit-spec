# Project Policy

The decisions a project makes about how delivery runs: which approval gates wait for a person, which stages are
switched off, whether formal work runs in a task worktree, and how it is integrated. Agents read the effective policy
with one command before routing, gate and Git decisions, never by parsing configuration files:

```bash
uv run devkit spec policy
```

```text
[GATE_POLICY: intent policy=ask source=default]
[GATE_POLICY: direction policy=auto source=config]
[GATE_POLICY: integration policy=ask source=default]
[STAGE_POLICY: collect-feedback state=off]
[GIT_POLICY: worktree=yes pull_request=no delete_branch=yes setup="uv sync"]
```

- `GATE_POLICY`: the approval gates of the spec workflows (`intent`, `direction`, `integration`), then any other gate
  the project configures. `policy` is `ask`, `auto` or `off`
  ([devkit approval gates](https://github.com/mjkimR/devkit/blob/main/docs/workflow/overview.md#3-approval-gates));
  `source` is `config` when `.devkit/config.toml` sets it, else `default`.
- `STAGE_POLICY`: one line per stage the project switched off.
- `GIT_POLICY`: `worktree` (route 2 and above run in a task worktree, devkit-spec's own key), then devkit's
  `[worktree]` settings: `pull_request`, `delete_branch`, `setup`.

`--format json` prints `{"approvals": {<gate>: {"policy", "source"}}, "stages_off": [...], "git": {...}}`.

## Configuration

Policy devkit already models stays in devkit's tables; devkit-spec adds only what is specific to spec-driven
development, under the `[tool.spec]` extension table that devkit passes through unread.

```toml
[workflow.approvals]
direction = "auto"          # devkit's default is ask for every gate; specrig defaulted direction to auto
integration = "ask"

[workflow.stages]
collect-feedback = "off"    # switch a stage off by id

[worktree]
pull_request = true         # integrate through pull requests
delete_branch = true        # delete the merged branch
setup = "uv sync"           # run in each new worktree

[tool.spec]
worktree = true             # route 2 and above (formal specs, proposals) run in a task worktree

[[tool.spec.namespaces]]    # monorepo packages with their own Living Spec under docs/packages/<name>/
name = "api"
path = "services/api"

[tool.spec.scope]           # the work-scope registry (devkit spec scope); every key is optional
shared_path = "/srv/scope"  # absolute; default: devkit-spec-scope/ in the Git common directory
namespace = "team"          # default: a hash of the Git common directory
timeout = 10                # seconds per registry command, 1 to 300
```

`[tool.spec.scope]` is described in [Work scope](scope.md#6-configuration).

| Code | Level | Class | Condition |
| --- | --- | --- | --- |
| `SPEC_CONFIG_INVALID` | `ERROR` (`INPUT_ERROR`) | `SpecConfigError` | `[tool.spec]` is not a table, has an unknown key, `worktree` is not a boolean, or a namespace entry is malformed (keys other than `name` and `path`, an invalid or `global` name, an unsafe path, a name or path registered twice), or `[tool.spec.scope]` is not a table, has an unknown key, a relative `shared_path`, a `namespace` that is not a plain name, or a `timeout` outside 1 to 300 whole seconds. |

devkit's own errors pass through: `CONFIG_INVALID` (an unreadable file), `WORKFLOW_CONFIG_INVALID`,
`WORKTREE_CONFIG_INVALID`.
