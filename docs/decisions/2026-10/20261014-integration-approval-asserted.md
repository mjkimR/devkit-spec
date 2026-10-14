---
id: ADR-integration-approval-asserted
title: Record the intent and direction gates, assert the integration gate
summary: "G1, G2 and G3 stay devkit's intent, direction and integration gates with the default ask; intent and direction answers are recorded, while the G3 OK is asserted with --given integration (or answered by the PR ready state), so approving integration needs no extra commit."
status: accepted
created_at: 2026-10-14
supersedes: ADR-approval-gates-intent-direction-integration
---

# [ADR-integration-approval-asserted] Record the intent and direction gates, assert the integration gate

- **Status**: Accepted
- **Date**: 2026-10-14
- **Deciders**: @mjkimR
- **Involved Components/Capabilities**: `CAP-DLV-delivery-workflows`, `CAP-DLV-project-policy`, `ARCH-06-runtime-view`
- **Supersedes**: `ADR-approval-gates-intent-direction-integration`

---

## 1. Context & Problem Statement

`ADR-approval-gates-intent-direction-integration` mapped specrig's human gates G1, G2 and G3 to devkit's approval
gates `intent`, `direction` and `integration` and recorded every answer with `devkit workflow answer`, a decision
record under the unit's `decisions/`. It rejected specrig's declared human checks partly because `--given` would
assert approvals.

specrig had already removed its G3 file for a reason that ADR did not weigh: G3 is asked after the final change
report, so its record is written after the change is committed. In a session it costs one more file and one more
commit after the user's OK; on a PR it records the PR ready state a second time. G1 and G2 have neither cost: their
records are written while the bundle is being drafted and are committed with it. In use the cost returned: the
integration record of `SPEC-subagent-procedure-in-contract` left the worktree dirty, so `devkit worktree finish`
could not run until a commit holding only that file was made and pushed.

devkit supports both forms: a gate is satisfied by an accepted decision record of the current segment, by
`--given <gate>` for one invocation, or by the `auto` policy.

---

## 2. Decision Drivers

- Gate decisions are never inferred, and a policy can delegate them explicitly.
- Approving integration must not create work that needs another commit after the change is final.
- One fact, one record: a PR's ready state and the session's explicit OK already carry the G3 decision.
- devkit stays SDD-agnostic: its defaults are not tuned for one methodology.

---

## 3. Considered Options

### Option 1: Record G1 and G2, assert G3 (Selected)
- **Overview**: the stages whose `human_gate` is `intent`, `direction` and `integration` carry G1, G2 and G3 with
  devkit's default `ask`. Under `ask`, G1 and G2 answers are recorded with `devkit workflow answer`. The user's G3 OK
  is not recorded: the executor passes `--given integration` to each `devkit workflow next` after it, and a runner
  binds the gate to the PR ready state.
- **Pros**: no file and no commit after the final change; G1 and G2 keep a durable record at no extra cost; the
  authority for G3 stays visible in the integration report and the merge.
- **Cons**: the G3 OK is not in the unit's history; every `next` after it must repeat `--given integration`.

### Option 2: Record every gate
- **Overview**: the superseded decision.
- **Pros**: every approval is in the unit's `decisions/`, the form devkit recommends for hosts.
- **Cons**: an extra commit for every session integration, and a second record of the PR ready state.

### Option 3: Ask G3 before the final commit
- **Overview**: present the final change report on the uncommitted change, record G3, then commit both together.
- **Pros**: one commit with a durable record.
- **Cons**: the order breaks whenever the user commits first or approves on a PR; the final report's head is not the
  approved head.

---

## 4. Decision Outcome

We decided to adopt **Option 1**, keeping devkit's default `ask` for every gate.

**Rationale**: G3 is the only gate whose record lands after the change is final, so it is the only gate whose record
costs a commit; the session OK and the PR ready state already state it once. A project that wants specrig's
direction behaviour still sets `direction = "auto"` in `[workflow.approvals]`.

---

## 5. Consequences

- **Positive**: integrating after an OK in a session needs no further commit; `devkit worktree finish` runs on the
  approved head.
- **Negative / Risks**: `--given integration` is an assertion an agent could make without an OK; the rule that an
  approval is never inferred now carries that gate alone, as it did in specrig. The integration report names the
  user's OK as the authority.
- **Follow-ups**: a G3 objection takes the stage's return path (`devkit workflow return --to review-refine|direction
  --note "..."`) instead of a recorded decline; a decision record a host UI writes still satisfies the gate; under
  `auto` the gate passes by policy (`source=policy`), reported as delegation, never as a human approval; `off`
  skips the stage; the `exception` stage has no gate; the intent gate always needs the user's intent; no policy
  value grants commit, merge, publication or deletion authority.
