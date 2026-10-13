---
id: FB-spec-summary-missing-from-new-guides
title: "The spec router and the feature output standard omit the summary"
scope: bundle
kind: friction
category: docs-mismatch
target: "spec skill and spec-specify references/feature.md"
skill: spec
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: promoted
created_at: 2026-10-13
---

# [FB-spec-summary-missing-from-new-guides] The spec router and the feature output standard omit the summary

## 1. Friction / Question (friction, question)

- **Context**: Creating a Route 2 bundle from the spec skill's routing table
- **Expectation**: The command shown produces a spec that satisfies RULE-document-summary once filled
- **Actual**: The routing table shows `devkit spec new <slug> [--title \"...\"]` and feature.md's output standard has no `summary` line; only spec-specify's SKILL.md mentions `--summary` and the DoD
- **Workaround (or Interpretation Chosen)**: Added the summary by hand while writing spec.md
- **Suggestion**: Show `--summary` in the routing table and a `summary:` line in feature.md's output standard

## Evidence

```text
spec SKILL.md: `devkit spec new <slug> [--title "..."]` creates specs/<YYYY-MM>/<YYYYMMDD>-<slug>/ and binds it
spec-specify SKILL.md: devkit spec new <slug> --title "<Title>" --summary "<English sentence>"
```

- **Disposition**: src/devkit_spec/bundle/skills/spec/SKILL.md, src/devkit_spec/bundle/skills/spec-specify/references/feature.md: S-Lane; the router shows `--summary` and the output standard a `summary` line
