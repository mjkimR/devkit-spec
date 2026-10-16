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
task_kind: feature                    # feature | bugfix: the spec follows sdd-spec-<task_kind>
workflow: sdd-proposal
workflow_hash: sha256:79420190142b779136c39c7edcfd2aac42abf8c250f21bfffc46f8172777e1f9
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
  directories, Antigravity workspace settings), and can `devkit sync` project it without per-user setup? Workers commit
  their build (`ADR-worker-delivers-committed-result`), so the access includes the Git common directory of a linked
  worktree, not only the worktree directory.
- **Q2**: Does a worktree inside the repository (for example under an ignored `.devkit/` path) avoid the sandbox
  limits, and what breaks: project discovery climbing to the base, `rg` and tool scans, scope registry attribution,
  `devkit worktree` path conventions and cleanup?
- **Q3**: Is a separate worker process started in the worktree (a headless host session with that directory as its
  root) viable for each host, and how does it return the envelope fields and keep the host's diff check?
- **Q4**: Can a host-native worktree isolation be adopted and registered with devkit (scope registry, setup, sync,
  `finish`) instead of `devkit worktree start`, or does it stay excluded?
- **Q5**: Projected roles load only in a session rooted in the project; a session started in a parent workspace has
  no `worker` subagent. Does the chosen option also cover that case, or does the caller always emulate there?
- **Q6**: Which repository Git settings help across hosts and sandboxes: `worktree.useRelativePaths` (and the
  `extensions.relativeWorktrees` it enables) so worktrees survive another mount path, `extensions.worktreeConfig` for
  per-worktree settings? What Git version does every tool reading the repository need, and should devkit set or check
  them (`[worktree]` config, `devkit worktree start`) for a repository that opts in? A personal repository can meet
  such conditions even where the defaults could not be assumed.
- **Q7**: How do the hosts' own worktree flows fit devkit's: Claude Code `isolation: worktree` subagents with
  `WorktreeCreate`/`WorktreeRemove` hooks and `worktree.baseRef`, and the ChatGPT Codex app's managed worktrees
  (detached HEAD, handoff between local and worktree, `.worktreeinclude`, `.codex` local environment setup scripts)?
  Desk research: `MAT-host-worktree-flows`.

## 3. Proposed Design & Impact

Options to compare after the spike:

- **O1, host access configuration**: project the extra-directory permission per host from devkit; worktrees stay
  where they are.
- **O2, worktree inside the repository**: change the worktree location so every sandbox covers it.
- **O3, worker process per worktree**: start the worker as its own host session rooted in the worktree.
- **O4, host-native isolation**: let the host create the worktree and register it with devkit. On Claude Code a
  `WorktreeCreate` hook could run `devkit worktree start` and hand its path to `isolation: worktree` subagents.
- **O5, repository Git settings**: an opt-in repository profile (for example relative worktree paths) that devkit
  sets or checks, alone or combined with O1 to O4.

Impact depends on the choice: the worker contract's host blocks and `spec-delegate` (all options), devkit's
`worktree` path convention and config (O2, O4, O5), the distribution projections (O1, O4 hooks), and a worker launch
procedure (O3).

## 4. Lifecycle & Retirement Criteria

- Restart condition: `SPEC-orchestration-mode` integrated with its Claude Code path working.
- Expected acceptance checks: a worker on each host the chosen option supports writes only inside its worktree and
  the host's diff check passes; the worker contract's host statuses match the verified behavior.
- On acceptance: set `status: accepted` and run `devkit spec proposal handoff worktree-host-compatibility`. On
  rejection: record a rejection ADR and delete the proposal directory.
