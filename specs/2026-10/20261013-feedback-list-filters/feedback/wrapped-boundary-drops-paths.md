---
id: FB-wrapped-boundary-drops-paths
title: "A wrapped _Boundary line silently drops its continuation paths"
scope: bundle
kind: friction
category: tool-error
target: "src/devkit_spec/entrypoints/bundle.py"
skill: spec-sync
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: open
created_at: 2026-10-13
---

# [FB-wrapped-boundary-drops-paths] A wrapped _Boundary line silently drops its continuation paths

## 1. Friction / Question (friction, question)

- **Context**: Deriving entrypoints for a task whose `_Boundary` listed four paths over four lines
- **Expectation**: spec-tasks asks for the paths a task touches; nothing says the value must fit one line
- **Actual**: `parse_boundaries` reads only the `_Boundary:` line itself; the three paths on continuation lines were dropped from `entrypoints derive` and the scope registry, with no notice
- **Workaround (or Interpretation Chosen)**: Rewrote the boundary as one long line
- **Suggestion**: Either fold indented continuation lines into the boundary value, or report them (a RULE-task-coverage or derive notice); and state the one-line form in spec-tasks

## Evidence

```text
[PAIR: CAP-DOCS-document-lookup code=src/devkit_spec/bundle/skills/spec-next/SKILL.md ... task=4 state=new]
(only 1 of the 4 Task 2.1 paths before the fix; 4 after joining the lines)
```
