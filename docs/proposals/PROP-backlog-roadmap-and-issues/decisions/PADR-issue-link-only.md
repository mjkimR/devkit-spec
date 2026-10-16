---
id: PADR-issue-link-only
title: Issue link only, no tracker sync
summary: A Unit may record the GitHub issue it serves in an issue field carried on handoff and closed by the dev PR; devkit-spec neither syncs issues nor milestones with GitHub nor requires an issue, and open feedback stays the intake for follow-ups.
proposal: PROP-backlog-roadmap-and-issues
status: draft
created_at: 2026-10-16
---

# [PADR-issue-link-only] Issue link only, no tracker sync

- **Status**: Draft
- **Date**: 2026-10-16
- **Involved Components/Capabilities**: `CAP-DLV-proposal-incubation`, `CAP-DLV-spec-bundles`,
  `CAP-HARN-agent-guidance`
- **Parent**: `PADR-roadmap-in-repository`

---

## 1. Context & Problem Statement

The strategy layer's master flow relies on GitHub issues to keep the link to an original request after a
decomposition (§5.2) or a close by supersede (§7.4), but the issue ↔ Unit rule is a TODO (§5). With the roadmap in the
repository (`PADR-roadmap-in-repository`), an issue is no longer the plan; it remains where people outside the agent
session file requests.

---

## 2. Decision Drivers

- Keep the link to the original request across handoff, decomposition and supersede.
- No third copy of the plan: autohub already syncs Work Plans to issues one way.
- Work without GitHub must keep working; no network access in rules.
- Small follow-ups found during work already have a reviewed intake: open feedback.

---

## 3. Considered Options

### Option 1: No link
- **Cons**: the original request is lost after handoff and decomposition.

### Option 2: Link only (Selected)
- **Overview**: an optional `issue` field on the Unit and `Closes #<n>` in the dev PR.
- **Pros**: one-way, small, offline-readable.
- **Cons**: an issue edited on GitHub does not update the Unit, by design.

### Option 3: Two-way sync of issues and milestones
- **Cons**: a third copy of the plan beside the repository and autohub; network access and conflict rules.

---

## 4. Decision Outcome

Option 2:

- **Field**: optional `issue` in `proposal.md` and `spec.md`: the issue number in the repository's own GitHub
  repository (`issue: 42`). `devkit spec proposal new --issue` and `devkit spec new --issue` set it; the handoff
  carries it. No rule checks that the issue exists.
- **Closing**: `spec-integrate` writes `Closes #<n>` into the dev PR body when the spec has an `issue`. A local merge
  without a PR leaves the issue open and the final report says so.
- **Decomposition and supersede**: the original issue becomes the parent; each resulting Unit links its own child
  issue, or the parent when no child is made.
- **`session` depth**: no Unit, so the PR body carries `Closes #<n>`.
- **Intake**: an issue is never required. A follow-up found during work is recorded as feedback by default; a request
  from outside may arrive as an issue, and Backlog links it when it creates the Unit.
- **Not done here**: creating issues or milestones, importing issue bodies, any sync. GitHub lookup commands, if
  needed later, are considered for devkit, since tracker access is not specific to spec-driven development.

---

## 5. Consequences

- `CAP-DLV-proposal-incubation` and `CAP-DLV-spec-bundles` document `issue`; the frontmatter format rule accepts it.
- The `spec` skill's Backlog procedure and `spec-integrate` gain the linking and closing steps.
- The strategy layer's §5 TODO "issue ↔ Unit link" is resolved by this rule.
