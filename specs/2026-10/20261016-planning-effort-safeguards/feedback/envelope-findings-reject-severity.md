---
id: FB-envelope-findings-reject-severity
title: Envelope findings refuse a severity key that role outputs naturally carry
scope: upstream
kind: friction
category: tool-error
target: devkit workflow envelope review --findings-file
skill: spec-delegate
agent: claude-code
origin: agent
severity: workaround
recurring: true
status: open
created_at: 2026-10-16
---

# [FB-envelope-findings-reject-severity] Envelope findings refuse a severity key that role outputs naturally carry

## 1. Friction / Question (friction, question)

- **Context**: Recording a reviewer's return as `review-01.yaml` and two challenger returns as envelopes.
- **Expectation**: Findings with a severity, which both role returns and the caller's requested output used, could be
  recorded as returned.
- **Actual**: `devkit workflow envelope review --findings-file` refused the file with `ENVELOPE_FINDINGS_INVALID`:
  unknown key `severity`. The allowed keys are `issue`, `evidence`, `failure_condition`, `suggested_action`,
  `resolution` and `waiver`.
- **Workaround (or Interpretation Chosen)**: Moved the severity into the `issue` text as a prefix such as
  `(medium)`.
- **Suggestion**: Either accept an optional `severity` in devkit's finding schema, or state in the `spec-delegate`
  payload reference that role outputs must not carry `severity`, so callers do not request it.

## Diagnostic Details

- **Reproduction**: A findings YAML item with `severity: medium`, passed to `devkit workflow envelope review
  --findings-file`.
- **Expected / Actual**: Expected the envelope; actual `ENVELOPE_FINDINGS_INVALID ... unknown keys ['severity']`.
- **Versions**: devkit pinned by `uv.lock` in devkit-spec at `66b6f6d` (exact version unknown).
- **Conditions**: Same for `challenger` envelopes written earlier in the session (severity folded into the text).
- **Workarounds Attempted**: Severity prefix in `issue` (succeeded).
- **Related Assets**: `devkit workflow envelope review`, `devkit workflow envelope new`,
  `src/devkit_spec/bundle/skills/spec-delegate/references/payload.md`.

## Evidence

```text
[ERROR] (ENVELOPE_FINDINGS_INVALID) --findings-file: finding 1: unknown keys ['severity']
[FIX] Write a mapping with only issue, evidence, failure_condition, suggested_action, resolution (and waiver on a waived finding)
```
