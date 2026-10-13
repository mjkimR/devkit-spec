# devkit-spec

Spec-driven development for AI coding agents, built on [devkit](https://github.com/mjkimR/devkit). One Python
package ships both halves:

- the `spec` **bundle** (`devkit.bundles`): instructions, skills, workflows, rules, templates and the docs skeleton,
  deployed into a project by `devkit sync` like any content package;
- the `devkit spec` **commands** (`devkit.commands`): mounted into devkit's own command line, so agents reach the
  whole toolchain through the one `devkit` executable of the project environment.

devkit provides everything that is not specific to spec-driven development: asset distribution, the rule, workflow
and gate engines, document search, task worktrees and the Agent Advisory Protocol. devkit-spec adds the document model
(Living Spec, feature specs, IDs, references) and the procedures on top. It is the successor of specrig, whose Go
CLI it replaces; [the architecture overview](docs/architecture/overview.md) maps each specrig component to its new
home.

Status: porting. Done: the document model (`devkit spec resolve|refs|list|search`), the seven spec rules, the four
delivery workflows with their role contracts, proposals and spec bundles (`devkit spec proposal new|padr|handoff`,
`devkit spec new`), `devkit spec policy`, the constitution, instructions, templates, 13 `spec*` skills, the
brownfield-adoption and feedback-hygiene playbooks and the opt-in docs skeleton. Not yet: namespaces, the scope
registry, entrypoints and the reconcile diff evidence.

## Use in a project

```bash
uv add --dev devkit devkit-spec   # by wheel URL or path until a release exists
uv run devkit sync                # deploys the spec bundle (auto_select) with devkit's own bundles
uv run devkit add spec:docs-skeleton  # optional: seed the docs/ skeleton (written once where absent, then project-owned)
uv run devkit spec --version      # [VERSION: devkit-spec <version>]
```

A project opts out of the bundle with `[presets] spec = false` in `.devkit/config.toml`.

## Development

devkit is developed next to this repository: `pyproject.toml` takes it from `../devkit/packages/devkit` as an
editable path dependency, so a change on either side is visible to the other at once. Clone
`https://github.com/mjkimR/devkit` beside this checkout, then:

```bash
just init        # uv sync
just ci          # lint-check, check, test, rules-check
```

Python 3.12 or later, macOS or Linux.
