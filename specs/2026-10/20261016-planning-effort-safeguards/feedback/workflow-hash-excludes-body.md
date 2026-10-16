---
id: FB-workflow-hash-excludes-body
title: It is not documented that a workflow's binding hash ignores its body
scope: upstream
kind: question
category: docs-mismatch
target: devkit workflow bind / WORKFLOW_DRIFT
skill: spec-plan
agent: claude-code
origin: agent
severity: noise
recurring: false
status: promoted
created_at: 2026-10-16
---

# [FB-workflow-hash-excludes-body] It is not documented that a workflow's binding hash ignores its body

## 1. Friction / Question (friction, question)

- **Context**: `SPEC-planning-effort-safeguards` edited the body of `sdd-proposal.md` (gate rules, spike text).
- **Expectation**: From the `spec` skill ("`devkit workflow next --unit <dir>` refuses `WORKFLOW_DRIFT` when the bound
  schema changed") and an earlier commit that updated workflow hashes in proposals, the plan assumed every bound
  proposal would need a rebind.
- **Actual**: `devkit workflow show sdd-proposal` kept the same hash after `devkit sync`; no proposal reported
  `WORKFLOW_DRIFT`. The hash covers the stage schema only.
- **Workaround (or Interpretation Chosen)**: Interpreted "schema" as the frontmatter only; dropped the rebind.
- **Suggestion**: State in the `spec` skill (and devkit's workflow docs) that body edits never drift a binding, so a
  body-only workflow change needs no rebind.

## Diagnostic Details

- **Reproduction**: Edit the body of a bundle workflow, `devkit sync`, `devkit workflow show <id>`.
- **Expected / Actual**: Expected a new hash; actual hash unchanged (`sha256:9091…`).
- **Versions**: devkit pinned by devkit-spec's `uv.lock` at `66b6f6d` (exact version unknown).
- **Conditions**: Six proposals bound to `sdd-proposal`.
- **Workarounds Attempted**: not applicable.
- **Related Assets**: `src/devkit_spec/bundle/skills/spec/SKILL.md` (Tier 1 binding sentence),
  `src/devkit_spec/bundle/workflows/sdd-proposal.md`.

## Evidence

```text
[WORKFLOW: sdd-proposal ... hash=sha256:90918c63...] before and after the body edit and devkit sync
devkit workflow next on all six PROP-* units: no WORKFLOW_DRIFT
```

- **Disposition**: `src/devkit_spec/bundle/skills/spec/SKILL.md`: `WORKFLOW_DRIFT` names the `stages` list and states that a body, title or stage-name edit needs no rebind; devkit already documents the hash inputs (`docs/workflow/definition-and-checks.md`, Schema Hash), so nothing is forwarded.
