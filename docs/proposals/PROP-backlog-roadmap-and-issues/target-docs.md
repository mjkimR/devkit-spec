---
id: PROP-backlog-roadmap-and-issues-target
title: Target Living Spec Structure for PROP-backlog-roadmap-and-issues
status: draft
proposal: PROP-backlog-roadmap-and-issues
created_at: 2026-10-16
# The Living Spec files this proposal changes, one "- file: <workspace-relative path>" each;
# devkit spec scope compare reads them to find overlaps with other work.
targets:
  - file: docs/capabilities/delivery/CAP-DLV-proposal-incubation.md
  - file: docs/capabilities/delivery/CAP-DLV-spec-bundles.md
  - file: docs/capabilities/harness/CAP-HARN-agent-guidance.md
  - file: docs/capabilities/documents/CAP-DOCS-document-lookup.md
  - file: docs/stories/delivery/US-route-development-intent.md
  - file: docs/architecture/ARCH-01-introduction-and-goals.md
---

# [Blueprint] PROP-backlog-roadmap-and-issues: Target Living Spec Structure for Backlog: goals, roadmap and issue tracking

This document defines the target blueprint of how the docs/ backbone (Living Spec) will evolve if proposal PROP-backlog-roadmap-and-issues is accepted. It represents a hypothesis plan subject to adjustment during implementation. Upon handoff, it is copied into specs/ to serve as a baseline for plan.md boundaries and reconcile.md targets.

The plan below assumes option (c) of the proposal's Q1 (goals in the repository, milestones and issues in GitHub).

---

## 1. System Capabilities Plan (docs/capabilities/)

- **`CAP-DLV-proposal-incubation`** (modify): `milestone` gets a defined meaning (a GitHub milestone title) and a new
  `issue` field joins the frontmatter; both are carried to `spec.md` on handoff. `new` takes `--issue`.
- **`CAP-DLV-spec-bundles`** (modify): `spec.md` accepts `issue` next to `milestone` for spec-depth work that starts
  without a proposal (`devkit spec new --issue`).
- **`CAP-DOCS-document-lookup`** (modify): `devkit spec list` sorts and groups by frontmatter fields (`priority`,
  `milestone`), if Q5 settles on it.
- **New capability in the delivery area, working name "backlog"** (if Q7 keeps tracker access in this package): the
  Backlog procedure's tool surface (issue and milestone lookup, the milestone check of Q4) and its output contract.

---

## 2. User Stories Plan (docs/stories/)

- **`US-route-development-intent`** (modify): Backlog acceptance criteria for registering a request as an issue,
  placing it in a milestone and linking the draft.
- **New story, working name "choose the next work"**: an agent at an idle repository recommends the next draft from the
  open milestones by priority, with the goal it serves.

---

## 3. Architecture & Decision Impact (docs/architecture/ & docs/decisions/)

- **`ARCH-01-introduction-and-goals`** (modify): goals get stable IDs (Q2) and the section states where the roadmap
  lives.
- **`ARCH-03-context`** (modify, if Q7 keeps tracker access here): GitHub issues and milestones as an external system.
- **Candidate ADRs** (from PADRs): owner of each planning fact (Q1); the issue ↔ Unit link (Q3).

---

## 4. Development Conventions & Governance (docs/development/ & .devkit/)

- **`CAP-HARN-agent-guidance`** (modify): the `spec` skill's classification reference gains the Backlog procedure;
  `spec-next` gains the idle next-work row; `spec-integrate` writes `Closes #<n>` into the PR body.
- **Rules**: the frontmatter format rule accepts `issue`; the milestone check of Q4 is a hygiene warning, not a rule.
- **Outside this repository**: the strategy layer's 01 §5 and glossary (workbench) are updated first.

---

## 5. System Before & After Comparison (Before & After)

| Question | Before | After |
| :--- | :--- | :--- |
| Which goal does this proposal serve? | Not recorded | Its milestone, and the goal the milestone serves |
| What should I work on next? | `spec-next` stops at "Idle" | `spec-next` recommends a draft by milestone and priority |
| Where is the original request of this spec? | Lost after handoff or decomposition | `issue` in `spec.md`; parent/child issues for splits |
| What does milestone "Phase 1" mean? | Undefined free text | A GitHub milestone with an exit condition |
