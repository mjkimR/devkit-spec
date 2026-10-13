# Development Workflow

How changes to devkit-spec are made, verified and committed. The repository develops through its own `spec` bundle:
the same constitution, skills, workflows and rules it ships.

## 1. Start Every Change from the Constitution

1. Run `uv run --no-active devkit get-context spec` once per agent context and read the instructions it lists before
   the actions they govern.
2. Start with `/spec <intent>`; `/spec-next` orients in work already under way. The router picks the route
   (S-Lane, direct delivery, bugfix, incubated) and the workflow (`CAP-DLV-delivery-workflows`).
3. Read `uv run --no-active devkit spec policy` before routing, gate and Git decisions. This repository sets no
   `[workflow.approvals]`, so every gate is `ask`.
4. Route 2 and above write `spec.md`, `plan.md` and `tasks.md` (`devkit spec new <slug>`) before production code, and
   reconcile into `docs/` before completion.

## 2. Boundaries of a Change

- A capability that is not specific to spec-driven development belongs in devkit (`../devkit`), not here: add it there
  first, then use it through devkit's public surface (`ARCH-03-context`).
- Never import devkit's private helpers; never copy them.
- Libraries never print; only `src/devkit_spec/cli/` writes output (`ARCH-08-cross-cutting`).
- Rule logic lives in `src/devkit_spec/rules/`; `src/devkit_spec/bundle/rules/<name>/rule.py` stays a one-line
  subclass with its guide `guide.md` beside it (`ADR-rules-implemented-in-the-package`).
- No external consumers exist yet: breaking changes to the bundle, the commands and the APIs are made in place,
  without migrations or deprecation shims.
- Port specrig behaviour by semantics, not code structure, and drop what devkit already covers
  (`MAT-specrig-port-map`).

## 3. Documentation

- `docs/` is this repository's Living Spec ([docs/README.md](../README.md)). A behaviour, contract or error-code
  change updates the owning capability in the same change; a lasting design choice gets an ADR.
- Every `SPEC_` code defined under `src/` must appear as `` `CODE` `` under `docs/` (`tests/test_documented_codes.py`),
  in its owning capability with level and condition.
- `src/devkit_spec/bundle/seed/docs/` is the skeleton consumers receive; `docs/` here is project-owned and describes
  devkit-spec itself. Changing one does not change the other.
- Skill and playbook documents of the bundle stay within 8192 bytes (`tests/test_bundle_budgets.py`).
- All documentation, guide material and bundle assets are English.

## 4. Verification

Run lint, type checks and relevant tests before completing a code change:

| Target | Command |
| --- | --- |
| Lint and format | `just lint` |
| Lint and format check (CI) | `just lint-check` |
| Type check (Pyright) | `just check` |
| Tests | `just test [pytest args]` |
| Test coverage | `just test-cov` |
| Governance rules | `just rules-check` (`devkit rules check`) |
| Spec rule tests (deployed copies) | `uv run --no-active devkit rules test [RULE-<id>...]` |
| Everything CI runs | `just ci` |

Recipes stay thin; shared shell logic belongs in `scripts/`. Tests live in `tests/`, never under `src/`, with one
exception: a spec rule's tests live in its folder, `src/devkit_spec/bundle/rules/<name>/tests/test_rule.py`, and deploy
with the rule (`CAP-GOV-spec-rules`). They are self-contained: `devkit.rules.testing` loads and evaluates the rule, and
no `tests/conftest.py` fixture is available to them. `just test` collects them with the rest; after
`uv run --no-active devkit sync`, `devkit rules test` runs the deployed copies' tests in isolation, as a consumer
would (arguments after `--` go to pytest).

## 5. Commits

- Commit only on an explicit instruction. Never commit `.env` files, secrets or personal data.
- Messages follow Conventional Commits in the imperative mood (`feat: ...`, `fix: ...`, `refactor: ...`, `docs: ...`).
- This repository configures no `verify-commands` for devkit's commit gate; `just ci` before committing is the local
  equivalent, and `just rules-check --staged` checks exactly what is staged.
