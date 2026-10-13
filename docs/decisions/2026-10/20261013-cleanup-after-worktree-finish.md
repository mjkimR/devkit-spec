---
id: ADR-cleanup-after-worktree-finish
title: Clean up after a finished task through devkit's post-finish extension point
summary: "devkit-spec registers a devkit.post_finish extension that prunes the handed-off proposal's empty directories and removes the finished worktree's scope record after a successful devkit worktree finish, while the skills keep registering and updating the registry."
status: accepted
created_at: 2026-10-13
supersedes: ADR-scope-maintenance-through-skills
---

# [ADR-cleanup-after-worktree-finish] Clean up after a finished task through devkit's post-finish extension point

- **Status**: Accepted
- **Date**: 2026-10-13
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `CAP-COLL-work-scope-registry`, `CAP-DLV-proposal-incubation`,
  `CAP-HARN-agent-guidance`, `ARCH-06-runtime-view`
- **Supersedes**: `ADR-scope-maintenance-through-skills`

---

## 1. Context & Problem Statement

`ADR-scope-maintenance-through-skills` left every registry step to the skills because `devkit worktree finish` could
not call devkit-spec, and rejected extension points in devkit as an extension mechanism for one plugin. In use, the two cleanup
steps after a finish (`devkit spec scope sweep --apply`, `devkit spec proposal prune <slug>`) are exactly the steps an
agent forgets once the merge is done, and a forgotten sweep leaves a stale record every other worktree sees. specrig
ran both inside its own finish.

devkit has since gained a general extension point for this: `devkit.post_finish` entry points, called after a
successful `devkit worktree finish`, under the rules of its `devkit.post_sync` extensions (an extension never fails the command).

---

## 2. Decision Drivers

- Cleanup after a finish runs without a step an agent can skip.
- devkit stays SDD-agnostic: the extension point is general, the cleanup lives in devkit-spec.
- A refused finish never leaves a live task unregistered.

---

## 3. Considered Options

### Option 1: A `devkit.post_finish` extension in devkit-spec (Selected)
- **Overview**: `devkit_spec.cleanup.after_finish` runs after a successful finish, in the base checkout of a project
  that deploys the `spec` bundle: it prunes `docs/proposals/PROP-<slug>/` when empty and removes the scope records of
  the finished worktree, at the revision it read; other stale records wait for `devkit spec scope sweep --apply`.
  Registration (`devkit spec new`, handoff) and updates (`spec-tasks`, `spec-sync`) stay with the skills.
- **Pros**: no manual cleanup step; a refused finish runs no extension, so the task stays registered; the extension removes only
  what the finished task owns.
- **Cons**: an extension failure is a `POST_FINISH_EXTENSION_FAILED` warning the agent has to notice.

### Option 2: A `devkit spec finish` wrapper
- **Overview**: devkit-spec's own command runs `devkit worktree finish`, then the cleanup.
- **Pros**: no devkit change.
- **Cons**: two finish commands; an agent that runs devkit's skips the cleanup.

### Option 3: Keep the cleanup in the skills (`ADR-scope-maintenance-through-skills`)
- **Pros**: no code.
- **Cons**: the cleanup depends on the agent remembering two commands after the merge.

---

## 4. Decision Outcome

We decided to adopt **Option 1**.

**Rationale**: the extension makes cleanup part of the finish an agent already runs, and keeps the safe ordering of the
superseded decision: nothing is removed unless the finish succeeded.

---

## 5. Consequences

- **Positive**: the `spec` skills drop the post-finish cleanup steps; `[NOTICE]` lines (`POST_FINISH_NOTICE`) report
  what the extension removed.
- **Negative / Risks**: the registry is still only as current as the skills' register and update steps; a stale
  record of an abandoned worktree (one never finished) still needs `devkit spec scope sweep --apply` or
  `devkit spec scope release -w <worktree>`.
- **Follow-ups**: none.
