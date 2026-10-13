---
id: FB-ruff-formats-plan-snippets
title: "ruff format checks the Python snippets of spec plans"
scope: repo
kind: friction
category: other
target: "justfile lint-check"
skill: spec-plan
agent: claude-code
origin: agent
severity: noise
recurring: false
status: dismissed
created_at: 2026-10-13
---

# [FB-ruff-formats-plan-snippets] ruff format checks the Python snippets of spec plans

## 1. Friction / Question (friction, question)

- **Context**: Writing an illustrative data-contract block in plan.md, as the spec-plan output standard suggests
- **Expectation**: A plan snippet is non-normative documentation
- **Actual**: `just ci` failed: `ruff format --check .` formats Python code blocks in Markdown, specs/ included
- **Workaround (or Interpretation Chosen)**: Rewrote the snippet in ruff's format
- **Suggestion**: Exclude specs/ (and docs/) from ruff format, or accept it and note it in docs/development/workflow.md

## Evidence

```text
1 file would be reformatted, 224 files already formatted
error: recipe `lint-check` failed on line 20 with exit code 1
```

- **Disposition**: `just lint` formats the snippets automatically and keeps them valid Python; no exclusion needed
