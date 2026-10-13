---
id: FB-lint-clean-detail-lists-every-violation
title: "The lint-clean check detail lists every violation on one line"
scope: bundle
kind: suggestion
category: token-cost
target: "devkit workflow next"
skill: spec-specify
agent: claude-code
origin: agent
severity: noise
recurring: false
status: open
created_at: 2026-10-13
---

# [FB-lint-clean-detail-lists-every-violation] The lint-clean check detail lists every violation on one line

## 2. Suggestion / Change Request (suggestion, change-request)

- **Current Procedure**: `devkit workflow next` prints `[CHECK: lint-clean ... detail="<n> violation(s): <every violation>"]`
- **Proposed Procedure**: Print the count and the first few, then point at `devkit rules check <unit>` for the full list
- **Expected Benefit**: A 20-violation spec cost one ~2.5 KB line that duplicated the rules check output
- **Cost & Risk**: A devkit change (the check renderer); none to the bundle
- **Attempted**: Hypothesis

## Evidence

```text
[CHECK: lint-clean class=lint evaluated=true detail="20 violation(s): specs/...:54 RULE-document-reference no document has the ID FB-a; ... (20 entries)"]
```
