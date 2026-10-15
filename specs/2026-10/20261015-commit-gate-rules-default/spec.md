---
id: SPEC-commit-gate-rules-default
title: Commit gate runs the spec rules by default
summary: 'Adopts devkit''s built-in rules-check commit gate: bumps devkit, and rewrites the constitution, architecture, development docs, seed and brownfield playbook that told projects to list the rules check in verify-commands.'
status: in-progress
created: 2026-10-15
related_capabilities:
  - CAP-GOV-spec-rules
related_stories:
  - US-keep-the-living-spec-consistent
workflow: direct-delivery
workflow_hash: sha256:6fe2644b9464ea860e6d6928748778b4ffd7a255e92ddea5fe10eba59138f287
---

# [SPEC-commit-gate-rules-default] Commit gate runs the spec rules by default

## 1. Problem Statement & Motivation

The spec constitution says commits run the spec rules through the commit gate, but devkit's commit gate ran rules
only when a project listed `devkit rules check --staged` in `[gates.settings.verify-commands]`, whose default is
empty. This repository configures no such command, so a staged `RULE-document-summary` error was committed unchecked
(`FB-commit-gate-runs-no-rules-check`). devkit now ships a built-in `rules-check` pre-commit gate, on by default, that
evaluates the staged tree (in place when the working tree holds exactly the staged content). devkit-spec must pin that
devkit and stop telling projects to configure the rules check themselves.

## 2. User Stories

- **US-1**: As an agent committing in a devkit-spec project, I want the spec rules to run at every commit without
  configuration, so that a commit cannot carry a rule error the documents promise the gate would catch.

## 3. Non-Goals

1. **Scope Excluded**: configuring `verify-commands` for this repository (lint, type check, tests stay in `just ci`).
2. **Scope Excluded**: changing devkit's gate or snapshot behavior; that work is done in devkit.
3. **Scope Excluded**: rewording documents that only say "the commit gate runs the staged checks"; they are correct
   once the gate runs the rules by default.

## 4. Acceptance Criteria & Behavioral Contracts

### [AC-01] devkit is pinned at the commit with the rules-check gate
- **Given** the repository's `uv.lock`
- **When** the environment is synced and `uv run devkit gate status` runs
- **Then** both `devkit-agt` and `devkit-advisory` are pinned at the same devkit commit that contains the gate, and
  the output lists `[GATE: rules-check stage=pre-commit order=100 enabled=true source=builtin]`

### [AC-02] A commit with a staged spec-rule error is refused
- **Given** this repository with its hooks installed and a staged document whose `summary` exceeds 300 characters
- **When** `git commit` runs
- **Then** the commit is refused with `GATE_RULES_FAILED` naming `RULE-document-summary`, and exits non-zero

### [AC-03] No guidance tells projects to list the rules check in verify-commands
- **Given** the constitution, the bundle's playbooks and seed, and this repository's `docs/`
- **When** they are searched for `verify-commands`
- **Then** no passage says the rules run through `verify-commands` or must be configured there; the commit gate is
  described as devkit's `rules-check` gate, on by default, turned off with `[gates.settings.rules-check]` `enabled = false`

### [AC-04] Brownfield adoption explains the default gate
- **Given** the `brownfield-adoption` playbook's commit gate step
- **When** an agent follows it in a repository with existing rule findings
- **Then** the step states that the hooks run `rules-check` by default on the files each commit changes, and offers
  fixing the findings, parking or lowering a rule in `[rules]`, or disabling the gate until they are resolved
