---
id: FB-projected-roles-need-a-session-in-the-project
title: Projected role agents are unavailable when the host session is rooted outside the project
scope: repo
kind: friction
category: missing-capability
target: src/devkit_spec/bundle/skills/spec-delegate/references/hosts.md
skill: spec-delegate
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: promoted
created_at: 2026-10-15
---

# [FB-projected-roles-need-a-session-in-the-project] Projected role agents are unavailable when the host session is rooted outside the project

## 1. Friction / Question (friction, question)

- **Context**: Delegating `review-refine` to the `reviewer` role from a Claude Code session started in a parent
  workspace that holds this repository as a child checkout.
- **Expectation**: `hosts.md` says the role is the subagent named `<role>` from `.claude/agents/<role>.md`.
- **Actual**: Claude Code loads project agents from the session's root, so `reviewer` (and the new `worker`) were not
  offered; the projected files exist only in the child repository and its worktrees.
- **Workaround (or Interpretation Chosen)**: Spawned a general-purpose subagent and told it to read the managed
  contract (`.devkit/managed/spec/subagents/reviewer.md`) and follow it, which is the `emulated` path.
- **Suggestion**: State in `hosts.md` that a projected role needs a session rooted in the project, and that otherwise
  the caller spawns a generic subagent with the managed contract path (and reports `emulated`). Relevant to
  `PROP-worktree-host-compatibility`, since a worker in a sibling worktree has the same root question.

## Diagnostic Details

- **Reproduction**: Start Claude Code in a directory above the project; list the available agent types.
- **Expected / Actual**: Expected `reviewer`; actual only built-in and user-level agent types.
- **Versions**: claude-code version unknown; devkit-spec `d75e673`.
- **Conditions**: session root is a parent workspace; repository checked out below it.
- **Workarounds Attempted**: general-purpose subagent with the managed contract; it returned a valid review.
- **Related Assets**: `spec-delegate/references/hosts.md`, `.claude/agents/reviewer.md`, `.claude/agents/worker.md`.

## Evidence

```text
hosts.md: | Claude Code | The subagent named `<role>` (Agent tool or `@agent-<role>`) | `.claude/agents/<role>.md` |
$ ls .claude/agents   -> challenger.md reconciler.md reviewer.md scout.md worker.md   (in the repository)
Agent types offered to the session: claude, claude-code-guide, Explore, general-purpose, Plan, statusline-setup
```

- **Disposition**: S-Lane: `spec-delegate/references/hosts.md` states the session-root condition and the emulated fallback; `PROP-worktree-host-compatibility` Q5 covers it for workers.
