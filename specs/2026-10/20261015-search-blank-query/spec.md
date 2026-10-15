---
id: SPEC-search-blank-query
title: Reject a blank search query
summary: "devkit spec search rejects a query that is empty or only whitespace with ARGUMENT_INVALID (exit 2) instead of silently returning no hits."
status: planned
created: 2026-10-15
related_capabilities:
  - CAP-DOCS-document-search
related_stories:
  - US-find-the-right-documents
workflow: direct-delivery
workflow_hash: sha256:6fe2644b9464ea860e6d6928748778b4ffd7a255e92ddea5fe10eba59138f287
---

# [SPEC-search-blank-query] Reject a blank search query

## 1. Problem Statement & Motivation

`devkit spec search ''` (or a query of only spaces) prints `[SEARCH: query=- mode=lexical count=0]` and exits `0`. An
agent that built the query from an empty variable cannot tell this apart from a real search with no hit, and moves
on believing nothing matches. The command already rejects a negative `--limit` with `ARGUMENT_INVALID`; a blank
query is the same kind of malformed input.

## 2. User Stories

- **US-1**: As an agent searching the Living Spec, I want a blank query refused with a directive, so that I fix my
  input instead of reading "no hit" as an answer.

## 3. Non-Goals

1. **Scope Excluded**: normalizing whitespace inside a non-blank query (blank words among non-blank ones keep today's
   joining).
2. **Scope Excluded**: a new `SPEC_` code; the existing `ARGUMENT_INVALID` covers malformed arguments.
3. **Scope Excluded**: changing `devkit_spec.search.search_documents`; the check lives at the command line.

## 4. Acceptance Criteria & Behavioral Contracts

### [AC-01] An empty or whitespace-only query is refused
- **Given** a workspace with spec documents
- **When** `devkit spec search ''`, `devkit spec search '   '` or `devkit spec search '' ' '` runs
- **Then** the command exits `2` with an `ARGUMENT_INVALID` error whose `[TARGET]` is `QUERY`, carries a `[FIX]`
  line, and prints no `[SEARCH:` line

### [AC-02] The JSON format reports the same error
- **Given** a workspace with spec documents
- **When** `devkit spec search '  ' --format json` runs
- **Then** the command exits `2` and stdout is one JSON object whose `error.code` is `ARGUMENT_INVALID`

### [AC-03] A non-blank query is unchanged
- **Given** a workspace with spec documents
- **When** `devkit spec search cache policy` runs
- **Then** the command exits `0` and prints `[SEARCH: query="cache policy" ...]` as before
