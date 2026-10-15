---
id: PLAN-commit-gate-rules-default
spec: SPEC-commit-gate-rules-default
---

# Technical Plan: `SPEC-commit-gate-rules-default` Commit gate runs the spec rules by default

## 1. Constitution & Invariant Review

None. The constitution's statement that commits run the spec rules becomes true by default; the wording names the gate
so it stays accurate. No ADR changes: `ADR-rules-implemented-in-the-package` already expects the commit gate's
environment to have devkit-spec installed.

## 2. Architecture Overview & Impact

- **Impacted Components**:
  - `uv.lock`, `.devkit/installation.json`: devkit pinned at `bc14046` with
    `uv lock --upgrade-package devkit-agt --upgrade-package devkit-advisory --refresh`, then `uv sync` and
    `devkit sync` (receipt and projected files).
  - `src/devkit_spec/bundle/AGENTS.md` (constitution, section 4): commits run the spec rules through devkit's
    `rules-check` commit gate, on by default. `devkit sync` reprojects it into `AGENTS.md`.
  - `src/devkit_spec/bundle/playbooks/brownfield-adoption/SKILL.md` (Step 4): the hooks run `rules-check` by default;
    choices for existing findings; `gate status` check.
  - `src/devkit_spec/bundle/seed/docs/development/ci-cd.md`: the local commit gate is `rules-check`.
  - `docs/development/workflow.md` (section 5), `docs/development/specrig-port-map.md` (`commit` row): this
    repository relies on the default gate.
  - Living Spec (`spec-sync`): `docs/glossary.md` (Commit gate), `ARCH-03-context` (devkit owns the gate and its
    `rules-check`), `ARCH-06-runtime-view` (scenario 3 sequence).
- **New Dependencies**: None.

## 3. Verification & Test Plan

- `just ci` (bundle budgets cover the edited playbook and constitution).
- AC-01: `uv run devkit gate status`; `rg -n "#[0-9a-f]{40}" uv.lock` shows one devkit commit.
- AC-02: in a scratch commit attempt in the worktree, stage a summary over 300 characters, `git commit`, observe the
  refusal, then unstage.
- AC-03: `rg -n verify-commands` over the bundle and `docs/` (outside `specs/` and proposals).
- `devkit rules check --ci --base main`.
