---
id: FB-commit-gate-runs-no-rules-check
title: The commit gate runs no spec rules here, so an error-severity violation was committed
scope: unknown
kind: friction
category: docs-mismatch
target: devkit gate status
skill: spec-sync
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: open
created_at: 2026-10-15
---

# [FB-commit-gate-runs-no-rules-check] The commit gate runs no spec rules here, so an error-severity violation was committed

## 1. Friction / Question (friction, question)

- **Context**: Committing the Living Spec sync of `SPEC-list-unknown-status` in its devkit worktree.
- **Expectation**: the spec constitution says commits run the spec rules through the commit gate
  (`devkit rules check --staged`), so a staged `RULE-document-summary` error blocks the commit.
- **Actual**: the commit succeeded with that error staged. `devkit gate status` shows only `verify-commands`
  (pre-commit) and `message-nonempty` (commit-msg), with no configuration source, so no rules check runs at commit.
- **Workaround (or Interpretation Chosen)**: fixed the summary in a follow-up commit and re-ran
  `devkit rules check --ci --base <base>` (0 violations) before recording the envelope.
- **Suggestion**: either have the spec bundle (or `devkit sync`) register a staged rules gate, or configure
  `verify-commands` with `devkit rules check --staged` in this repository, or reword the constitution so agents do
  not rely on a gate that is not installed. Ownership (devkit gate defaults, devkit-spec bundle, or project config) is
  for hygiene to decide.

## Diagnostic Details

- **Reproduction**: stage a document whose `summary` exceeds 300 characters; `git commit`.
- **Expected / Actual**: expected the commit refused; actual commit `c0f9289` created.
- **Versions**: devkit 0.1.1; devkit-spec base `ed2dd0d`.
- **Conditions**: hooks dispatched from the base repository's `.git/hooks` (managed wrappers present).
- **Workarounds Attempted**: follow-up commit `9ee6725`; CI-mode rules check clean.
- **Related Assets**: spec constitution §4, `.devkit/config.toml`, `devkit gate`.

## Evidence

```text
constitution §4: `devkit rules check` runs the spec rules; commits run them through the commit gate (`devkit rules check --staged`)
[VIOLATION: RULE-document-summary severity=error file=docs/capabilities/documents/CAP-DOCS-document-lookup.md line=4 ... summary has 355 characters]
c0f9289 docs(specs): reconcile list-unknown-status into the Living Spec      (commit succeeded)
[GATE: verify-commands stage=pre-commit order=200 enabled=true source=builtin]
[GATE: message-nonempty stage=commit-msg order=900 enabled=true source=builtin]
[CONFIG: sources=none]
```
