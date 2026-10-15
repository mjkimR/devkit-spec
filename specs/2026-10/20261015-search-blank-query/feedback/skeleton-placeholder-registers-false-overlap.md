---
id: FB-skeleton-placeholder-registers-false-overlap
title: Scope registration counts the skeleton placeholder <target area> as a declared code scope
scope: repo
kind: friction
category: tool-error
target: devkit spec scope register
skill: spec-orchestrate
agent: claude-code
origin: agent
severity: noise
recurring: false
status: open
created_at: 2026-10-15
---

# [FB-skeleton-placeholder-registers-false-overlap] Scope registration counts the skeleton placeholder <target area> as a declared code scope

## 1. Friction / Question (friction, question)

- **Context**: Orchestration mode, two Route 2 units started back to back: `devkit spec new <slug>` then
  `devkit spec scope register --spec <dir>` in each worktree, then `devkit spec scope query` from the base to schedule
  them, as `spec-orchestrate` §2 and §3 step 1 prescribe.
- **Expectation**: right after registration the bundles declare no real paths, so the query reports no overlap (or
  only unresolved scopes).
- **Actual**: the query reported one code overlap between the two unrelated units, evidenced by the literal skeleton
  placeholder `<target area>` that `devkit spec new` writes into `plan.md` and `tasks.md`
  (`src/devkit_spec/proposals/specs.py:137`). The overlap disappeared once `spec-tasks` replaced the placeholder.
- **Workaround (or Interpretation Chosen)**: read the `[EVIDENCE]` line, judged it a placeholder artifact and kept the
  units parallel; rechecked after `spec-tasks` (`overlapping=0`).
- **Suggestion**: skip skeleton files (the `<!-- devkit:skeleton -->` marker) or angle-bracket placeholders when
  collecting declared scopes, or report them as unresolved, so the overlap check right after registration is
  meaningful for scheduling.

## Diagnostic Details

- **Reproduction**: two `devkit spec new` bundles in two `devkit worktree start` worktrees, `devkit spec scope register`
  in each, `devkit spec scope query`.
- **Expected / Actual**: expected `overlapping=0`; actual `overlapping=1` with `kind=code` evidence `<target area>`.
- **Versions**: devkit 0.1.1; devkit-spec base `ed2dd0d`.
- **Conditions**: both bundles still skeletons (`not-skeleton` unmet).
- **Workarounds Attempted**: rechecked after `spec-tasks`; overlap gone.
- **Related Assets**: `src/devkit_spec/proposals/specs.py`, `src/devkit_spec/scope/`, `spec-orchestrate` §2.

## Evidence

```text
[PAIR: a=SPEC-list-unknown-status b=SPEC-search-blank-query docs=0 code=1 unresolved=2]
[EVIDENCE: "<target area>" a=SPEC-list-unknown-status b=SPEC-search-blank-query kind=code granularity=unknown other="<target area>" source=declared-code other_source=declared-code]
[SUMMARY: namespace=0c908353e6858b2b records=2 pairs=1 overlapping=1 problems=0]
(after spec-tasks) [SUMMARY: namespace=0c908353e6858b2b records=2 pairs=1 overlapping=0 problems=0]
```
