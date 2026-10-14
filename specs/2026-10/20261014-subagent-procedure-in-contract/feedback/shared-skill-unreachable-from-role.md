---
id: FB-shared-skill-unreachable-from-role
title: Reviewer and reconciler projections name a skill the subagent cannot load
scope: bundle
kind: suggestion
category: instruction-conflict
target: src/devkit_spec/bundle/subagents/reconciler.md
skill: spec-delegate
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: open
created_at: 2026-10-14
---

# [FB-shared-skill-unreachable-from-role] Reviewer and reconciler projections name a skill the subagent cannot load

## 2. Suggestion / Change Request (suggestion, change-request)

- **Current Procedure**: The projection header says "Procedure: skill `spec-review`" (or `spec-sync`). The Claude Code projection lists `tools` without the Skill tool and sets no `skills:` preload, so the subagent has to find `.claude/skills/<skill>/SKILL.md` by itself. The projected skill starts with a `uv run devkit get-context spec` prerequisite, which the reconciler (no shell) cannot run.
- **Proposed Procedure**: Either set the Claude Code `skills:` host key (and Antigravity `skills`) for these two roles, or name the skill's file path in the contract body and tell the role to read `.devkit/managed/spec/AGENTS.md` instead of running `get-context`. Preloading the whole `spec-sync` brings in confirmation steps the reconciler must not take, so the path-plus-section pointer may fit it better.
- **Expected Benefit**: The role reaches its procedure without a search and without an instruction it cannot follow.
- **Cost & Risk**: Preloading adds about 2k tokens to each subagent spawn; host semantics of `skills:` for Antigravity are unverified.
- **Attempted**: Hypothesis; declared non-goal 4 of `SPEC-subagent-procedure-in-contract`.

## Evidence

```text
.claude/agents/reviewer.md: tools: [Read, Grep, Glob, Bash]; "Procedure: skill `spec-review`."
.claude/agents/reconciler.md: tools: [Read, Grep, Glob, Write, Edit]; "Procedure: skill `spec-sync`."
.claude/skills/spec-sync/SKILL.md: "Before performing this skill, load this bundle's context by running `uv run devkit get-context spec`"
```
