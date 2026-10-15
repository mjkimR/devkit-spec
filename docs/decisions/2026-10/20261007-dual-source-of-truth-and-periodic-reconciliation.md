---
id: ADR-dual-source-of-truth-and-periodic-reconciliation
title: Complementary code and spec ledgers with periodic human-in-the-loop drift reconciliation
summary: Code is the ledger of how the system runs and the Living Spec the ledger of intent, contracts and invariants; per-feature reconciliation syncs only the core contract delta, and accumulated drift is cleaned up periodically with the user deciding whether code or spec is wrong.
status: accepted
created_at: 2026-10-07
---

# [ADR-dual-source-of-truth-and-periodic-reconciliation] Complementary code and spec ledgers with periodic human-in-the-loop drift reconciliation

- **Status**: Accepted
- **Date**: 2026-10-07
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `CAP-DLV-delivery-workflows`, the `spec-sync` skill, `docs/capabilities/`,
  `docs/stories/`, `specs/`
- **Follow-up**: `PROP-periodic-drift-reconciliation`

---

## 1. Context & Problem Statement

Spec-driven delivery separates feature specs (`specs/`) from the Living Spec (`docs/`) and reconciles the Living Spec
when a change completes (`spec-sync`, `reconcile.md`). The decision was established early in the methodology
and carries over unchanged (`ADR-rebuild-spec-on-devkit`).

Dogfooding and larger features showed its limits:

1. **Drift is structural.** However tight the gates, many sessions and refactorings accumulate small gaps between code
   and spec.
2. **The two sit at different levels of abstraction.** Code is the runtime truth: implementation detail, language
   idioms, fine-grained error handling. The spec is the truth of intent and invariants: architectural decisions,
   functional promises, system boundaries.
3. **Either single source of truth fails at the extreme.**
   - Code as the only ledger blows up the agent's context window, and reading code alone does not reveal
     architectural intent or business invariants, which leads to regressions.
   - A spec forced into complete automatic sync makes agents copy every micro change of the code into documents,
     which bloats them and buries the design intent in noise.

The premise that one side can be the absolute single ledger, or that complete automatic sync is achievable, is not
sustainable.

---

## 2. Decision Drivers

- **Realistic governance**: accept accumulating drift as the normal state of the system instead of an unrealistic
  zero-drift ideal.
- **Session cost**: keep the documentation work at feature completion (`spec-sync`) to the core delta so delivery
  stays fast.
- **Human arbitration of intent**: when code and spec disagree, whether the code is wrong or the spec is stale is
  decided with the developer in the loop.

---

## 3. Considered Options

1. **Code as the sole truth**: minimal specs, reliance on comments and AST analysis. Rejected: it does not stop the
   agent's context from drifting over time.
2. **Spec absolutism with strict continuous sync**: lint enforces a one-to-one match of spec and code on every commit
   or pull request. Rejected: document noise explodes and agents produce mechanical, hallucinated updates.
3. **Two complementary ledgers with periodic human reconciliation (chosen)**:
   - The spec is the ledger of intent, contracts and invariants; code is the ledger of the running implementation.
   - At feature completion, only the core delta (capabilities, stories) is synced lightly (Tier 1, micro-sync).
   - Accumulated drift is reviewed and cleaned up by the user and the agent together at milestones or in periodic
     sessions (Tier 2, periodic human reconciliation).

---

## 4. Decision Outcome & Rationale

Option 3 is adopted.

- **Complementary ledgers**:
  - Code is the ledger that proves how the system behaves.
  - The spec (`docs/capabilities/`, `docs/stories/`) is the ledger of why and what the system exists for, and of the
    invariants that must not break.
- **Two-tier sync lifecycle**:
  - **Tier 1 (per-feature micro-sync)**: when a task or pull request completes, `spec-sync` reflects only the added or
    changed core contracts and does not force implementation detail to match.
  - **Tier 2 (periodic macro-reconciliation)**: periodically or at milestones, spec-code drift is reviewed and cleaned
    up under the user's explicit judgement.
- **Human involvement is required**: a gap between code and spec may be a plain bug or a missed spec update. That
  branch is not left to the agent's guess; it goes through the user's approval loop.

---

## 5. Consequences

- **Positive**:
  - Agents stop spending tokens and sessions on over-editing the spec during feature work.
  - Drift, when it occurs, is not treated as a failure of the system but as the subject of a routine sweep or hygiene
    session.
- **Follow-up**: `PROP-periodic-drift-reconciliation` explores a drift check that detects symbol and interface changes
  between code and spec, and the interactive reconciliation workflow.
