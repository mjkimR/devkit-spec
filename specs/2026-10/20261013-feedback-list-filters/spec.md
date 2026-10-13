---
id: SPEC-feedback-list-filters
title: Feedback list filters
summary: "Adds a generic repeatable --where KEY=VALUES frontmatter filter to devkit spec list, orders feedback by severity and prints its severity, scope and target, so skills select feedback without opening each file."
status: completed
created: 2026-10-13
related_capabilities:
  - CAP-DOCS-document-lookup
related_stories:
  - US-find-the-right-documents
workflow: direct-delivery
workflow_hash: sha256:6fe2644b9464ea860e6d6928748778b4ffd7a255e92ddea5fe10eba59138f287
---

# [SPEC-feedback-list-filters] Feedback list filters

## 1. Problem Statement & Motivation

Four bundle assets select feedback by severity: the `spec-feedback` sweep (critical count), the `spec-next` skill (critical feedback first), the G3 report of
`envelope.md` (one line per open critical item) and the `feedback-hygiene` playbook (scope or severity the user names,
ordered by severity). `devkit spec list feedback` filters only by the generic fields of `CAP-DOCS-document-lookup`
and prints none of the feedback fields, so each asset tells the agent to list open feedback and then open every file
to read its `severity`, `scope` and `target`. specrig had dedicated `--scope`, `--severity` and `--kind` flags and a
severity order; the port left them out as a non-goal of `CAP-DOCS-document-lookup`.

`devkit spec list` takes the document kind as its positional `KIND`, so a feedback `--kind` flag would collide with
it. A generic frontmatter filter avoids the collision and serves any field (G2 direction, decision 02).

## 2. User Stories

- **US-1**: As an agent orienting in a repository (`US-find-the-right-documents`), I want to list exactly the open
  feedback of a given severity or scope with its target, so that I report or triage it without reading each file.

## 3. Non-Goals

1. **Scope Excluded**: specrig's feedback defaults: listing only `status: open` feedback unless asked, and hiding
   `workaround` and `noise` items without `--all`.
   - **Rationale**: `list` serves every kind in one command, so a feedback-only default would make `list feedback`
     and `list feedback spec` select differently; items hidden without a trace in the output would drop out of the
     G3 report and the hygiene pass. Every current call site already passes `--status open`.
2. **Scope Excluded**: a `--sort` option, and per-kind filters other than `--where` (`--with-story`, `--with-cap`,
   proposal priority and size).
3. **Scope Excluded**: comparison operators, substring or pattern matching in `--where`; it matches whole values.
   - **When to Reconsider**: when an asset needs a field match that whole values cannot express.
4. **Scope Excluded**: changes to the feedback document format, its location rules (`RULE-id-convention`) or the
   `spec-feedback` recording procedure.

## 4. Acceptance Criteria & Behavioral Contracts

The feedback fixtures below carry `severity`, `scope` and `target` frontmatter as the `spec-feedback` template writes
them.

### [AC-01] One --where field keeps the documents whose value is in the list
- **Given** open feedback FB-a (`severity: critical`), FB-b (`severity: blocked`) and FB-c
  (`severity: noise`)
- **When** the agent runs `devkit spec list feedback --where severity=critical,BLOCKED`
- **Then** the output lists FB-a and FB-b and not FB-c, values compared case-insensitively after trimming,
  and the command exits `0`

### [AC-02] Repeated --where options and the other filters combine with AND
- **Given** FB-a (`severity: critical`, `scope: bundle`), FB-d (`severity: critical`, `scope: repo`) and a
  capability without a `severity` field
- **When** the agent runs `devkit spec list --where severity=critical --where scope=bundle --status open`
- **Then** only FB-a is listed: a document lacking the field, or holding it with another value, does not match

### [AC-03] Values match by their parsed form: list elements, booleans and dates
- **Given** feedback with `recurring: true` and `created_at: 2026-10-13`, and a capability with
  `stories: [US-x, US-y]`
- **When** the agent runs `devkit spec list --where recurring=true`, `--where created_at=2026-10-13` and
  `--where stories=US-y`
- **Then** the first two list the feedback (a boolean matches `true`/`false`, a date or timestamp its ISO 8601 form)
  and the third the capability (a list matches when one element matches); a mapping or `null` matches nothing

### [AC-04] A malformed --where is an argument error
- **Given** any workspace
- **When** the agent passes `--where severity`, `--where =critical` or `--where severity=` (or `severity=,`)
- **Then** the command prints nothing on stdout, reports `ARGUMENT_INVALID` naming the malformed value, and exits `2`

### [AC-05] Feedback is ordered by severity within its kind
- **Given** open feedback FB-a (`noise`), FB-b (`critical`), FB-c (no `severity`), FB-d (`blocked`) and
  FB-e (`workaround`)
- **When** the agent runs `devkit spec list feedback`
- **Then** the order is FB-b, FB-d, FB-e, FB-a, FB-c (critical, blocked, workaround, noise, then any other
  or missing value; ties by ID, then path), and the order of the other kinds is unchanged (kind order, ID, path)

### [AC-06] Feedback lines and records carry severity, scope and target
- **Given** feedback FB-a with `severity: critical`, `scope: bundle` and `target: devkit spec list`
- **When** the agent runs `devkit spec list feedback` and `devkit spec list feedback --format json`
- **Then** the text line is
  `[DOCUMENT: FB-a kind=feedback status=open path=<path> tasks=- severity=critical scope=bundle target="devkit spec list" title=<title>]`,
  the JSON record carries `"severity": "critical"`, `"scope": "bundle"`, `"target": "devkit spec list"`, a missing
  field prints `-` (text) or `null` (JSON), and lines and records of other kinds carry none of the three fields

### [AC-07] The next-page command repeats --where
- **Given** more feedback than `--limit 1` shows
- **When** the agent runs `devkit spec list feedback --where severity=critical,blocked --limit 1`
- **Then** `[NEXT_CMD: ...]` contains `--where severity=critical,blocked` once per given `--where`, in the given
  order, with `--limit 1 --offset 1`

### [AC-08] Bundle assets select feedback through the list
- **Given** the `spec-next` skill, the `spec` skill's `references/envelope.md`, the `spec-feedback` skill's
  `references/sweep.md` and the `feedback-hygiene` playbook
- **When** they need open critical feedback, or feedback of a severity or scope
- **Then** each names `devkit spec list feedback --status open --history --where severity=critical` (or the matching
  `--where`), `--history` included because feedback recorded in a completed bundle stays open, and no longer tells the agent to open each file to read its `severity`
