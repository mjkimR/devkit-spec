---
id: TASKS-git-policy-levels
spec: SPEC-git-policy-levels
plan: PLAN-git-policy-levels
---

# Task Breakdown: `SPEC-git-policy-levels` Worktree and pull request policy levels

- [x] **Task 1**: devkit-agt lock bump and repository config at the new levels.
  - **_Boundary**: uv.lock, .devkit/config.toml
  - _Requirements: AC-02, AC-06_
- [x] **Task 2**: Worktree level parsing, template and policy output, with tests.
  - **_Boundary**: src/devkit_spec/config.py, src/devkit_spec/cli/policy.py, tests/test_cli_policy.py,
    tests/test_package.py, tests/test_config_template.py
  - _Requirements: AC-01, AC-02_
- [x] **Task 3**: Handoff branch guard and scope registration keyed on a linked worktree, with tests.
  - **_Boundary**: src/devkit_spec/proposals/handoff.py, src/devkit_spec/scope/flow.py,
    src/devkit_spec/cli/proposals.py, src/devkit_spec/errors.py,
    tests/proposals/test_proposal_handoff_worktree.py, tests/scope/test_flow.py
  - _Requirements: AC-03, AC-04_
- [x] **Task 4**: Skill, reference, workflow and playbook guidance for the levels within the byte budgets.
  - **_Boundary**: src/devkit_spec/bundle/skills/spec/, src/devkit_spec/bundle/skills/spec-integrate/SKILL.md,
    src/devkit_spec/bundle/skills/spec-next/SKILL.md, src/devkit_spec/bundle/workflows/,
    src/devkit_spec/bundle/playbooks/brownfield-adoption/SKILL.md, src/devkit_spec/bundle/AGENTS.md
  - _Requirements: AC-05, AC-06_
  - **Verification**: `rg -n "worktree=(yes|no)|pull_request=(yes|no)" src/devkit_spec/bundle` and
    `just test tests/test_bundle_budgets.py`
