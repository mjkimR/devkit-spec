---
id: FB-policy-change-in-a-task-branch
title: "A Git policy change made in a task branch does not govern that task's finish"
scope: bundle
kind: suggestion
category: missing-capability
target: "spec skill references/worktree.md"
skill: spec
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: open
created_at: 2026-10-13
---

# [FB-policy-change-in-a-task-branch] A Git policy change made in a task branch does not govern that task's finish

## 2. Suggestion / Change Request (suggestion, change-request)

- **Current Procedure**: worktree.md says to integrate per GIT_POLICY; `devkit worktree finish` reads `[worktree]` of the base checkout
- **Proposed Procedure**: State that a change to `[worktree]` or `[tool.spec]` takes effect for the current task only once it is committed in the base; make it there first (an S-Lane) when the task depends on it
- **Expected Benefit**: No refused `finish --merge` (WORKTREE_PR_POLICY) after G3
- **Cost & Risk**: One sentence in worktree.md
- **Attempted**: Tested: switching this repository to pull_request = false was committed in the base before integration

## Evidence

```text
[GIT_POLICY: worktree=yes pull_request=yes delete_branch=yes setup=-]   (base, before the S-Lane)
--merge  Fast-forward the base onto the branch ... ([worktree] pull_request = false)
```
