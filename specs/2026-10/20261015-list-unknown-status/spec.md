---
id: SPEC-list-unknown-status
title: Flag an unknown status filter in devkit spec list
summary: "devkit spec list adds a SPEC_LIST_STATUS_UNKNOWN notice naming each --status value no document of the selected kinds carries, with the statuses that do occur, so a mistyped filter is not read as an empty result."
status: completed
created: 2026-10-15
related_capabilities:
  - CAP-DOCS-document-lookup
related_stories:
  - US-find-the-right-documents
workflow: direct-delivery
workflow_hash: sha256:6fe2644b9464ea860e6d6928748778b4ffd7a255e92ddea5fe10eba59138f287
---

# [SPEC-list-unknown-status] Flag an unknown status filter in devkit spec list

## 1. Problem Statement & Motivation

`devkit spec list spec --status bogus` prints an empty page and exits `0`. A mistyped or wrong-vocabulary status
(`done` for `completed`, `open` on a kind that has no such status) looks exactly like "no document is in this
state". Status vocabularies are not fixed in code: they come from the document templates, which a project may
override, so the command cannot validate against a closed list. It can compare the requested values with the
statuses the selected kinds actually carry.

## 2. User Stories

- **US-1**: As an agent browsing documents by status, I want to be told when a status I filter by occurs on no
  document of those kinds, together with the statuses that do occur, so that I correct the filter instead of
  concluding nothing matches.

## 3. Non-Goals

1. **Scope Excluded**: refusing the command or changing its exit code; the filter result stays as it is.
   - **Rationale**: a valid status that no document carries yet (for example `deprecated`) must not fail.
2. **Scope Excluded**: a per-kind status vocabulary in code or configuration.
   - **When to Reconsider**: if templates gain a machine-readable status list.
3. **Scope Excluded**: the same check for `--where status=...`, `--area` or other filters, and for other commands
   (`search`, `entrypoints --status`).

## 4. Acceptance Criteria & Behavioral Contracts

### [AC-01] An unknown status gets a notice
- **Given** a workspace whose spec documents carry the statuses planned and completed
- **When** `devkit spec list spec --status bogus` runs
- **Then** stdout is the same page as before (`total=0`), stderr carries one `[NOTICE]` with code
  `SPEC_LIST_STATUS_UNKNOWN` naming `bogus` and listing `completed, planned` in its `[FIX]`, and the command exits
  `0`

### [AC-02] The JSON format carries the notice
- **Given** the workspace of AC-01
- **When** `devkit spec list spec --status bogus --format json` runs
- **Then** the command exits `0` and the `notices` array holds one object with code `SPEC_LIST_STATUS_UNKNOWN`

### [AC-03] Only the unknown values are named
- **Given** the workspace of AC-01
- **When** `devkit spec list spec --status Planned,bogus` runs
- **Then** the planned specs are listed as before (comparison stays case-insensitive) and the notice names
  `bogus` only

### [AC-04] Statuses outside the shown selection still count as known
- **Given** a workspace where only a completed (historical) spec carries the status completed
- **When** `devkit spec list spec --status completed` runs without `--history`, or the status occurs only in another
  namespace
- **Then** no `SPEC_LIST_STATUS_UNKNOWN` notice is printed

### [AC-05] Without kinds every document counts
- **Given** a workspace where only feedback documents carry the status open
- **When** `devkit spec list --status open` runs, and then `devkit spec list spec --status open`
- **Then** the first prints no `SPEC_LIST_STATUS_UNKNOWN` notice and the second prints one naming `open`
