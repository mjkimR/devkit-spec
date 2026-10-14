---
id: PLAN-subagent-procedure-in-contract
spec: SPEC-subagent-procedure-in-contract
---

# Technical Plan: `SPEC-subagent-procedure-in-contract` Subagent procedures in role contracts

## 1. Architecture Overview & Impact

- Target area: `spec` bundle content only (`src/devkit_spec/bundle/`), its tests and the Living Spec that describes it.
  No Python source and no devkit change.
- devkit renders a contract's `hosts.<host>` block into frontmatter and the whole body into the prompt; `skill` is
  optional and only adds the header line "Procedure: skill `<name>`". Dropping it from `scout` and `challenger` is
  therefore supported as is.
- No ADR: no `MUST` changes. `ADR-skills-named-spec` lists the skill names at the time of its decision and is not
  edited.
- `incubated-delivery` changes (the `spike` stage's `skills`), so units bound to it report `WORKFLOW_DRIFT` until
  rebound. This repository has none, and no external consumers exist.

## 2. Component Breakdown & Interface Contracts

**Role contracts** (`subagents/*.md`). The body is the role's prompt and only that:

- `scout`, `challenger`: drop `skill`; body = Purpose, Input (one line naming the payload fields), Procedure (the
  former skill's invariants and steps), Return, Write boundaries, On failure. Scout gets `Bash` (Claude Code) and
  `run_command` with `commandExecutionPolicy: sandbox` (Antigravity); Codex keeps `sandbox_mode: read-only`, and the
  procedure falls back to `rg` when `devkit` cannot run there. Challenger resolves IDs from `relevant_files` or by
  searching the `id:` frontmatter, since it has no shell. Both point at `.devkit/managed/spec/AGENTS.md` instead of
  `devkit get-context`.
- All four: remove `## Host projection notes` (the rationale moves to YAML comments beside the `hosts` keys) and the
  "the Developer records them with ..." sentences. The reconciler's `## Safety conditions` are already enforced by
  `spec-delegate` Steps 5 and 6; the one rule the role itself must follow (never waive a required contract mismatch)
  moves into its Write boundaries. Input sections shrink to the fields the role receives.

**`spec-delegate`**: Invariant 1 and the Inputs read the contract frontmatter only; Step 2 gains per-role payload
notes (moved from the contracts' Input sections); Step 3 passes only the payload when a projection exists and has the
main session follow the contract body only when it substitutes. Size stays within 8192 bytes.

**References**: `bundle.toml` (two assets and their preset entries), `workflows/incubated-delivery.md` (spike
`skills: [spec-delegate]`, body line), `skills/spec/SKILL.md` (routing row). The Living Spec reflection, drafted in the
`living-spec-draft` stage: `CAP-DLV-delivery-workflows` (4.3 spike paragraph, 4.6 role table and contract fields),
`CAP-HARN-agent-guidance` (skill count, 4.4 table), `ARCH-05-1-containers` (skill count).

**Skill restructuring** (`skill-authoring` playbook, Step 2.2, conditional content first): `spec-delegate` moves the
per-host invocation list into `references/hosts.md` (read when spawning a subagent) and replaces its envelope command
block with a pointer to the `spec` skill's `references/envelope.md`, which already documents the flags; its
invariants, payload table, diff comparison and fold-back rules stay. `spec` moves Tier 2 (operational playbooks) into
`references/playbooks.md`, keeping a one-line branch with the read condition; gate and approval rules stay, since
the playbook keeps safety constraints in `SKILL.md`.

**Tests**: a new `tests/test_role_contracts.py` reads the source contracts and `spec-delegate` (AC-02 to AC-06);
`tests/test_workflows.py` gains a check that no removed skill is projected after sync (AC-01).

## 3. Verification & Test Plan

- `just test tests/test_role_contracts.py tests/test_workflows.py tests/test_bundle_budgets.py` (AC-08: sizes, links)
- `uv run devkit sync` in the worktree, then `rg -n "spec-scout|spec-challenge" src README.md` returns nothing (AC-07)
- `just ci`
