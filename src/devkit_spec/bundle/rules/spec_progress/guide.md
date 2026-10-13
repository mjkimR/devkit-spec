# [RULE-spec-progress] Spec Progress Status

## 1. Overview

A spec's `status` tells a reader where its work is without opening `tasks.md`: `draft` or `planned` before the first
task is done, `in-progress` while tasks are being checked, `completed` once the Living Spec is reconciled
(`RULE-spec-lifecycle`). Nothing else moves a spec to `in-progress`, so this rule reports a spec whose tasks have
started while its status says they have not.

- **Phase and severity**: `linter`, `warning`: a progress hint, not a contract, so it never blocks a commit. Shipped
  by the `spec` bundle (preset `core`).
- **What is checked**: every spec bundle (`specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` with a `spec.md`). Statuses are compared
  trimmed and case-insensitively.
- **Targeting**: as `RULE-spec-lifecycle`: `devkit rules check` without targets checks every bundle not matched by
  `[rules] exclude`; a run with targets checks a bundle when it targets its `spec.md` or names its `tasks.md` as an
  explicit target.

## 2. Cause of Violation

Reported at line 1 of `spec.md` when that is a target, otherwise of the named `tasks.md`: the `spec.md` status is
`draft` or `planned` and at least one task in `tasks.md` is checked: `Spec status '<status>' of <spec.md> is behind
its tasks: <checked> of <total> checked`. Tasks are counted as devkit's `tasks-checked` workflow check counts them
(`- [ ]` / `- [x]` items outside the frontmatter and fenced code blocks).

A bundle whose every task is checked and whose `reconcile.md` is `resolved` is not reported here:
`RULE-spec-lifecycle` reports it and its fix sets `completed`.

## 3. Remediation

**Autofix**: `devkit rules fix` sets `status: in-progress` in `spec.md`. It rewrites only the frontmatter's top-level
`status:` line, keeps every other character, and writes only a targeted `spec.md`. When only `tasks.md` is targeted,
the violation is not fixable; target the spec too (`devkit rules fix specs/<YYYY-MM>/<YYYYMMDD>-<slug>/spec.md`).

## 4. Configuration

The rule has no settings. Project policy in `.devkit/config.toml` (`[rules] exclude`, `[rules.severity_overrides]`,
`[rules.phase_overrides]`) applies as to every rule; a project that wants the status kept strictly raises it with
`[rules.severity_overrides] "RULE-spec-progress" = "error"`.

## 5. Exceptions

There is no inline suppression. A spec with other statuses (`in-progress`, `completed`, a project-specific value) is
never reported.
