# RULE-spec-lifecycle

Declaring a spec complete and reconciling it with the Living Spec are paired actions. In a spec bundle
(`specs/<YYYY-MM>/<YYYYMMDD>-<slug>/`), the `status` of `spec.md`, the checklist of `tasks.md` and the `status` of
`reconcile.md` must agree; workflow stages are derived from `tasks.md` and `reconcile.md`, so a mismatch misleads the
next step.

## Violations

Reported on `spec.md`, line 1 (see Scope for runs that target only `tasks.md` or `reconcile.md`). Statuses are compared trimmed and case-insensitively.

- `spec.md` has `status: completed` but the bundle has no `reconcile.md`.
- `spec.md` has `status: completed` but `reconcile.md` has a status other than `resolved`.
- `spec.md` is not `completed`, yet every task in `tasks.md` is checked (at least one, none open) and
  `reconcile.md` is `resolved`: the spec status is stale. Tasks are the `- [ ]` / `- [x]` checklist items (also
  `*` and `+` markers, any indentation) outside the frontmatter and fenced code blocks, counted as devkit's
  `tasks-checked` workflow check counts them. A bundle without `tasks.md` or without checklist items is never stale.

## Remediation

1. A completed spec without `reconcile.md`: sync the Living Spec, then write `reconcile.md` with `reconcile_id`,
   `feature`, `status: resolved` and `targets` (`file`, `resolution`, and a `rationale` for a waiver). If there is no
   evidence of reconciliation, set the spec `status` back to its real stage (for example `in-progress`).
2. A completed spec whose `reconcile.md` is not resolved: reconcile the remaining targets, or waive them with a
   substantive rationale, then set the reconcile `status: resolved`.
3. A stale spec status: `devkit rules fix` sets `status: completed` in `spec.md`. It rewrites only the frontmatter's
   top-level `status:` line, keeps every other character, and writes only a targeted `spec.md` (a whole-workspace run
   targets every one). A `spec.md` without a `status:` line is fixed by hand.

## Scope

Every `spec.md` under `specs/` is a bundle, completed ones included: the first two violations are about completed
specs, so unlike the other spec rules this one does not treat completed bundles as untouchable history.

The relationship spans three files, so a change to any of them can break it. `devkit rules check` without targets
checks every bundle. A run with targets (a commit checks the files it changes) checks a bundle when it targets its
`spec.md`, `tasks.md` or `reconcile.md`; the violation is reported on `spec.md` when that is a target, otherwise on
the targeted `reconcile.md` or `tasks.md`, and the fix then runs only once `spec.md` is targeted too
(`devkit rules fix specs/<YYYY-MM>/<YYYYMMDD>-<slug>/spec.md`).

## Examples

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
