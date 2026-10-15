---
id: FB-review-head-before-any-commit
title: Review envelope head points at the base when the reviewed change is not committed yet
scope: repo
kind: question
category: instruction-conflict
target: src/devkit_spec/bundle/skills/spec-review/SKILL.md
skill: spec-review
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: promoted
created_at: 2026-10-15
---

# [FB-review-head-before-any-commit] Review envelope head points at the base when the reviewed change is not committed yet

## 1. Friction / Question (friction, question)

- **Context**: Recording the review envelope of a Route 2 task in its worktree before any commit, because commits
  wait for the user's authorization.
- **Expectation**: `spec-review` expects the change "committed or staged" and records `--head $(git rev-parse HEAD)`.
- **Actual**: With nothing committed, `HEAD` is the base commit, so `diff_scope` names a range that contains none of
  the reviewed change; the envelope still passes.
- **Workaround (or Interpretation Chosen)**: Recorded head = base and said in the summary that the uncommitted
  worktree diff was reviewed; the cumulative check runs after the commit at integration.
- **Suggestion**: State which evidence applies before the first commit: either require an intermediate commit
  before review (when commit authority exists) or allow a working-tree review with an explicit marker, and say
  that stage evidence is refreshed after the commit.

## Diagnostic Details

- **Reproduction**: Route 2 task without commits; run `spec-review` and record the envelope as documented.
- **Expected / Actual**: Expected head to identify the reviewed content; actual head = base `79b3cb1`.
- **Versions**: devkit-spec base `79b3cb1`; devkit-agt `856f1af`.
- **Conditions**: commit authority not yet granted in the session.
- **Workarounds Attempted**: summary note in `envelopes/review-01.yaml`.
- **Related Assets**: `skills/spec-review/SKILL.md` (Prerequisites, section 3), `devkit workflow envelope new`.

## Evidence

```text
skills/spec-review/SKILL.md: "Working tree with all implementation changes committed or staged."
skills/spec-review/SKILL.md: --base <ref> --head $(git rev-parse HEAD)
$ git rev-parse --short HEAD   -> 79b3cb1 (base; the change is uncommitted)
```

- **Disposition**: S-Lane: `spec-review` prerequisites ask for an intermediate commit before review, and an uncommitted-change assumption in the envelope when a review runs on uncommitted changes.
