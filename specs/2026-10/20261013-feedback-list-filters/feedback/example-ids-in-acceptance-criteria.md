---
id: FB-example-ids-in-acceptance-criteria
title: "Example IDs in acceptance criteria are checked as references"
scope: bundle
kind: friction
category: spec-ambiguity
target: "spec-specify skill"
skill: spec-specify
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: open
created_at: 2026-10-13
---

# [FB-example-ids-in-acceptance-criteria] Example IDs in acceptance criteria are checked as references

## 1. Friction / Question (friction, question)

- **Context**: Writing fixture documents (FB-a .. FB-e) into Given/When/Then lines of spec.md
- **Expectation**: Fixture names in a scenario are examples, not edges of the contract
- **Actual**: Written in backticks they are body references; RULE-document-reference reported 20 unresolved IDs and the specify stage stayed open
- **Workaround (or Interpretation Chosen)**: Wrote the fixture IDs without backticks
- **Suggestion**: Say in spec-specify (or contract-authoring) how to write example IDs: plain text, or a fenced block, which the reference parser skips

## Evidence

```text
[VIOLATION: RULE-document-reference ... file=specs/2026-10/20261013-feedback-list-filters/spec.md line=81 ... message="no document has the ID FB-e"]
[SUMMARY: errors=20 warnings=0 infos=0 fixed=0]
```
