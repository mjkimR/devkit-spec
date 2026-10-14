# [RULE-spec-lifecycle] Spec Lifecycle Consistency

## 1. Overview

Declaring a spec complete and reconciling it with the Living Spec are paired actions. In a spec bundle
(`specs/<YYYY-MM>/<YYYYMMDD>-<slug>/`), the `status` of `spec.md`, the checklist of `tasks.md` and the `status` of
`reconcile.md` must agree; workflow stages are derived from `tasks.md` and `reconcile.md`, so a mismatch misleads the
next step.

- **Phase and severity**: `linter`, `error`. Shipped by the `spec` bundle (preset `core`).
- **What is checked**: every `spec.md` under `specs/` defines a bundle (its directory), completed ones included: the
  first two violations are about completed specs, so unlike the other spec rules this one does not treat completed
  bundles as untouchable history. Statuses are compared trimmed and case-insensitively.
- **Targeting**: the relationship spans three files, so a change to any of them can break it. `devkit rules check`
  without targets checks every bundle not matched by `[rules] exclude`. A run with targets (a commit checks the files
  it changes) checks a bundle when it targets its `spec.md`, or names its `reconcile.md` or `tasks.md` as an explicit
  target.

## 2. Cause of Violation

Reported at line 1 of `spec.md` when that is a target, otherwise of the first named file of `reconcile.md` and
`tasks.md`, so it always lands in a file the run targets:

- `spec.md` has `status: completed` but the bundle has no `reconcile.md`: `Completed spec <spec.md> has no
  reconcile.md`.
- `spec.md` has `status: completed` but `reconcile.md` has a status other than `resolved`: `Completed spec <spec.md>
  has reconcile.md with status '<status>'`.
- `spec.md` is not `completed`, yet every task in `tasks.md` is checked (at least one, none open) and `reconcile.md`
  is `resolved`: `Spec status '<status>' of <spec.md> is stale: all tasks are checked and reconcile.md is resolved`.
  Tasks are the `- [ ]` / `- [x]` checklist items (also `*` and `+` markers, any indentation) outside the frontmatter
  and fenced code blocks, counted as devkit's `tasks-checked` workflow check counts them. A bundle without
  `tasks.md` or without checklist items is never stale.

## 3. Remediation

1. A completed spec without `reconcile.md`: sync the Living Spec, then write `reconcile.md` with `reconcile_id`,
   `status: resolved` and `targets` (`file`, `resolution`, and a `rationale` for a waiver), as
   `RULE-reconcile-contract` describes. If there is no evidence of reconciliation, set the spec `status` back to its
   real stage (for example `in-progress`).
2. A completed spec whose `reconcile.md` is not resolved: reconcile the remaining targets, or waive them with a
   substantive rationale, then set the reconcile `status: resolved`.
3. **Autofix** for a stale spec status: `devkit rules fix` sets `status: completed` in `spec.md`. It rewrites only the
   value of the frontmatter's top-level `status:` line, keeps every other character (a trailing comment on that line
   included: a `#` after whitespace and outside a quoted value, so the whole of `"draft #2"` is the value), and writes only a targeted `spec.md` that is
   valid UTF-8 (a whole-workspace run targets every one). When only `tasks.md` or `reconcile.md` is targeted, the
   violation is not fixable; target the spec too (`devkit rules fix specs/<YYYY-MM>/<YYYYMMDD>-<slug>/spec.md`). A
   `spec.md` without a `status:` line is fixed by hand.

Read the `spec:living-spec-writing` instruction (Completed Specs and Traceability) before setting a spec `completed`
by hand or moving it back to an earlier stage: it says what a completed spec means for later work;
`devkit rules explain` prints its path as a `[RELATED: ...]` line.

## 4. Configuration

The rule has no settings. Project policy in `.devkit/config.toml` (`[rules] exclude`, `[rules.severity_overrides]`,
`[rules.phase_overrides]`) applies as to every rule.

## 5. Exceptions

There is no inline suppression. Set the statuses to the bundle's real stage instead of excusing a mismatch;
`[rules] exclude` removes a bundle's files from every rule.

## 6. Examples

Incorrect:

```text
specs/2026-10/20261004-example/
  spec.md        status: completed
  tasks.md       11 of 11 tasks checked
  (no reconcile.md)

specs/2026-10/20261004-other/
  spec.md        status: planned      <- tasks 5/5 checked, reconcile resolved
  reconcile.md   status: resolved
```

Correct:

```text
specs/2026-10/20261004-example/
  spec.md        status: completed
  reconcile.md   status: resolved, targets: [...]

specs/2026-10/20261004-other/
  spec.md        status: completed    <- devkit rules fix
  reconcile.md   status: resolved
```
