---
id: ADR-medium-review-delegation
title: Separate review roles and bound medium delegation
summary: "Medium requires initial code review regardless of size, permits evidence-backed initial reconcile self-verification, and leaves repeat code and reconcile calls to the implementer while retaining all workflow checks."
status: accepted
created_at: 2026-10-16
---

# [ADR-medium-review-delegation] Separate review roles and bound medium delegation

## Context

Code review and reconcile verification compare different artifacts and require different instructions. Requiring a
subagent after every fix repeats independent review even when the implementer can verify the correction directly.
`ADR-reconcile-check-envelope` establishes separate reconcile evidence and its stage exit; those remain required.

## Decision

- Use distinct read-only `code-reviewer` and `reconcile-reviewer` contracts. The implementer writes, fixes and
  resolves Living Spec reflection and `reconcile.md` at every effort. Reviewers only return verification results.
- At medium, initial code review is mandatory for session and Unit paths regardless of change size.
- Only medium Unit-path reconcile verification may omit its initial subagent call when all affected contracts and
  documents can be identified, agreement with the actual diff can be directly demonstrated, and no unresolved
  contract interpretation or cross-component impact remains. A confirmed no-impact or wording-only reflection may
  qualify; small size alone does not. Uncertainty requires the reconcile reviewer. Record the omission reason and
  self-verification evidence in the existing `reconcile-check` envelope.
- After the initial medium review, the implementer verifies fixes and subsequent changes and decides whether to
  invoke either reviewer again. Expanded scope, uncertain correctness or contract interpretation are reasons for
  another call. Findings still need evidence of resolution. Attribute later verification to its actual executor;
  a failed or stale initial call never fulfills the required first review.
- Low retains self-review and self-checked reconcile. High retains code re-review after fixes and independent
  reconcile verification. Stage IDs, order, entry/exit checks, gates, returns and effort selection are unchanged;
  only stage role identifiers are renamed. Required repository policies remain binding.

## Consequences

The initial medium reconcile check can be self-verification, while its evidence and completion check remain
mandatory. This supplements the verifier assignment in `ADR-reconcile-check-envelope`; its envelope separation and
stage check remain intact. Role names change in place, without aliases. Active units bound to renamed stage roles
must rebind after inspecting workflow drift. Completed units remain history.
