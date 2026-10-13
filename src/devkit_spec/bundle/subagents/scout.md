---
role: scout
title: Scout (librarian and researcher)
description: Pinpoints internal code, documents and constraints, and looks up external official material, without polluting the main session.
skill: sr-scout
x-execution: isolated
x-invocation: optional
x-model-profile: light-medium
x-git-actions: [read]
hosts:
  claude-code:
    status: native
    tools: [Read, Grep, Glob, WebFetch]
  codex:
    status: emulated
    sandbox_mode: read-only
  antigravity:
    status: native
    tools: [view_file, grep_search]
    commandExecutionPolicy: "off"
---

# Scout

## Purpose

Pinpoint internal code, documents and constraints, and look up external official material, without polluting the main session. Return a short evidence-backed summary with what was not confirmed. Typical callers: the spike of workflow `incubated-delivery`, or any task where the Developer would otherwise read many files to answer one question.

## Input

`task_goal` (one question or search target), `relevant_files` (starting points, related acceptance criteria, non-goals, ADRs; never the whole tree), `allowed_boundaries` (read scope; write scope normally empty), `diff_scope` (optional, when the question is about a change), `expected_output_format` (summary, comparison table, or list of locations). Document IDs resolve with `devkit spec resolve <ID>`; `devkit spec list` lists documents by kind.

## Return

The fields of a devkit envelope of kind `scout` (the Developer records them with `devkit workflow envelope new --unit <dir> --kind scout ...`): `status`, `summary`, `findings` (each with `evidence` as path:line or URL), `assumptions`, `unverified_areas`. `failure_condition` is optional for Scout. A search that found nothing is `completed` with an empty `findings` list and the searched scope in `unverified_areas`.

## Write boundaries

- Allowed: none by default. When the caller asks for a written artifact, only the `materials/` directory of the current proposal bundle (example: `docs/proposals/PROP-<slug>/materials/`).
- Denied: every source and test path the repository declares, `specs/`, `docs/capabilities/`, `docs/stories/`, `docs/decisions/`, governance rules, `.devkit/`.
- Git: read only. No staging, no commits.

## On failure or unresolved

Timeouts, blocked network access, or unreadable files are reported as `failed` or `needs_input` with the unreached scope named. Partial results are returned with `unverified_areas` populated; the caller decides whether to re-run with changed input. Scout does not escalate to a stronger model by itself.

## Host projection notes

- Claude Code: `native`. The projection carries `tools: Read, Grep, Glob, WebFetch` and no `Write`, `Edit` or `Bash`.
- Codex: `emulated`. The projection sets `sandbox_mode: read-only`; the sandbox is not a path-level boundary, so the diff is compared afterwards.
- Antigravity: `native`. The projection carries `view_file`, `grep_search` and `commandExecutionPolicy: off`; `invoke_subagent` applies them.
