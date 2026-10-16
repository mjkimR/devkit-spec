---
id: PLAN-review-role-policy
spec: SPEC-review-role-policy
---

# Technical Plan: `SPEC-review-role-policy`

## 1. Constitution & Invariant Review
Preserve workflow structure and completion checks. Record the lasting delegation policy in a new ADR supplementing `ADR-reconcile-check-envelope`; keep the accepted ADR unchanged. Medium code review remains independent and mandatory.

## 2. Components
- Bundle role contracts, manifest, delegation payloads, effort and completion guidance, worker and workflow instructions: separate roles and align medium policy.
- Existing role-contract and workflow tests: follow renamed projections and verify unchanged stage structure.
- Living Spec: update `CAP-DLV-delivery-workflows`, `CAP-HARN-agent-guidance`, glossary and add the policy ADR.

## 3. Verification
Run just lint, just check, relevant role/workflow tests and just rules-check. Compare base workflow schemas excluding role identifiers. Obtain independent code review; self-verify fixes at medium unless uncertainty requires another call. Reconcile and independently verify this policy change because it changes the delegation contract.
