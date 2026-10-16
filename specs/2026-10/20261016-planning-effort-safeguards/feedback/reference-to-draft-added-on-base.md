---
id: FB-reference-to-draft-added-on-base
title: A Planning branch cannot cite a draft proposal added to the base after it branched
scope: repo
kind: friction
category: other
target: RULE-document-reference
skill: spec
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: promoted
created_at: 2026-10-16
---

# [FB-reference-to-draft-added-on-base] A Planning branch cannot cite a draft proposal added to the base after it branched

Branch timing, not a wrong ID: the cited draft existed, only on the base.

## 1. Friction / Question (friction, question)

- **Context**: Planning of `PROP-backlog-roadmap-and-issues` on its `plan-` branch. Meanwhile Backlog added the draft
  proposal for direct acceptance to the base (Backlog commits go to the base directly).
- **Expectation**: The Planning branch could cite the new draft by its full ID, as the constitution asks.
- **Actual**: The commit gate refused the PADR: `RULE-document-reference` reported that no document has that ID,
  because the branch predates the draft.
- **Workaround (or Interpretation Chosen)**: Wrote the slug without the `PROP-` prefix in prose instead of the ID; the
  alternative was merging the base into the Planning branch mid-Planning.
- **Suggestion**: State in the `spec` skill's branches or classification reference how a Planning branch cites a
  Backlog item added after it started (integrate the base first, or cite the slug), or let the rule accept a
  `PROP-` ID that resolves on the base branch with a warning.

## Diagnostic Details

- **Reproduction**: Start `plan-<a>`; add draft `PROP-<b>` on the base; cite `` `PROP-<b>` `` on `plan-<a>`; commit.
- **Expected / Actual**: Expected the reference to pass; actual `RULE-document-reference ... no document has the ID`.
- **Versions**: devkit-spec base `3c175b1`..`81da247` (2026-10-16).
- **Conditions**: Backlog work committed to the base while a Planning branch was open; worktree mode.
- **Workarounds Attempted**: Slug in prose (succeeded); merging the base was done later for the finish anyway.
- **Related Assets**: `RULE-document-reference`, `docs/proposals/PROP-backlog-roadmap-and-issues/decisions/PADR-roadmap-in-repository.md`.

## Evidence

```text
[VIOLATION: RULE-document-reference ... PADR-roadmap-in-repository.md line=86 message="no document has the ID PROP-draft-direct-acceptance"]
```

- **Disposition**: `src/devkit_spec/bundle/skills/spec/references/branches.md` §3: a document added to the base after the branch started is cited by ID after merging the base, otherwise by slug in prose; the rule is unchanged.
