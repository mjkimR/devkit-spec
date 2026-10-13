---
id: FB-derive-prints-every-pair
title: "entrypoints derive prints every boundary-target pair"
scope: bundle
kind: suggestion
category: token-cost
target: "devkit spec entrypoints derive"
skill: spec-sync
agent: claude-code
origin: agent
severity: noise
recurring: true
status: promoted
created_at: 2026-10-13
---

# [FB-derive-prints-every-pair] entrypoints derive prints every boundary-target pair

## 2. Suggestion / Change Request (suggestion, change-request)

- **Current Procedure**: `derive --spec` prints one `[PAIR]` line per boundary path and reconcile target, so a spec
  with 20 boundary paths and 4 targets prints 80 lines, mostly tests and skill files paired with every capability.
- **Proposed Procedure**: print `new` pairs only by default (count the `declared` ones in the summary), or group
  lines per target; keep the full list under `--format json`.
- **Expected Benefit**: the spec-sync review step reads a handful of candidates instead of the whole product.
- **Cost & Risk**: a change of the derive output contract (`CAP-TRACE-code-entrypoints`).
- **Attempted**: observed twice in this repository (`SPEC-feedback-list-filters`, this spec).

## Evidence

```text
[SUMMARY: pairs=80 new=70 declared=10 skipped=3 applied=0]
```

- **Disposition**: src/devkit_spec/cli/entrypoints.py, `CAP-TRACE-code-entrypoints`: S-Lane; the text output is one `[CANDIDATES]` line per document with its paths grouped by state (80 lines become 4 in the observed case); JSON keeps every pair
