---
id: FB-lock-bump-command-misses-new-devkit-commits
title: Documented devkit lock bump names the wrong package and keeps a cached commit
scope: repo
kind: friction
category: docs-mismatch
target: docs/development/setup.md
skill: spec
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: promoted
created_at: 2026-10-15
---

# [FB-lock-bump-command-misses-new-devkit-commits] Documented devkit lock bump names the wrong package and keeps a cached commit

## 1. Friction / Question (friction, question)

- **Context**: Bumping `uv.lock` to a devkit commit pushed minutes earlier, to adopt the `pull_request` levels.
- **Expectation**: `docs/development/setup.md` says `uv lock --upgrade-package devkit` moves to the latest main.
- **Actual**: The package is `devkit-agt`, not `devkit`. `uv lock --upgrade-package devkit-agt` resolved without
  moving the pin, because uv reused its cached Git ref; `devkit-advisory` comes from the same commit and stays behind.
- **Workaround (or Interpretation Chosen)**: `uv lock --upgrade-package devkit-agt --upgrade-package devkit-advisory
  --refresh` moved both pins to the new commit.
- **Suggestion**: Document that command (or a `just` recipe for it) and how to confirm the pinned commit
  (`rg -n "#[0-9a-f]{40}" uv.lock` against `git ls-remote`).

## Diagnostic Details

- **Reproduction**: Push a devkit commit, then run `uv lock --upgrade-package devkit-agt` in devkit-spec.
- **Expected / Actual**: Expected the new commit; actual `Resolved 33 packages` with the old `#656e9f2` pin.
- **Versions**: devkit-agt 0.1.1 at `656e9f2` and `856f1af`; uv version unknown.
- **Conditions**: devkit-spec task worktree; devkit source is Git main without a rev.
- **Workarounds Attempted**: `--refresh` with both packages: pins moved to `856f1af`.
- **Related Assets**: `docs/development/setup.md`, `pyproject.toml` `[tool.uv.sources]`, `uv.lock`.

## Evidence

```text
docs/development/setup.md:16: `uv lock --upgrade-package devkit` moves to the latest main.
$ uv lock --upgrade-package devkit-agt   -> Resolved 33 packages in 538ms (uv.lock unchanged, #656e9f2...)
$ uv lock --upgrade-package devkit-agt --upgrade-package devkit-advisory --refresh
  Updated devkit-advisory v0.1.1 (656e9f21) -> v0.1.1 (856f1afe)
  Updated devkit-agt v0.1.1 (656e9f21) -> v0.1.1 (856f1afe)
```

- **Disposition**: S-Lane fix of `docs/development/setup.md`: the documented bump names `devkit-agt` and `devkit-advisory` with `--refresh`.
