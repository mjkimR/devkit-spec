---
id: FB-config-template-has-no-preview
title: devkit config template cannot show the rendered template without writing the project config
scope: upstream
kind: suggestion
category: missing-capability
target: devkit config template
skill: none
agent: claude-code
origin: agent
severity: noise
recurring: false
status: promoted
created_at: 2026-10-15
---

# [FB-config-template-has-no-preview] devkit config template cannot show the rendered template without writing the project config

## 2. Suggestion / Change Request (suggestion, change-request)

- **Current Procedure**: The only way to see how a template key renders is `devkit config template`, which appends
  every missing key to the project's `.devkit/config.toml` and creates `.devkit/transient/lock`.
- **Proposed Procedure**: A read-only mode (for example `--print`) that writes the rendered template to stdout.
- **Expected Benefit**: Checking a template change (here the `pull_request` and `worktree` level lines) does not
  dirty a tracked file that then has to be restored.
- **Cost & Risk**: One flag and its output contract.
- **Attempted**: Rendered the table through the library (`render_table`) instead, after restoring the config.

## Diagnostic Details

- **Reproduction**: Run `devkit config template` in the devkit repository to inspect the `[worktree]` lines.
- **Expected / Actual**: Expected a preview; actual 32 commented lines added to the tracked `.devkit/config.toml` and
  an untracked `.devkit/transient/lock`.
- **Versions**: devkit-agt 0.1.1 at `f792330`.
- **Conditions**: devkit repository base checkout.
- **Workarounds Attempted**: `git restore .devkit/config.toml`, removed the lock file, rendered via the library.
- **Related Assets**: `devkit config template`, `devkit.core.config_template.render_table`.

## Evidence

```text
$ git diff --stat   -> .devkit/config.toml | 32 ++++++++++++++++++
$ git status --short   -> ?? .devkit/transient/  (only .devkit/transient/lock)
```

- **Disposition**: devkit `ecff122`: `devkit config template --print` writes nothing and returns the resulting file as `text`.
