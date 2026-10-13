# RULE-spec-format

Every capability, story and proposal starts with a YAML frontmatter block that sets `id`, `title` and `status`. The
rule checks that the fields are present, non-blank strings; their values are checked by the other spec rules.

## Violations

- A file without a frontmatter block (`---` on the first line, closed by `---`).
- A malformed block: never closed, invalid YAML, duplicate keys, or not a mapping. Fix it by hand.
- A missing or blank `id`, `title` or `status`, or one that is not a string (quote a value such as `id: "123"`).

`devkit rules fix` fills what is missing and leaves every present value alone:

- A file without a block gets one: `id` the file stem, `title` the first `# ` heading (a leading `[ID]` dropped),
  else the stem, `status: draft` and `created_at` today.
- A block missing `id`, `title` or `status` gets the same values for the missing fields, plus `created_at` when
  none of `created_at`, `created` or `date` is set.

Review the filled-in values: `status: draft` and a title taken from the heading are starting points, not decisions.

## Scope

Markdown files under `docs/capabilities/`, `docs/stories/` and `docs/proposals/`, except `README.md`, templates
(`*-template.md`, `*_template.md`), directories starting with `.` and `materials/` directories. Unlike the
document index, a file is checked even when it declares no ID. Like every devkit rule, a violation is reported only
in the files the run targets: a commit checks the files it changes, `devkit rules check` without targets the whole
workspace.

## Examples

A capability (`docs/capabilities/<area>/CAP-<AREA>-<slug>.md`):

```yaml
---
id: CAP-HARN-context-pack-slicing
title: Context pack slicing
area: harness
status: active
stories:
  - US-init-project-docs
---
```

A story (`docs/stories/<area>/US-<slug>.md`):

```yaml
---
id: US-init-project-docs
title: Initialize project documents
area: onboarding
actor: System administrator
status: active
capabilities:
  - CAP-HARN-context-pack-slicing
---
```
