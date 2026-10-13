---
id: PLAN-open-feedback-and-progress
spec: SPEC-open-feedback-and-progress
---

# Technical Plan: `SPEC-open-feedback-and-progress` Open feedback outside history and in-progress specs

## 1. Constitution & Invariant Review

`CAP-DOCS-document-model` (historical documents) and `CAP-GOV-spec-rules` (rule catalog, history behavior) change
with this spec; no ADR is needed: the history rule is narrowed for one kind, and a new rule follows the existing rule
layout (`ADR-rules-implemented-in-the-package`).

## 2. Architecture Overview & Impact

- **Impacted Components**:
  - `src/devkit_spec/documents/index.py`: `DocumentIndex.load` leaves feedback documents out of `historical`; `list`,
    `search` and every rule (`rules.reportable`) follow from it.
  - `src/devkit_spec/rules/spec_lifecycle.py`: the bundle reading (`bundles`) and the status-line rewrite
    (`with_status`) become shared helpers.
  - `src/devkit_spec/rules/spec_progress.py` (new): `SpecProgressRule`, phase `linter`, severity `warning`.
  - `src/devkit_spec/bundle/rules/spec_progress/` (new): `rule.py` wrapper, `guide.md`, `tests/test_rule.py`;
    `bundle.toml` declares the asset and adds it to preset `core`.
  - Assets listing feedback: `spec-next`, `spec/references/envelope.md`, `spec-feedback/references/sweep.md`,
    `feedback-hygiene`.
- **New Dependencies**: None.

## 3. Component & Interface Design

- `SpecProgressRule.check`: for each bundle (as `RULE-spec-lifecycle` reads them) whose `spec.md` status is `draft`
  or `planned`, with at least one checked task, and not in the lifecycle's stale state (every task checked and
  `reconcile.md` resolved), one violation on the targeted file (`spec.md`, else an explicitly targeted `tasks.md`),
  fixable when `spec.md` is targeted and has a `status:` line.
- `SpecProgressRule.fix`: rewrites that line to `status: in-progress`.

## 5. Error Handling & Edge Cases

- A bundle in the lifecycle's stale state is left to `RULE-spec-lifecycle`, so the two fixes never disagree.
- Statuses compare trimmed and lower-cased; other statuses (`in-progress`, `completed`, unknown) are not reported.

## 6. Verification & Test Plan

- Rule tests in `src/devkit_spec/bundle/rules/spec_progress/tests/test_rule.py` (AC-04..AC-06).
- `tests/test_cli_documents.py` and `tests/test_search.py` (AC-01, AC-02); a rule-run test for AC-03.
- `rg` over the four assets for `--history` on `list feedback` (AC-07).
- `just ci`; `devkit sync` then `devkit rules test`.
