---
id: SPEC-subagent-procedure-in-contract
title: Subagent procedures in role contracts
summary: Fold the subagent-only Scout and Challenger procedures into their role contracts, keep caller-facing guidance in spec-delegate, and pass only the per-call payload when a projection exists.
status: completed
created: 2026-10-14
related_capabilities:
  - CAP-DLV-delivery-workflows
  - CAP-HARN-agent-guidance
related_stories: []
workflow: direct-delivery
workflow_hash: sha256:6fe2644b9464ea860e6d6928748778b4ffd7a255e92ddea5fe10eba59138f287
---

# [SPEC-subagent-procedure-in-contract] Subagent procedures in role contracts

## 1. Problem Statement & Motivation

`devkit sync` renders each role contract body into the host's native agent file, and the host program loads that file
as the subagent's system prompt at spawn. Three things around it waste tokens or do not work:

- The `scout` and `challenger` procedures live in the skills `spec-scout` and `spec-challenge`. The projection carries
  only the line "Procedure: skill `spec-scout`"; the subagent has no Skill tool and no preloaded skill, so it must
  find and read the file itself. Both skills serve only these roles, yet they sit in the main session's skill
  catalog, where the main session may run them itself and lose the isolation.
- `spec-delegate` tells the main session to read the whole contract and paste its body into the subagent prompt.
  The projection already carries the body, so the main session pays output tokens for a copy the subagent then reads
  twice.
- Contract bodies mix the subagent's prompt with caller-only material (`Host projection notes`, the reconciler's
  `Safety conditions`, how the Developer records the envelope), which every subagent reads for nothing.

The Scout procedure also names `devkit spec search`, `list`, `resolve` and `refs`, but the role has no shell.

Moving the caller guidance into `spec-delegate` leaves it 16 bytes under the 8192-byte skill budget, and the `spec`
router is 48 bytes under it, so the next edit to either fails `tests/test_bundle_budgets.py`. devkit's
`skill-authoring` playbook (`authoring` bundle) restructures such a skill by moving conditional content into
references with a stated read condition.

## 2. User Stories

- **US-1**: As the Developer delegating to a support role, I want to send only the per-call payload, so that a
  delegation costs main-session tokens only for what changes between calls.
- **US-2**: As a support role subagent, I want my whole procedure in my system prompt, so that I start working
  without searching for a skill file or running a command I cannot run.

## 3. Non-Goals

1. **Scope Excluded**: removing or inlining `spec-review` and `spec-sync`. The main session runs them by default and
   the workflows' stage `skills:` lists and `[NEXT_SKILL]` name them, so `reviewer` and `reconciler` keep their
   `skill` field.
2. **Scope Excluded**: shell access for `challenger` and `reconciler`. Their tools stay as they are.
   - **When to Reconsider**: a reconciler draft repeatedly misses documents that `devkit spec refs` would have found.
3. **Scope Excluded**: a devkit change (a CLI that serves stage guidance, or a projection that drops body sections).
   Everything here is bundle content.
4. **Scope Excluded**: preloading skills through the Claude Code `skills:` host key.

## 4. Acceptance Criteria & Behavioral Contracts

### [AC-01] The subagent-only skills are gone
- **Given** the `spec` bundle after this change
- **When** `bundle.toml` is read and `devkit sync` runs into an empty workspace
- **Then** no asset `spec-scout` or `spec-challenge` exists, no `spec-scout` or `spec-challenge` skill directory is
  projected, and `devkit workflow validate` exits 0 with no errors

### [AC-02] Scout and Challenger carry their procedure
- **Given** the `scout` and `challenger` contracts
- **When** their frontmatter and body are read
- **Then** neither has a `skill` field, and each body has a `## Procedure` and a `## Return` section, so the
  projected agent file holds the whole procedure

### [AC-03] Contract bodies hold only the role's prompt
- **Given** the four role contracts
- **When** their bodies are searched
- **Then** none contains a `## Host projection notes` or `## Safety conditions` heading or the phrase
  `the Developer records them`

### [AC-04] spec-delegate passes the payload only
- **Given** `spec-delegate`
- **When** it is read
- **Then** it tells the caller to read the contract frontmatter, to pass only the payload when the role has a
  projected file, and to follow the contract body itself only when the main session substitutes; it carries each
  role's payload notes; and it stays within the 8192-byte skill budget

### [AC-05] Scout can run devkit spec queries
- **Given** the `scout` contract
- **When** its `hosts` block is read
- **Then** `claude-code.tools` includes `Bash`, `antigravity.tools` includes `run_command` with
  `commandExecutionPolicy: sandbox`, and the `challenger` contract has neither `Bash` nor `run_command`

### [AC-06] Reviewer and Reconciler keep their shared skills
- **Given** the `reviewer` and `reconciler` contracts
- **When** their frontmatter is read
- **Then** `reviewer.skill` is `spec-review` and `reconciler.skill` is `spec-sync`

### [AC-07] No live reference to the removed skills
- **Given** the repository after this change
- **When** `spec-scout` and `spec-challenge` are searched in `src/` and `README.md`
- **Then** there is no match, and `devkit rules check` reports no violation

### [AC-08] The two crowded skills regain headroom by condition, not by deletion
- **Given** `spec-delegate` and `spec` after this change
- **When** their `SKILL.md` sizes and links are checked
- **Then** each `SKILL.md` is at most 7680 bytes; the per-host invocation steps live in
  `spec-delegate/references/hosts.md` and the operational playbook branch in `spec/references/playbooks.md`, each
  linked from its `SKILL.md` with a read condition; every relative link in a skill document resolves, and every file
  under a skill's `references/` is linked from that skill
