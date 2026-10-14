---
id: PLAN-feedback-config
spec: SPEC-feedback-config
---

# Technical Plan: `SPEC-feedback-config` Repository-first feedback configuration

## 1. Constitution & Invariant Review

None. `CAP-DLV-project-policy` owns tool.spec validation; devkit owns stage switches and Git policy.
Feedback remains spec document capture; external transport is excluded.

## 2. Architecture Overview & Impact

- config.py: frozen FeedbackConfig, strict choices, defaults and template extension.
- cli/policy.py: effective feedback values in text and JSON.
- Feedback skill, sweep, template, router and hygiene: policy consumption and repository-first ownership.
- Project config: opt into detailed upstream coverage.
- Living Spec: reflect configuration and guidance contracts.

## 3. Verification & Test Plan

Test defaults, supported values, malformed types/values/keys, CLI output and template round trips.
Run just lint, just check, just test and just rules-check. Review guidance against all acceptance criteria.
No dependency or storage schema changes are needed.
