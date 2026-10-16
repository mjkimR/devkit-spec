---
id: TASKS-planning-feedback-capture
spec: SPEC-planning-feedback-capture
plan: PLAN-planning-feedback-capture
---

# Task Breakdown: `SPEC-planning-feedback-capture`

- [ ] **Task 1**: Validate/discover proposal feedback, with rule/autofix and lookup/namespace coverage
  - **_Boundary**: src/devkit_spec/rules/id_convention.py, src/devkit_spec/rules/spec_format.py,
    src/devkit_spec/bundle/rules/id_convention/, src/devkit_spec/bundle/rules/spec_format/,
    tests/documents/, tests/test_namespaces.py
  - _Requirements: AC-01_
- [ ] **Task 2**: Transfer open feedback transactionally with invalid-source, collision, rewrite and rollback tests
  - **_Boundary**: src/devkit_spec/proposals/handoff.py, src/devkit_spec/proposals/feedback.py,
    tests/proposals/test_proposal_feedback.py
  - _Requirements: AC-02, AC-03, AC-04_
- [ ] **Task 3**: Add Planning sweep/run-capture/cleanup contracts and verify workflow evaluation
  - **_Boundary**: src/devkit_spec/bundle/workflows/sdd-proposal.md, src/devkit_spec/bundle/skills/spec-feedback/,
    src/devkit_spec/bundle/skills/spec/, src/devkit_spec/bundle/skills/spec-next/,
    src/devkit_spec/bundle/skills/spec-delegate/, src/devkit_spec/bundle/subagents/planning-worker.md,
    src/devkit_spec/bundle/subagents/development-worker.md, src/devkit_spec/bundle/playbooks/feedback-hygiene/SKILL.md,
    tests/test_workflows.py
  - _Requirements: AC-05, AC-06, AC-07, AC-08_
