---
id: FB-authoring-preset-not-selected
title: The skill-authoring playbook and size rule are not selected in a repository that authors skills
scope: repo
kind: suggestion
category: missing-capability
target: .devkit/config.toml
skill: none
agent: claude-code
origin: user
severity: workaround
recurring: false
status: open
created_at: 2026-10-14
---

# [FB-authoring-preset-not-selected] The skill-authoring playbook and size rule are not selected in a repository that authors skills

## 2. Suggestion / Change Request (suggestion, change-request)

- **Current Procedure**: `[presets]` selects only `spec`, so `devkit playbook search` finds no `skill-authoring` playbook and `RULE-skill-document-size` never runs; `tests/test_bundle_budgets.py` re-implements the 8192-byte check.
- **Proposed Procedure**: Select `authoring:skill-authoring` (`devkit add authoring:skill-authoring`) so the playbook is discoverable when a bundle skill is restructured and `devkit rules check --phase hygiene` reports oversized skills.
- **Expected Benefit**: The restructuring procedure is found by search instead of by reading devkit's installed package; the size signal comes from the shipped rule.
- **Cost & Risk**: The rule checks projected skill paths, which carry devkit's injected context block and so run about 700 bytes larger than the sources the test measures; a few skills may need an override or a split.
- **Attempted**: Hypothesis; the playbook was read from the installed devkit package for `SPEC-subagent-procedure-in-contract`.

## Evidence

```text
uv run devkit playbook search "skill authoring" -> "results": []
.devkit/config.toml [presets]: spec = ["core", "docs-skeleton"]
devkit/authoring_guide/bundle/bundle.toml: [presets.skill-authoring] assets = ["skill-authoring", "skill-document-size"]
```
