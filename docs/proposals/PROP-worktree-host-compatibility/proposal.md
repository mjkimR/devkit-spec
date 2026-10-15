---
id: PROP-worktree-host-compatibility
title: Worktree access for subagents across hosts
summary: "Investigate how worker subagents on Claude Code, Codex and Antigravity can read, write and run commands in a sibling devkit worktree, and choose a portable approach for orchestration mode."
status: draft                         # draft | reviewing | accepted | rejected
created_at: 2026-10-15
target_area: delivery/
priority: medium                      # critical | high | medium | low
size: M                               # S | M | L | XL
boundaries:
  owns:
    - delivery/
  excludes:
    - docs/decisions/
workflow: incubated-delivery
workflow_hash: sha256:c6cf386f9eb37b061d626d4bc701dd4e01f43674666d160179f69da5c391463e
---

# [PROP-worktree-host-compatibility] Worktree access for subagents across hosts

## 1. Background & Hypothesis

`SPEC-orchestration-mode` has worker subagents implement in their own devkit worktree
(`<parent of base>/<base name>-wt-<slug>`). Its spike found that no host gives a subagent its own working directory:
on Claude Code a worker shares the session's directory and must use absolute paths and `git -C`, and the session must
already allow the sibling path; Codex `workspace-write` confines writes to the project root, which excludes the
sibling worktree; Antigravity has no documented working-directory control. Orchestration mode therefore starts as
Claude Code `native`, Codex `unsupported` (the main session substitutes) and Antigravity `unverified`.

Hypothesis: a documented host mechanism, a different worktree location or a separate worker process makes worker
delegation work on every supported host without weakening the post-run diff check.

## 2. Technical Spike Questions

- **Q1**: Per host, what documented mechanism grants a subagent (or the session) read, write and command access to an
  extra directory (Claude Code permission settings for additional directories, Codex writable roots or added
  directories, Antigravity workspace settings), and can `devkit sync` project it without per-user setup?
- **Q2**: Does a worktree inside the repository (for example under an ignored `.devkit/` path) avoid the sandbox
  limits, and what breaks: project discovery climbing to the base, `rg` and tool scans, scope registry attribution,
  `devkit worktree` path conventions and cleanup?
- **Q3**: Is a separate worker process started in the worktree (a headless host session with that directory as its
  root) viable for each host, and how does it return the envelope fields and keep the host's diff check?
- **Q4**: Can a host-native worktree isolation be adopted and registered with devkit (scope registry, setup, sync,
  `finish`) instead of `devkit worktree start`, or does it stay excluded?
- **Q5**: Projected roles load only in a session rooted in the project; a session started in a parent workspace has
  no `worker` subagent. Does the chosen option also cover that case, or does the caller always emulate there?

## 3. Proposed Design & Impact

Options to compare after the spike:

- **O1, host access configuration**: project the extra-directory permission per host from devkit; worktrees stay
  where they are.
- **O2, worktree inside the repository**: change the worktree location so every sandbox covers it.
- **O3, worker process per worktree**: start the worker as its own host session rooted in the worktree.
- **O4, host-native isolation**: let the host create the worktree and register it with devkit.

Impact depends on the choice: the worker contract's host blocks and `spec-delegate` (all options), devkit's
`worktree` path convention and config (O2, O4), the distribution projections (O1), and a worker launch procedure (O3).

## 4. Lifecycle & Retirement Criteria

- Restart condition: `SPEC-orchestration-mode` integrated with its Claude Code path working.
- Expected acceptance checks: a worker on each host the chosen option supports writes only inside its worktree and
  the host's diff check passes; the worker contract's host statuses match the verified behavior.
- On acceptance: set `status: accepted` and run `devkit spec proposal handoff worktree-host-compatibility`. On
  rejection: record a rejection ADR and delete the proposal directory.
