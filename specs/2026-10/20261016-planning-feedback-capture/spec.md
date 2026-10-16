---
id: SPEC-planning-feedback-capture
title: Feedback capture in Planning
summary: Keeps Planning feedback in its proposal bundle, carries open observations into the spec at handoff, and preserves them before proposal cleanup. Adds run-level capture and a Planning feedback sweep using the existing policy.
status: completed
created: 2026-10-16
related_capabilities: []
related_stories: []
workflow: sdd-spec-feature
workflow_hash: sha256:20b913108a194572244fd42f0587ce3fe7fecfb7610c8afb52fa6b35e79fb0e0
---

# [SPEC-planning-feedback-capture] Feedback capture in Planning

## Intent

Planning observations belong inside the worker boundary and must survive handoff and proposal deletion. As a Planning
executor, I want to keep feedback with the proposal and carry open work forward without changing its status.
`ADR-planning-feedback-in-proposal` authorizes storage/retirement. Strategy 01 §6.2 was updated in workbench 72dd79d
before handoff. Affected contracts: `CAP-HARN-agent-guidance`, `CAP-DLV-delivery-workflows`,
`CAP-DLV-proposal-incubation`, `CAP-DOCS-document-model` and `CAP-GOV-spec-rules`.

## Non-goals

- **Scope Excluded**: new feedback statuses, template changes, hygiene disposition decisions.
- **Scope Excluded**: Backlog/inline Planning stages, autohub UI/rejection orchestration changes, devkit APIs.
- **Scope Excluded**: implementing the pilot's conversation-answer API and missing plan-intent commit-instruction fixes;
  retain those observations as feedback before completion.

## Acceptance Criteria

### [AC-01] Valid and discoverable proposal feedback

- **Given** direct Markdown feedback at `docs/proposals/PROP-<slug>/feedback/<name>.md` with undated kebab-case name.
- **When** rules, lookup, resolution, references and namespace filtering run.
- **Then** expected identity is `FB-<name>`, path/ID/H1 checks match spec-local feedback, missing-ID autofix derives
  the feedback ID, and feedback remains current in rejected proposals awaiting cleanup.

### [AC-02] Open feedback follows handoff

- **Given** accepted proposal feedback with open, promoted, dismissed and forwarded statuses.
- **When** handoff succeeds.
- **Then** only open files enter the new spec's feedback directory, settled files go to preserved materials/feedback,
  IDs/statuses/created_at remain unchanged, links and proposal/PADR references follow existing relocation semantics,
  and no source is carried twice. Empty/absent feedback preserves existing behavior; Planning envelopes are dropped.

### [AC-03] Invalid and unsafe sources cannot be retired

- **Given** unreadable/malformed feedback, missing/unknown status, ID/name mismatch, nested feedback paths,
  symlink feedback sources or unsafe/conflicting destinations.
- **When** handoff preflight runs.
- **Then** it fails before writing with existing SPEC_PROPOSAL_INVALID or SPEC_PROPOSAL_TARGET_EXISTS errors and
  never overwrites. Non-feedback sidecars keep generic preservation behavior.

### [AC-04] Feedback participates in rollback

- **Given** valid feedback and an injected write/move failure, including cross-filesystem copying.
- **When** handoff cannot finish its writes.
- **Then** sources remain/restored and no partial spec/ADR/material targets remain under the existing rollback
  contract. Successful moves rewrite relative links using each file's original location.

### [AC-05] Deletion without handoff preserves observations

- **Given** rejected, decomposed or abandoned proposal feedback.
- **When** the Host follows cleanup/decomposition instructions.
- **Then** feedback stays in the proposal until deletion; open files move once to the current month-level backlog
  in the deletion commit, preserving IDs/statuses/observation dates. Settled records stay in Git. Check collisions
  and invalid files, update relative links, preserve historical context with Git revision/path and strikethrough
  references, validate current references, and refuse deletion on unresolved live dependencies. Rejection starts
  no worker and never changes feedback statuses.

### [AC-06] Run capture and sweep

- **Given** direct Planning or a Planning/Development worker ending complete, with questions or with a problem.
- **When** capture=observed applies.
- **Then** concrete observations are recorded before the last work commit, inside the proposal/spec respectively.
  Before every Planning return, an enabled sweep covers that run plus committed accumulated records, deduplicates
  the full open backlog, writes fresh feedback evidence then one worker record. Older PASS is not later-run coverage.
  Incomplete coverage records FAIL with its gap; no freshness engine is added.

### [AC-07] Shared stage, policy and person gate

- **Given** sdd-proposal with plan-intent accepted.
- **When** next evaluates missing, failed, zero-observation, requested-only or stage-off sweep evidence.
- **Then** collect-feedback precedes plan-accept; missing/failed evidence holds it, zero/policy-skip PASS opens the
  person gate only for reviewing/accepted proposals, stage-off skips without an envelope. Observed capture still
  applies with stage-off; explicit user sweeps keep their no-envelope override. Shared exit/gate/role/isolation/
  skills/artifacts match Development; entry uses anchor-exists.

### [AC-08] Rejection uses recorded coverage

- **Given** a Planning run returned with sweep/worker records or an explicit policy skip/coverage gap.
- **When** the proposal is rejected, including during questions.
- **Then** rejection uses recorded coverage, starts no worker/Cloud Agent, claims no fresh later-conversation sweep,
  and preserves existing open-question/rejection handling. Rejection before any run has no run observations.

## Assumptions and verification

Direct execution at medium effort. Cleanup is an instructed Host operation, not a new CLI. Run freshness is an
executor procedure reviewed against records. Use handoff failure injection, rule/autofix, lookup/namespace and real
workflow evaluation tests; required lint/type/full-test/governance checks and independent code/reconcile reviews.
The new ADR is a handoff output; no existing accepted ADR is edited.
