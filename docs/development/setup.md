# Local Setup

How a contributor (person or AI coding agent) gets a working devkit-spec checkout. Architecture of the environments:
`ARCH-07-deployment`.

## 1. Prerequisites

- **Python** 3.12 or later (`.python-version` pins 3.12).
- **uv** (environments and dependencies), **just** (recipes), **Git**.
- **macOS or Linux**. Windows is not supported (the scope registry needs `flock`).

## 2. Clone Both Repositories

devkit is developed next to this repository: `pyproject.toml` takes `devkit` from `../devkit/packages/devkit` and
`devkit-embed` from `../devkit/packages/devkit-embed` as editable path sources, so a change on either side is visible
to the other at once.

```bash
git clone https://github.com/mjkimR/devkit
git clone https://github.com/mjkimR/devkit-spec   # beside it: ../devkit must exist
cd devkit-spec
just init                                         # uv sync --no-active
```

Every recipe runs `uv run --no-active ...`, so an activated virtual environment of another project never leaks in.

## 3. Optional: Dense Search

`devkit spec search` ranks lexically unless devkit's search extra is installed. To work on hybrid or dense ranking:

```bash
uv sync --no-active --extra search    # devkit[search]: numpy, tokenizers, devkit-embed
```

## 4. Check the Installation

```bash
uv run --no-active devkit spec --version          # [VERSION: devkit-spec <version>]
uv run --no-active devkit get-context spec        # the constitution this repository follows
uv run --no-active devkit status                  # deployed bundles and drift
just ci                                           # lint-check, check, test, rules-check
```

## 5. The Repository Consumes Its Own Bundle

`.devkit/config.toml` selects `spec = ["core", "docs-skeleton"]`, and the editable install makes devkit read the bundle
straight from `src/devkit_spec/bundle/`. After editing anything under `src/devkit_spec/bundle/`, redeploy so the
managed copies, the projected skills and subagents and the `AGENTS.md` block follow:

```bash
uv run --no-active devkit sync
```

`.devkit/managed/` is Git-ignored and never edited by hand. More in [Development workflow](workflow.md).
