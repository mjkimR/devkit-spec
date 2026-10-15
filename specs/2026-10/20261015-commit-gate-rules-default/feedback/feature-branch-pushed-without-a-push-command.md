---
id: FB-feature-branch-pushed-without-a-push-command
title: A devkit feature branch reached the remote although no push was run
scope: unknown
kind: question
category: other
target: devkit repository Git hooks and settings (post-commit, push.autoSetupRemote)
skill: none
agent: claude-code
origin: agent
severity: noise
recurring: false
status: open
created_at: 2026-10-15
---

# [FB-feature-branch-pushed-without-a-push-command] A devkit feature branch reached the remote although no push was run

Nature: an outward-facing Git action happened without an explicit command; its cause was not verified.

## 1. Friction / Question (friction, question)

- **Context**: Building the `rules-check` gate on a local branch of the devkit repository before asking the user to
  merge.
- **Expectation**: nothing leaves the machine before the user authorizes a push.
- **Actual**: after two local commits, `origin/rules-commit-gate` existed with the branch head; its reflog entry is
  "update by push". The only pushes run were of `main`, after authorization. The repository has `10-cgate` in
  `post-commit.d`, `push.autoSetupRemote=true` and a `branch.<name>.vscode-merge-base` entry.
- **Workaround (or Interpretation Chosen)**: reported it to the user; left the remote branch in place.
- **Suggestion**: a hygiene session should confirm what pushed it (a post-commit hook or an editor's sync) and, if it
  is intended, say so in the repository's agent guide so agents treat feature commits there as published.

## Diagnostic Details

- **Reproduction**: unknown; observed once.
- **Expected / Actual**: expected no remote branch; actual `refs/heads/rules-commit-gate` at `bc14046` on `origin`.
- **Versions**: cgate version unknown; devkit `bc14046`.
- **Conditions**: devkit checkout under the workbench, branch created with `git switch -c`.
- **Workarounds Attempted**: not applicable.
- **Related Assets**: devkit `.git/hooks/post-commit.d/10-cgate`, Git config.

## Evidence

```text
$ git status -sb   -> ## rules-commit-gate...origin/rules-commit-gate
$ git reflog show origin/rules-commit-gate   -> bc14046 refs/remotes/origin/rules-commit-gate@{0}: update by push
$ git config --get push.autoSetupRemote   -> true
branch.rules-commit-gate.vscode-merge-base origin/main
```
