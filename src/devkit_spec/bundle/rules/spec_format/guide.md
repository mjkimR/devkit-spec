# [RULE-spec-format] Spec Document Frontmatter

## 1. Overview

Every capability, story and proposal starts with a YAML frontmatter block that sets `id`, `title` and `status`:
without them a document cannot be indexed, searched or referenced. The rule checks that the fields are present,
non-blank strings; their values are checked by the other spec rules (`RULE-id-convention` for the ID).

- **Phase and severity**: `linter`, `error`. Shipped by the `spec` bundle (preset `core`).
- **What is checked**: the targeted Markdown files under `docs/capabilities/`, `docs/stories/` and `docs/proposals/`,
  and under `capabilities/` and `stories/` of each namespace docs root (`docs/packages/<name>/`, registered in
  `[[tool.spec.namespaces]]`). Unlike the document index, a file is checked even when it declares no ID.
- **What is not**: `README.md`, templates (`*-template.md`, `*_template.md`), directories starting with `.` and
  `materials/` directories.
- **The `namespace` field**: checked in the bundle anchors, a proposal's `proposal.md` under `docs/proposals/` and a
  spec's `spec.md` under `specs/`, when they set it. Current anchors are checked when targeted, a completed spec only
  when named as an explicit target; a run that targets `.devkit/config.toml` checks every current anchor not matched
  by `[rules] exclude`, since a change to the registry can invalidate them.

## 2. Cause of Violation

- A file without a frontmatter block (`---` on the first line, closed by `---`), fixable: `document has no YAML
  frontmatter block (--- ... --- on the first line)`.
- A malformed block (never closed, invalid YAML, duplicate keys, or not a mapping): `frontmatter is malformed:
  <reason>`.
- A missing or blank `id`, `title` or `status`, fixable (an `id` only where the path derives it, see Remediation):
  `frontmatter is missing the required field '<name>'`.
- One of them that is not a string (quote a value such as `id: "123"`): `frontmatter field '<name>' must be a string`.
- A `namespace` in a bundle anchor that is not a string: `frontmatter field 'namespace' must be a string`; or that
  names neither `global` nor a registered namespace: `frontmatter namespace '<value>' is not global or a registered
  namespace`. Reported at the `namespace` line.

## 3. Remediation

- **Autofix**: `devkit rules fix` fills what is missing and leaves every present value alone:
  - a file without a block gets one: `id` the ID its path derives, `title` the first `# ` heading (a leading `[ID]`
    dropped), else the file stem, `status: draft` (or `open` for proposal feedback) and `created_at` today;
  - a block missing `id`, `title` or `status` (or setting it to an empty or null value) gets the same values for the
    missing fields, plus `created_at` when none of `created_at`, `created` or `date` is set.

  The path derives the ID of a capability or story (`CAP-<AREA>-<slug>`, `US-<slug>`: the file stem), a single-file
  proposal `docs/proposals/PROP-<slug>.md` (`PROP-<slug>`), a bundle's `PROP-<slug>/proposal.md` (`PROP-<slug>`) and
  `PROP-<slug>/target-docs.md` (`PROP-<slug>-target`), and a PADR `PROP-<slug>/decisions/PADR-<name>.md`
  (`PADR-<name>`), or direct proposal `feedback/<name>.md` (`FB-<name>`). Any other file under `docs/proposals/` derives no ID: its missing `id` is reported without a fix
  (the fix still fills the other fields), and is set by hand.

  It never touches a malformed block, a field of the wrong type or a file that is not valid UTF-8. Review the
  filled-in values: `status: draft` and a title taken from the heading are starting points, not decisions.
- **By hand**: close the block with `---` and fix its YAML; quote a non-string value. For `namespace`, set a name
  registered in `[[tool.spec.namespaces]]` of `.devkit/config.toml`, or remove the field: a bundle without one is
  global. The `namespace` field is not fixable.

## 4. Configuration

The rule has no settings. Namespaces come from `[[tool.spec.namespaces]]` in `.devkit/config.toml`; project policy
(`[rules] exclude`, `[rules.severity_overrides]`, `[rules.phase_overrides]`) applies as to every rule.

## 5. Exceptions

There is no inline suppression. Free-form notes belong in a `materials/` directory, which the rule skips;
`[rules] exclude` removes a file from every rule.

## 6. Examples

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
