---
id: SPEC-review-role-policy
title: Separate review roles and bound medium review repetition
summary: Separates code and reconcile reviewers, preserves mandatory initial medium code review, and permits documented medium reconcile self-verification and discretionary repeat reviews.
status: planned
created: 2026-10-16
related_capabilities:
  - CAP-DLV-delivery-workflows
  - CAP-HARN-agent-guidance
related_stories: []
workflow: sdd-spec-feature
workflow_hash: sha256:200b62037a75f0224fc4deeffe8b5d6a0f6bcc5ded729a0606e1d24b4ac34d38
---

# [SPEC-review-role-policy] Separate review roles and bound medium review repetition

## 1. Problem Statement & Motivation
Code and reconcile verification need distinct read-only instructions. Mandatory repeat delegation at medium adds work without distinguishing the author's verification from a new independent review.

## 2. User Stories
- As a Developer, I want separate verification roles and bounded medium delegation so that review responsibility remains clear and fixes do not automatically start another subagent round.

## 3. Non-Goals
- Scope Excluded: changing stage IDs, order, gates, exit checks, effort selection, proposal Planning, or high-effort review obligations.
- Scope Excluded: skipping the first medium code review, introducing line-count thresholds, or delegating reconcile writing.

## 4. Acceptance Criteria
### [AC-01] Separate read-only roles
- **Given** the spec bundle is synced
- **When** review roles are projected
- **Then** code-reviewer follows spec-review and returns review/reverify, reconcile-reviewer follows spec-sync and returns reconcile-check, and neither writes files or Git state.

### [AC-02] Mandatory first medium code review
- **Given** session or Unit-path Development at medium, regardless of change size
- **When** implementation is ready for review
- **Then** one isolated code-reviewer pass is required; low retains self-review and high retains independent re-review after fixes.

### [AC-03] Conditional first medium reconcile delegation
- **Given** Unit-path Development at medium with a written reconcile result
- **When** the implementer can identify all affected contracts and documents, demonstrate agreement from the actual diff, and has no unresolved contract interpretation or cross-component impact
- **Then** the implementer may replace the first reconcile-reviewer call with a self-check, recording the omission reason and verification evidence in reconcile-check; uncertain impact requires the reviewer, and high always delegates.

### [AC-04] Medium repeat delegation is discretionary
- **Given** a completed initial review followed by fixes or further changes at medium
- **When** the implementer verifies the affected changes and resolves findings with evidence
- **Then** another subagent call is optional by the implementer's judgment; changed scope, uncertain correctness or contract interpretation are reasons to call again, and stale or failed calls do not satisfy an initial required review.

### [AC-05] Preserve workflow structure and completion evidence
- **Given** the updated workflows
- **When** comparing their definitions with the base
- **Then** stage IDs, order, entry/exit checks, gates and returns are unchanged, only reviewer role identifiers change; reconcile writing stays with the implementer and reconcile-check remains required at every effort.

## 5. Assumptions
The agreed policy is implemented at medium; high obligations and effort selection are preserved. Role identifiers change in place without compatibility aliases.
