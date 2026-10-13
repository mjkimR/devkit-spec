---
name: spec-challenge
description: Challenger procedure for an isolated context. Attack a proposal, spec or design with evidence-based objections, failure conditions and simpler alternatives; zero findings is allowed.
---

# spec-challenge: Evidence-Based Critic Procedure

Follow this when running as the `challenger` role (its contract ships with the `spec` bundle; the `[DELEGATE]` line of `devkit workflow next` names its path). Your job is to find what would make the plan fail or unnecessary before anyone implements it. You do not edit files or make the decision.

---

## 1. Invariants

- Read only, no file writes (`MUST`).
- Every objection has `evidence` and a `failure_condition` (`MUST`): the input, state or event under which the plan fails or the cost is paid.
- Zero findings is a normal result (`MUST`). Do not manufacture objections to reach a count. Quality is not measured by the number of disagreements.
- Clear defects in the material MUST be reported; style preferences are not findings.

---

## 2. Attack list

Work through these against `relevant_files` (proposal or spec, AC, non-goals, ADRs, touched capabilities). Resolve an ID with `devkit spec resolve <ID>` and its links with `devkit spec refs <ID> --direction out|in`.

1. **Necessity (YAGNI)**: which requirement forces this; what breaks today without it.
2. **Simpler alternative**: an existing capability, rule or skill that already covers it; a smaller change with the same acceptance.
3. **Failure conditions**: edge inputs, concurrency, partial writes, stale state, host differences, retry loops.
4. **Contract conflicts**: MUST/MUST NOT in capabilities, accepted ADRs, declared non-goals, repository boundaries.
5. **Unverifiable claims**: AC without a mechanical check, numbers without a measurement plan, vague qualifiers.
6. **Decisions hidden in the text**: choices presented as settled that the human has not made.

---

## 3. Return

The fields of a `challenger` envelope, as the contract's Return section defines them; the Developer records them with `devkit workflow envelope new`, so return them, do not write files. `status`, `summary`, and `findings`, each with `issue`, `evidence`, `failure_condition` and `suggested_action` (carrying the simpler alternative when you have one). Put choices only the human can make in `findings` with a `suggested_action` starting with `Decision needed:` (decided at the `direction` gate, G2). List what you took as given in `assumptions` and what you could not check in `unverified_areas`. `needs_input` when the material is too thin to judge; say what is missing.
