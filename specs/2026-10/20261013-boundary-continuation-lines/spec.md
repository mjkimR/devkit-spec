---
id: SPEC-boundary-continuation-lines
title: Boundary continuation lines
summary: "Joins the indented continuation lines of a tasks.md _Boundary value to it, so entrypoint derivation and the work scope registry read every path a wrapped boundary declares."
status: completed
created: 2026-10-13
related_capabilities:
  - CAP-TRACE-code-entrypoints
  - CAP-COLL-work-scope-registry
related_stories: []
workflow: direct-delivery
workflow_hash: sha256:6fe2644b9464ea860e6d6928748778b4ffd7a255e92ddea5fe10eba59138f287
---

# [SPEC-boundary-continuation-lines] Boundary continuation lines

## 1. Problem Statement & Motivation

`CAP-TRACE-code-entrypoints` reads every `_Boundary` line of `tasks.md`, and the work scope registry
(`CAP-COLL-work-scope-registry`) reads the same parse. Only the label line is read: a boundary wrapped over several
lines, as Markdown renders it as one value, silently loses the paths on its continuation lines. In
`SPEC-feedback-list-filters` three of a task's four paths dropped out of `devkit spec entrypoints derive` and the
registry without a notice. specrig had the same gap. The direction gate chose to join continuation lines (G2).

## 2. User Stories

- **US-1**: As an agent writing `tasks.md`, I want a long `_Boundary` wrapped over lines to count in full, so that
  derived entrypoints and the work scope registry hold every path I declared.

## 3. Non-Goals

1. **Scope Excluded**: lazy continuation lines (not indented deeper than the label line), and boundaries continued
   after a blank line.
   - **Rationale**: a line at the label's indentation or after a blank line starts another block in a task list.
2. **Scope Excluded**: other labels (`_Requirements:`, `**Verification**`); `RULE-task-coverage` reads
   `_Requirements` on its own.

## 4. Acceptance Criteria & Behavioral Contracts

### [AC-01] Indented continuation lines join the value
- **Given** a task whose `  - **_Boundary**: src/a.py,` line is followed by `    src/b.py,` and `    src/c.py`
- **When** `tasks.md` is parsed (`devkit spec entrypoints derive --spec <dir>`)
- **Then** the task's boundary entries are `src/a.py`, `src/b.py` and `src/c.py`, in order

### [AC-02] A continuation ends at a list item, a blank line or a shallower line
- **Given** the same boundary followed by `    - _Requirements: AC-01_`, and a second task whose boundary is followed
  by a blank line and an indented paragraph, and a third whose boundary is followed by a line at its own indentation
- **When** `tasks.md` is parsed
- **Then** none of those following lines adds an entry

### [AC-03] The work scope registry reads the joined value
- **Given** a registered spec whose `tasks.md` wraps a boundary over three lines
- **When** the agent runs `devkit spec scope register --spec <dir>` (or `scope update`)
- **Then** the record's declared code scopes hold all three paths

### [AC-04] The spec-tasks skill states the form
- **Given** the `spec-tasks` skill
- **When** an agent reads how to write `_Boundary`
- **Then** it says a value may wrap onto lines indented deeper than the label line, and that anything else ends it
