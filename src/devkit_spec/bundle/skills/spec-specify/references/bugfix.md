# spec-specify reference: bugfix characterization and evidence

Read when the bundle is bound to workflow `bugfix` (a defect with contract impact or uncertainty). The `characterize` stage writes `spec.md`, the `reproduce` stage writes the Red envelope, the `fix-verify` stage writes the Green envelope. The shared contracts (non-goals, AC format, references, clarification rule, self-validation, DoD) are in `SKILL.md` §4 and §5. Stage order, checks and returns: `devkit workflow show --unit <dir>`; the current stage: `devkit workflow next --unit <dir>`.

## Step 1: Characterize the defect (stage `characterize`)

Write `spec.md` with `kind: bugfix` in the frontmatter (the stage exits on `frontmatter(spec.md kind bugfix)`) and these sections. Do not write a feature-style user story.

- **Current behavior**: the trigger conditions, environment and the observed wrong result, with evidence (log, failing command, test name).
- **Expected behavior and its basis**: the result the existing contract requires, citing the capability, story, ADR or test that defines it by ID. If the expected behavior itself is not agreed, stop and return to the `direction` gate (G2): that is a design decision, not a defect (`devkit workflow return --unit <dir> --to direction --note "<what is not agreed>"`).
- **Behavior to preserve**: the call paths, input boundaries and related contracts around the change point that must keep working. Name the existing tests that cover them and the gap that needs a new check.
- **Reproduction conditions**: the exact command, data and environment that reproduce the defect, or, when automation is impossible, the observation conditions and expected results that will serve as alternative evidence.
- **Scope**: what is excluded from this fix (unrelated cleanup, a contract or structure change that would need the delivery workflow). Non-goals state what is excluded, with a rationale or reopen trigger when it helps.
- **Acceptance criteria**: at least one `[AC-NN]` scenario for the resolved behavior and one for each preserved behavior, written so the Green envelope can cite them.

The `characterize` exit also runs `lint-clean`, which checks `spec.md` against the skeleton `tasks.md` beside it (`RULE-task-coverage`): until `spec-tasks` writes the real tasks, keep the skeleton task's `_Requirements:` line listing exactly the spec's AC IDs.

## Step 2: Reproduce before fixing (stage `reproduce`)

- Prefer an automated reproduction: a test that fails on the characterized defect before any fix. Keep it; it becomes the regression test.
- A compile, environment or test-setup failure unrelated to the defect is not reproduction evidence. A build failure that is the defect is.
- Record the Red envelope:

```bash
devkit workflow envelope new --unit <dir> --kind red --stage reproduce \
  --summary "<defect reproduced as characterized>" \
  --check reproduced="PASS <test or command> fails as characterized" \
  --base <ref> --head $(git rev-parse HEAD)
```

`checks.reproduced` starts with `PASS` only when the failure is the characterized one; otherwise record `--check reproduced="FAIL ..."` and return to `characterize` (`devkit workflow return --unit <dir> --to characterize`). `--head` is the commit the reproduction ran on; omit it when the reproduction ran on uncommitted work and say so with `--assume`.

## Step 3: Fix and verify (stage `fix-verify`)

- Implement within the task's expected scope (`_Boundary:` in `tasks.md`); explain any path beyond it in the report. Do not mix unrelated changes.
- Verify resolution under the same reproduction conditions and preservation over the declared paths. Record the Green envelope:

```bash
devkit workflow envelope new --unit <dir> --kind green --stage fix-verify \
  --summary "<resolved and preserved>" \
  --check resolved="PASS <same conditions now give the expected result>" \
  --check preserved="PASS <preserved behaviors and the tests run>" \
  --base <ref> --head $(git rev-parse HEAD)
```

- `revision-ancestor(red green)` is available for a stricter project workflow (it needs `--head` on both envelopes); the bundled `bugfix` workflow does not require it.
- `devkit workflow envelope check --unit <dir>` reports a malformed envelope; a malformed file never satisfies a check.

## Step 4: Alternative evidence

External outages, environment-dependent or non-deterministic defects: fix the observation conditions and expected results in `spec.md` first (Step 1), then report in the Green envelope whether resolution was confirmed and what uncertainty remains. One non-occurrence is not resolution; say so with `--unverified "<what remains unconfirmed>"`.

## Step 5: Route changes

When investigation shows the fix needs a contract change or a design choice, return to the `direction` gate (`devkit workflow return --unit <dir> --to direction`). If the work leaves the bugfix shape, agree the new route with the user (the `spec` skill's routing): rebind to delivery with `devkit workflow bind --unit <dir> --workflow direct-delivery`, or incubate the direction as a proposal. Say which approvals and which evidence stay valid (reproduction evidence usually does; AC and preserved-behavior lists are re-examined).

## Output standard

Keep the frontmatter lines `devkit spec new --workflow bugfix` or `devkit spec proposal handoff` wrote (`id`, `workflow`, `workflow_hash`) and add `kind: bugfix`.

```markdown
---
id: SPEC-<defect-slug>
title: <Defect Title>
status: draft # draft | planned | in-progress | completed
created: <YYYY-MM-DD>
kind: bugfix
related_capabilities:
  - CAP-<AREA>-<slug>
related_stories:
  - US-<slug>
workflow: bugfix                     # written by `devkit spec new --workflow bugfix` or `devkit spec proposal handoff`
workflow_hash: sha256:<hex>
---

# [SPEC-<defect-slug>] <Defect Title>

## 1. Current Behavior
<Trigger, environment, observed result, evidence.>

## 2. Expected Behavior and Basis
<Required result and the contract that defines it.>

## 3. Behavior to Preserve
<Paths, boundaries, existing tests, gaps.>

## 4. Reproduction Conditions
<Command, data, environment, or alternative observation conditions.>

## 5. Non-Goals
1. **Scope Excluded**: <Item>
   - **Rationale**: <Why, when it helps>
   - **When to Reconsider**: <Trigger, when one exists>

## 6. Acceptance Criteria & Behavioral Contracts
### Scenario 1: [AC-01] <Resolved behavior>
- **Given** <reproduction conditions>
- **When** <the trigger>
- **Then** <expected result>

### Scenario 2: [AC-02] <Preserved behavior>
- **Given** <neighboring path>
- **When** <its normal input>
- **Then** <unchanged result>
```
