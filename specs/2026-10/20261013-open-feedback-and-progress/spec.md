---
id: SPEC-open-feedback-and-progress
title: Open feedback outside history and in-progress specs
summary: "Keeps feedback files of completed spec bundles out of the work history, so they are listed, searched and checked like current documents, and adds RULE-spec-progress, a fixable warning that moves a draft or planned spec with checked tasks to in-progress."
status: completed
created: 2026-10-13
related_capabilities:
  - CAP-DOCS-document-model
  - CAP-GOV-spec-rules
related_stories: []
workflow: direct-delivery
workflow_hash: sha256:6fe2644b9464ea860e6d6928748778b4ffd7a255e92ddea5fe10eba59138f287
---

# [SPEC-open-feedback-and-progress] Open feedback outside history and in-progress specs

## 1. Problem Statement & Motivation

The `collect-feedback` stage records feedback in a spec bundle after `living-spec-draft` has set the spec
`completed`, and `CAP-DOCS-document-model` makes every file of a completed bundle historical. Open feedback therefore
drops out of `devkit spec list feedback` and `search` unless `--history` is passed, and the rules stop checking it.
Previously, every `specs/**/feedback/*.md` was listed whatever the bundle's status; a feedback file has its own lifecycle
(`open` until a hygiene session promotes, dismisses or forwards it), so it is not work history.

A spec's `status` also stays `planned` through build, review and reconcile: nothing sets `in-progress`, although the
templates offer it. `RULE-spec-lifecycle` only reports statuses that contradict the contract (errors), and devkit
gives each rule one severity, so the progress hint is a rule of its own with severity `warning` (G2 direction).

## 2. User Stories

- **US-1**: As an agent orienting in a repository, I want open feedback of completed bundles listed without extra
  flags, so that the G3 report and `/spec-next` see feedback recorded in the current task.
- **US-2**: As a reader of `devkit spec list spec`, I want a spec under construction shown as `in-progress`, so that
  its status tells where the work is without opening `tasks.md`.

## 3. Non-Goals

1. **Scope Excluded**: other files of completed bundles stay historical (`spec.md`, `plan.md`, `tasks.md`,
   `reconcile.md`, `decisions/`, `envelopes/`).
2. **Scope Excluded**: per-violation severities in devkit; the progress check is a separate rule.
   - **When to Reconsider**: when several rules need conditions of different severity.
3. **Scope Excluded**: workflow checks or stage changes based on `in-progress`.

## 4. Acceptance Criteria & Behavioral Contracts

### [AC-01] Feedback of a completed bundle is listed without --history
- **Given** a completed spec bundle with `feedback/x.md` (`status: open`)
- **When** the agent runs `devkit spec list feedback --status open` and `devkit spec list spec`
- **Then** the first lists the feedback with `historical` `false` in JSON, and the second still hides the completed
  spec (exit `0` for both)

### [AC-02] Feedback of a completed bundle is searchable without --history
- **Given** the same bundle, the feedback's title holding a distinctive word
- **When** the agent runs `devkit spec search "<word>"`
- **Then** the feedback is a hit without `--history`

### [AC-03] Rules check feedback of completed bundles in whole-workspace runs
- **Given** a completed bundle whose `feedback/x.md` declares an ID that does not match its path, and whose `plan.md`
  has a broken reference
- **When** the agent runs `devkit rules check` without targets
- **Then** `RULE-id-convention` reports the feedback file and no rule reports `plan.md`

### [AC-04] RULE-spec-progress reports a draft or planned spec with checked tasks
- **Given** bundles whose `spec.md` is `planned` (1 of 2 tasks checked), `draft` (1 of 1 checked, no `reconcile.md`),
  `planned` (0 of 2 checked), `in-progress` (1 of 2 checked) and `planned` with every task checked and a resolved
  `reconcile.md`
- **When** the agent runs `devkit rules check`
- **Then** `RULE-spec-progress` reports exactly the first two, at line 1 of `spec.md`, with severity `warning`,
  fixable; the last is reported only by `RULE-spec-lifecycle`; the run exits `0` when no error remains

### [AC-05] The fix sets status in-progress
- **Given** the reported `planned` bundle of AC-04
- **When** the agent runs `devkit rules fix <bundle>/spec.md`
- **Then** only the frontmatter `status:` line changes, to `status: in-progress`, and a second fix changes nothing

### [AC-06] Targeting follows RULE-spec-lifecycle
- **Given** a reported bundle
- **When** a run targets only its `tasks.md`
- **Then** the violation is on `tasks.md` and is not fixable; a run targeting neither `spec.md` nor `tasks.md`
  reports nothing for the bundle

### [AC-07] Bundle assets list feedback without --history
- **Given** the `spec-next` skill, the `spec` skill's `references/envelope.md`, the `spec-feedback` skill and its
  `references/sweep.md`, and the `feedback-hygiene` playbook
- **When** they list open feedback
- **Then** none passes `--history` to `devkit spec list feedback`
