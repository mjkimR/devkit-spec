---
id: TASKS-feedback-config
spec: SPEC-feedback-config
plan: PLAN-feedback-config
---

# Task Breakdown: `SPEC-feedback-config` Repository-first feedback configuration

- [x] **Task 1**: Feedback config, template and policy output with regression tests.
  - **_Boundary**: src/devkit_spec/config.py, src/devkit_spec/cli/policy.py, tests/test_cli_policy.py, tests/test_config_template.py, tests/test_feedback_config.py, tests/test_cli_documents.py
  - _Requirements: AC-01, AC-02_
- [x] **Task 2**: Repository-first capture, sweep, detail, hygiene and project settings.
  - **_Boundary**: src/devkit_spec/bundle/skills/spec-feedback/, src/devkit_spec/bundle/skills/spec/SKILL.md, src/devkit_spec/bundle/playbooks/feedback-hygiene/SKILL.md, .devkit/config.toml
  - _Requirements: AC-03, AC-04_
