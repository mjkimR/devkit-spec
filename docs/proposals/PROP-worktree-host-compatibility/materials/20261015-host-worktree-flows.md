---
id: MAT-host-worktree-flows
title: Host worktree flows and repository Git settings
created_at: 2026-10-15
---

# [MAT-host-worktree-flows] Host worktree flows and repository Git settings

Desk research before the spike, from the hosts' current documentation and public issue reports. Statements marked
"to verify" are not confirmed against an installed version.

## 1. Claude Code

Source: [Run parallel sessions with worktrees](https://code.claude.com/docs/en/worktrees).

- `claude --worktree <name>` (or the `EnterWorktree` tool) creates `.claude/worktrees/<name>/` inside the repository
  on branch `worktree-<name>`; the docs recommend ignoring `.claude/worktrees/`. Entering a path outside that
  directory asks the user every time.
- **Subagents can run in their own worktree**: `isolation: worktree` in a custom subagent's frontmatter gives each run
  a temporary worktree, removed when the subagent finishes without changes and otherwise kept for a periodic sweep.
  `worktree.baseRef: "head"` (settings) branches it from the current `HEAD` instead of the remote default branch.
- While a session or subagent is isolated, Claude Code refuses edits, command working directories and git redirects
  (`git -C`, `GIT_DIR`, a `cd`) that reach the main checkout. Commits from the worktree work under the sandbox, which
  allows writes to the shared `.git`.
- **`WorktreeCreate` / `WorktreeRemove` hooks** replace the default creation: the hook reads the name on stdin and
  prints the directory to use, also for subagent worktrees. A hook-created directory must not resolve into the main
  checkout; `.worktreeinclude` is not processed then.
- Project skills, agents and commands of the main checkout load in its worktrees when the worktree has no copy.

## 2. ChatGPT (Codex app and CLI)

Sources: [Git worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees),
[Local environments](https://learn.chatgpt.com/docs/environments/local-environment), issue reports linked below.

- The app creates managed worktrees under `$CODEX_HOME/worktrees` (configurable worktree root), in **detached HEAD**
  from the chosen branch, so no branch is created per chat. "Create branch here" turns one into a branch.
- **Handoff** moves a chat between the local checkout and its worktree; Codex runs the Git steps (a branch is checked
  out in one place at a time). Ignored files travel only when listed in `.worktreeinclude`.
- Cleanup keeps the 15 most recent managed worktrees by default and snapshots a worktree before deleting it.
- **Local environments** (`.codex/` at the project root, committable): a setup script runs when a worktree is created
  for a new chat, with per-OS overrides; actions run common commands. App-only.
- Recommended flow in the docs: set up a local environment, start tasks in a worktree, hand off to local when the IDE
  or dev server is needed, then commit, push and open a PR from a branch.
- Codex CLI `workspace-write` denies writes under `.git`; a linked worktree's index and refs live in the common
  `.git`, so a worker there cannot commit. Reported fixes add the common directory
  (`git rev-parse --git-common-dir`) to `sandbox_workspace_write.writable_roots`, or let the orchestrator commit
  ([a write-up](https://gallon.me/letting-codex-agents-commit-making-git-writable-in-the-workspace-write-sandbox.html);
  setup scripts get no variable naming the original repository root:
  [openai/codex#13576](https://github.com/openai/codex/issues/13576)).
  devkit-spec's worker never commits, so only the worktree directory itself must be writable (to verify).

## 3. Repository Git settings

Source: [git-config `worktree.*`](https://code.googlesource.com/git/+/HEAD/Documentation/config/worktree.adoc).
Local Git is 2.49.0.

- `worktree.useRelativePaths = true` links worktrees with relative paths (the worktree's `.git` file and the
  `gitdir` record in `.git/worktrees/<name>/`), so the repository and its worktrees keep working when moved or mounted
  at another path, as long as they move together. It enables `extensions.relativeWorktrees`, which makes the
  repository unreadable for Git versions without the extension (introduced in Git 2.48; to verify per tool).
  `git worktree add --relative-paths` and `git worktree repair --relative-paths` apply it per worktree.
- `extensions.worktreeConfig = true` enables per-worktree configuration (`git config --worktree`, stored in
  `.git/worktrees/<name>/config.worktree`), for settings one worktree needs and the base must not take.
- These are repository settings, not defaults: a personal repository can opt in once, provided every tool that reads
  it (host CLIs, containers, CI images) runs a recent enough Git.

## 4. Consequences for the options

- O4 gains a concrete Claude Code path: a `WorktreeCreate` hook that runs `devkit worktree start` and prints its path
  would let `isolation: worktree` subagents run in devkit worktrees, with Claude Code's isolation checks on top.
  Open: the hook gets a name, not a slug or base; it also replaces creation for `--worktree` sessions; removal and
  `devkit worktree finish` must not conflict.
- O2 matches both hosts' defaults (worktrees inside a project-owned directory). With relative worktree paths the
  repository and its worktrees stay valid when a sandbox or container mounts them elsewhere.
- Codex's flow is branchless (detached HEAD) and app-driven, unlike `devkit worktree start` (branch per slug).
