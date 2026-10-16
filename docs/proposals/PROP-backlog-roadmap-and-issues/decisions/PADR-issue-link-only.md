---
id: PADR-issue-link-only
title: Issue link only, no tracker sync
summary: A Unit may record the inbound GitHub request issue it serves in an issue field carried on handoff; the issue is closed only when its last linked Unit merges, never names an autohub record issue, and devkit-spec neither syncs issues or milestones nor requires an issue.
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
repository (`PADR-roadmap-in-repository`), the link to an original draft is `decomposed_from` or `supersedes`, and an
issue is where people outside the agent session file requests. autohub also writes issues, one way, as records of its
Work Plans.

---

## 2. Decision Drivers

- An inbound request is closed when the work it asked for is merged, not earlier.
- No third copy of the plan, and no second writer of records autohub owns.
- Work without GitHub must keep working; no network access in rules.

---

## 3. Considered Options

### Option 1: No link
- **Cons**: the request's author sees no outcome, and a reader of a spec cannot find the request.

### Option 2: Link only (Selected)
- **Overview**: an optional `issue` field on the Unit; the merge that finishes the last linked Unit closes it.
- **Pros**: one-way, small, offline-readable.
- **Cons**: an issue edited on GitHub does not update the Unit, by design.

### Option 3: Two-way sync of issues and milestones
- **Cons**: a third copy of the plan beside the repository and autohub; network access and conflict rules.

---

## 4. Decision Outcome

Option 2:

- **Field**: optional `issue` in `proposal.md` and `spec.md`: a positive integer, the number of an issue in the
  repository's own GitHub repository (`issue: 42`). `devkit spec proposal new --issue` and `devkit spec new --issue`
  set it; the handoff carries it; the format rule checks the type. No rule checks that the issue exists.
- **Inbound requests only**: `issue` names an issue someone filed as a request. Issues autohub creates as Work Plan
  records are autohub's one-way records and are never linked or closed from a Unit.
- **Closing**: when a Unit is the last open Unit linking its issue, `spec-integrate` writes `Closes #<n>` into the PR
  body, or into the final commit message on a local merge; otherwise it writes `Refs #<n>`. The open Units are the
  linked slugs other than the integrating one, each counted once across the base and its `plan-` and `dev-` branches,
  that are a draft, a `reviewing` or `accepted` proposal or a spec not completed; rejected proposals do not count. When
  a later sibling is added after a close, Backlog reopens the issue or files a follow-up.
- **Decomposition and supersede**: every resulting draft keeps the original's `issue`; the provenance is
  `decomposed_from` or `supersedes`. No child issues are required.
- **`session` depth**: no Unit; the PR body or the final commit message carries `Closes #<n>`.
- **Intake**: an issue is never required. When `gh` is available, Backlog drains the open issues no Unit links into
  drafts, feedback (closing the issue with the feedback ID) or a declined close, skipping autohub record issues
  (`PADR-roadmap-in-repository`).
- **Not done here**: creating issues or milestones, importing issue bodies, any sync, GitHub lookup commands (if needed
  later, considered for devkit, since tracker access is not specific to spec-driven development).

---

## 5. Consequences

- `CAP-DLV-proposal-incubation` and `CAP-DLV-spec-bundles` document `issue` and `decomposed_from`; the format rule
  checks `issue`'s type.
- The `spec` skill's Backlog procedure and `spec-integrate` gain the linking and closing steps.
- The strategy layer's §5 TODO "issue ↔ Unit link" is resolved by this rule.
