---
id: ADR-handoff-workflow-key
title: Name the follow-up workflow of a proposal handoff_workflow
summary: A proposal names the workflow its spec follows after handoff in the handoff_workflow frontmatter key, because workflow and workflow_hash are devkit's binding of the proposal unit itself; devkit spec proposal handoff performs the cross-layout move.
status: accepted
created_at: 2026-10-13
---

# [ADR-handoff-workflow-key] Name the follow-up workflow of a proposal handoff_workflow

- **Status**: Accepted
- **Date**: 2026-10-13
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `CAP-DLV-proposal-incubation`, `CAP-DLV-delivery-workflows`

---

## 1. Context & Problem Statement

In specrig, a proposal's frontmatter `workflow` named the workflow the spec would follow after handoff (with a `WF-`
prefix). In devkit, `workflow` and `workflow_hash` in a unit's anchor file are the binding of that unit, and
`proposal.md` is the anchor of an `incubated-delivery` unit. The same key cannot hold both the proposal's own binding
and the follow-up workflow. devkit's `devkit workflow handoff` rebinds a unit in place and refuses a candidate with
another anchor (`HANDOFF_LAYOUT_MISMATCH`), so it cannot turn a proposal bundle into a spec bundle.

---

## 2. Decision Drivers

- devkit's binding keys keep devkit's meaning.
- The follow-up workflow is part of the proposal record that is reviewed and approved.
- The cross-layout move (proposal bundle to spec bundle) needs its own command.

---

## 3. Considered Options

### Option 1: A separate key `handoff_workflow` (Selected)
- **Overview**: `handoff_workflow: <id>` without prefix (`bugfix`; default `direct-delivery`), written by
  `devkit spec proposal new --handoff-workflow`; `devkit spec proposal handoff` binds `spec.md` to it.
- **Pros**: no clash with devkit's binding; the choice is visible in the proposal under review.
- **Cons**: a key name that differs from specrig.

### Option 2: Keep `workflow` for the follow-up workflow
- **Overview**: leave the proposal unbound and reuse `workflow`.
- **Pros**: specrig's key.
- **Cons**: the proposal could not be a devkit workflow unit, so `incubated-delivery` gates could not be evaluated.

### Option 3: Choose the workflow only at handoff time
- **Overview**: a handoff option and no frontmatter key.
- **Pros**: no key at all.
- **Cons**: the decision escapes the reviewed record and depends on the agent remembering it.

---

## 4. Decision Outcome

We decided to adopt **Option 1**.

**Rationale**: it keeps devkit's binding intact and records the follow-up workflow where the approval applies.

---

## 5. Consequences

- **Positive**: `incubated-delivery` ends at handoff and declares no `next` candidates; once its direction gate holds,
  `devkit spec proposal handoff <slug>` creates the spec bundle and binds `spec.md` to `handoff_workflow`, whose first
  stage is evaluated from the start.
- **Negative / Risks**: a `handoff_workflow` that does not resolve and validate refuses the handoff before anything is
  written (`SPEC_PROPOSAL_WORKFLOW_INVALID`).
- **Follow-ups**: a spec bound to `bugfix` carries `kind: bugfix` and starts with `spec.md` only
  (`ADR-bugfix-bundles-start-with-spec-only`).
