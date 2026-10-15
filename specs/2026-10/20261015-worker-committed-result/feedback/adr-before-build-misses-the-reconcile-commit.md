---
id: FB-adr-before-build-misses-the-reconcile-commit
title: An ADR written before the build cannot be a reconcile target once the commit gate checks each commit
scope: repo
kind: friction
category: instruction-conflict
target: src/devkit_spec/bundle/rules/reconcile_contract/guide.md
skill: spec-sync
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: open
created_at: 2026-10-15
---

# [FB-adr-before-build-misses-the-reconcile-commit] An ADR written before the build cannot be a reconcile target once the commit gate checks each commit

## 1. Friction / Question (friction, question)

- **Context**: `SPEC-worker-committed-result` changes a MUST, so its ADR was written and committed as build Task 1,
  before implementation, as the constitution and `spec-specify` require. At `living-spec-draft` the resolved
  `reconcile.md` listed that ADR as a `modified` target.
- **Expectation**: `spec` skill `references/completion.md`: "a target already committed earlier in a feature is
  verified in the cumulative branch diff".
- **Actual**: with devkit's `rules-check` commit gate on by default, `RULE-reconcile-contract` refused the commit: the
  ADR is absent from the staged diff. The rule's guide says the staged check needs every `modified` target in the
  same diff; only `--ci` accepts an earlier commit. Before the gate ran rules, the conflict never surfaced.
- **Workaround (or Interpretation Chosen)**: dropped the ADR from `targets` and explained in the record's body that it
  was committed with Task 1 and is covered by the cumulative `--ci` check.
- **Suggestion**: either let the staged check accept a `modified` target that the branch already changed since its
  merge base (as `--ci` does), or state in `spec-sync` and `completion.md` that a document committed before the
  reconcile commit is not listed as a target, and how the ADR of a changed MUST is recorded.

## Diagnostic Details

- **Reproduction**: commit an ADR in an early task commit; later stage a `resolved` `reconcile.md` listing it as
  `modified`; `git commit`.
- **Expected / Actual**: expected the commit to pass (target changed earlier on the branch); actual `GATE_RULES_FAILED`
  equivalent from `devkit rules check --staged`: `target ... is resolved as modified but absent from the staged diff`.
- **Versions**: devkit `bc14046`; devkit-spec `b249e3b` plus this branch.
- **Conditions**: `rules-check` gate enabled by default.
- **Workarounds Attempted**: target removed with an explanation; commit passed.
- **Related Assets**: `RULE-reconcile-contract`, `spec-sync` Step 2 and 4, `spec/references/completion.md`.

## Evidence

```text
[VIOLATION: RULE-reconcile-contract severity=error file=specs/2026-10/20261015-worker-committed-result/reconcile.md line=1 message="target docs/decisions/2026-10/20261015-worker-delivers-committed-result.md is resolved as modified but absent from the staged diff"]
completion.md: a target already committed earlier in a feature is verified in the cumulative branch diff.
guide.md: --ci judges the whole branch against its merge base, so a target changed in an earlier commit of the branch counts there.
```
