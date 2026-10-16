---
id: PROP-backlog-roadmap-and-issues-target
title: Target Living Spec Structure for PROP-backlog-roadmap-and-issues
status: draft
proposal: PROP-backlog-roadmap-and-issues
created_at: 2026-10-16
# The Living Spec files this proposal changes, one "- file: <workspace-relative path>" each;
# devkit spec scope compare reads them to find overlaps with other work.
targets:
  - file: docs/capabilities/documents/CAP-DOCS-document-model.md
  - file: docs/capabilities/documents/CAP-DOCS-document-lookup.md
  - file: docs/capabilities/governance/CAP-GOV-spec-rules.md
  - file: docs/capabilities/delivery/CAP-DLV-proposal-incubation.md
  - file: docs/capabilities/delivery/CAP-DLV-spec-bundles.md
  - file: docs/capabilities/harness/CAP-HARN-agent-guidance.md
  - file: docs/stories/delivery/US-route-development-intent.md
  - file: docs/architecture/ARCH-01-introduction-and-goals.md
---

# [Blueprint] PROP-backlog-roadmap-and-issues: Target Living Spec Structure for Backlog: goals, roadmap and issue tracking

This document defines the target blueprint of how the docs/ backbone (Living Spec) will evolve if proposal PROP-backlog-roadmap-and-issues is accepted. It represents a hypothesis plan subject to adjustment during implementation. Upon handoff, it is copied into specs/ to serve as a baseline for plan.md boundaries and reconcile.md targets.

---

## 1. System Capabilities Plan (docs/capabilities/)

- **`CAP-DOCS-document-model`** (modify): kind `milestone` with prefix `MS` and location `docs/roadmap/`; `milestone`
  joins the single-ID relation fields, `depends_on` the list relation fields.
- **`CAP-DOCS-document-lookup`** (modify): `devkit spec list milestone`; sorting and grouping by frontmatter fields
  (`priority`, `milestone`).
- **`CAP-GOV-spec-rules`** (modify): `RULE-id-convention` knows the milestone location; a `depends_on` cycle is an
  error; the format rule accepts `issue`; the milestone status warnings in the hygiene profile.
- **`CAP-DLV-proposal-incubation`** (modify): `milestone` is an `MS-` ID; new optional `issue`; both carried on
  handoff; `new` takes `--issue`.
- **`CAP-DLV-spec-bundles`** (modify): `spec.md` accepts `milestone` as an `MS-` ID and `issue`; `devkit spec new`
  takes `--milestone` and `--issue`.

---

## 2. User Stories Plan (docs/stories/)

- **`US-route-development-intent`** (modify): Backlog acceptance criteria for placing work in a milestone, linking an
  issue, and the idle next-work recommendation; or a new story in the delivery area, working name "choose the next
  work", if the criteria outgrow it.

---

## 3. Architecture & Decision Impact (docs/architecture/ & docs/decisions/)

- **`ARCH-01-introduction-and-goals`** (modify): states that the roadmap lives in `docs/roadmap/` and that milestones
  cite the goals of §1.2.
- **ADRs promoted on handoff**: `PADR-roadmap-in-repository`, `PADR-milestone-documents`, `PADR-issue-link-only`.

---

## 4. Development Conventions & Governance (docs/development/ & .devkit/)

- **`CAP-HARN-agent-guidance`** (modify): the `spec` skill's classification reference gains the Backlog procedure;
  `spec-next` gains the idle next-work row; `spec-integrate` writes `Closes #<n>`; a milestone template; the docs
  skeleton gains `docs/roadmap/`.
- **Outside this repository**: the strategy layer's 01 §1, §5 and glossary, and 02's responsibilities (workbench), are
  updated first.

---

## 5. System Before & After Comparison (Before & After)

| Question | Before | After |
| :--- | :--- | :--- |
| Which goal does this proposal serve? | Not recorded | Its milestone, which cites the goal |
| What should I work on next? | `spec-next` stops at "Idle" | `spec-next` recommends a draft by milestone, priority and size |
| Which milestones come first? | Undefined | `depends_on` on each successor; ready when its dependencies are `done` |
| Where is the original request of this spec? | Lost after handoff or decomposition | `issue` in `spec.md`; parent/child issues for splits |
| What does milestone "Phase 1" mean? | Undefined free text | `MS-<slug>`, a validated document with an exit condition |
