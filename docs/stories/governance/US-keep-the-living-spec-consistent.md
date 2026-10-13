---
id: US-keep-the-living-spec-consistent
title: Keep the Living Spec Consistent
summary: A developer or AI coding agent relies on deterministic spec rules, run locally, at the commit gate and in CI, to keep document IDs, references, links, summaries, task coverage, spec lifecycle and code entrypoints consistent as documents and code change.
area: governance
actor: AI coding agent, developer
status: active
capabilities:
  - CAP-DOCS-document-model
  - CAP-GOV-spec-rules
  - CAP-TRACE-code-entrypoints
created_at: 2026-10-13
---

# [US-keep-the-living-spec-consistent] Keep the Living Spec Consistent

## 1. User Story Narrative

- **As a**: AI coding agent or developer changing documents and code in a project that uses the `spec` bundle
- **I want to**: have every structural inconsistency I introduce (a broken reference, a one-sided link, a misplaced
  file, a stale spec status, an unreconciled change, a dead code entrypoint) reported with a stable rule ID and a
  deterministic remediation, and repaired automatically where the repair is unambiguous
- **So that**: the Living Spec stays a trustworthy current-state contract that later agents can navigate by ID
  without re-validating it

---

## 2. Background & Context

Agents work in good faith but lose context, work on parallel branches and delete or move code. The spec rules run in
devkit's rule engine: `devkit rules check` for the whole workspace, `check --staged` as the commit gate on the exact
staged tree, and `check --ci --base <ref>` on a pull request. Each rule reads the same document index, reports only in
the files the run targets, and leaves completed spec bundles alone as work history unless they are named.

---

## 3. Acceptance Criteria (Given / When / Then)

### Scenario 1: A one-sided link is fixed deterministically

- **Given**: a story lists a capability in `capabilities`, and the capability does not list the story
- **When**: the agent runs `devkit rules check` and then `devkit rules fix`
- **Then**: the check reports `RULE-traceability-link` on the capability with `status=fixable`, the fix appends the
  story ID to the capability's `stories` in the list's existing style, and a recheck reports no violation

### Scenario 2: Deleting code without updating its document fails the commit gate

- **Given**: a capability declares `src/<package>/engine.py` in `entrypoints`
- **When**: a commit stages only the deletion of that file and the commit gate runs `devkit rules check --staged`
- **Then**: `RULE-code-entrypoints` reports the capability, although the commit does not touch it, and the commit is
  blocked until the declaration is updated or removed

### Scenario 3: A reference to a missing document is reported, never guessed

- **Given**: a decision cites a capability ID that no document declares
- **When**: the agent runs `devkit rules check`
- **Then**: `RULE-document-reference` reports the unresolved ID with `status=open`, and `devkit rules fix` leaves the
  reference unchanged

### Scenario 4: A resolved reconcile record needs its evidence

- **Given**: a commit marks a spec's `reconcile.md` `resolved` with a `modified` target that the commit does not change
- **When**: the commit gate runs `devkit rules check --staged`
- **Then**: `RULE-reconcile-contract` reports the target, and committing the Living Spec edit with the record clears it
