# devkit-spec

Spec-driven development for AI coding agents, built on [devkit](https://github.com/mjkimR/devkit). One Python
package ships both halves:

- the `spec` **bundle** (`devkit.bundles`): instructions, skills, workflows, rules, templates and the docs skeleton,
  deployed into a project by `devkit sync` like any content package;
- the `devkit spec` **commands** (`devkit.commands`): mounted into devkit's own command line, so agents reach the
  whole toolchain through the one `devkit` executable of the project environment.

devkit provides everything that is not specific to spec-driven development: asset distribution, the rule, workflow
and gate engines, document search, task worktrees and the Agent Advisory Protocol. devkit-spec adds the document model
(Living Spec, feature specs, IDs, references) and the procedures on top.
The project's own Living Spec starts at [docs/README.md](docs/README.md).

Status: the document model with namespaces (`devkit spec
resolve|refs|list|search`), ten spec rules, the four delivery workflows with their role contracts, proposals and spec
bundles (`devkit spec proposal new|padr|handoff`, `devkit spec new`), code entrypoints (`devkit spec entrypoints`),
the scope registry (`devkit spec scope`), `devkit spec policy`, the constitution, instructions, templates, 12 `spec*`
skills, two playbooks and the opt-in docs skeleton.

## Use in a project

```bash
uv add --dev "devkit-spec @ git+https://github.com/mjkimR/devkit-spec"   # devkit comes with it (Git source)
uv run devkit sync                # deploys the spec bundle (auto_select) with devkit's own bundles
uv run devkit add spec:docs-skeleton  # optional: seed the docs/ skeleton (written once where absent, then project-owned)
uv run devkit spec --version      # [VERSION: devkit-spec <version>]
```

The repository is private: Git must be able to read it. Locally `gh auth setup-git` (or any Git credential helper)
is enough. Where only a token is available (CI, cloud agents), give Git the token through the environment, nothing
written to disk; `uv.lock` keeps plain URLs:

```bash
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0="url.https://x-access-token:${GITHUB_TOKEN}@github.com/.insteadOf"
export GIT_CONFIG_VALUE_0="https://github.com/"
uv sync --locked
```

A project opts out of the bundle with `[presets] spec = false` in `.devkit/config.toml`. `uv run devkit config
template` writes every key the file accepts as a comment at its default, devkit-spec's `[tool.spec]` tables
included; uncomment a key to change it.

## Development

devkit comes from its GitHub main through a Git source pinned in `uv.lock`; `just local-devkit <command>` tries
an unpushed devkit checkout at `../devkit`. Then:

```bash
just init        # uv sync
just ci          # lint-check, check, test, rules-check
```

Python 3.12 or later, macOS or Linux.
