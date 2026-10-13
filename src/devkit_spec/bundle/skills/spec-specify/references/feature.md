# spec-specify reference: feature specification

Read when the bundle is bound to workflow `direct-delivery` (a new feature, enhancement or contract change). The procedure fills `spec.md` during the `specify` stage. The shared contracts (non-goals, AC format, references, clarification rule, self-validation, DoD) are in `SKILL.md` §4 and §5 and are not repeated here.

## Step 1: Clarify intent and the core problem

- Ask targeted questions to understand the real user problem, target audience and business context (3-question batches, options with a recommended default).
- Identify the primary user story:
  - **As a** `<role>`
  - **I want to** `<action/capability>`
  - **So that** `<outcome/value>`
- When an existing story already expresses it, cite it by ID (`` `US-<slug>` ``) and list it in `related_stories`.

## Step 2: Establish non-goals

Define what this feature will **not** do. Each non-goal names its Scope Excluded; give the Rationale and a When to Reconsider trigger when a later reader would otherwise reopen the question.

## Step 3: Define acceptance scenarios

- One H3 per scenario with its `[AC-NN]` ID and Given/When/Then.
- Cover the happy path, boundary values, error scenarios (the interface's error contract: exit codes, status or error codes, error payloads) and permission or unauthorized cases.
- Prefer scenarios a test or a CLI run can confirm literally.

## Step 4: Validate against system invariants

Review `docs/architecture/` and the capabilities the feature touches (`devkit spec refs <CAP-ID> --direction in` shows what depends on them). State explicitly when an ADR will be required. A new policy or design choice outside the approved scope goes back to the `direction` gate (`devkit workflow return --unit <dir> --to direction --note "<choice>"`).

## Step 5: Output standard

Keep the frontmatter lines `devkit spec new` or `devkit spec proposal handoff` wrote (`id`, `workflow`, `workflow_hash`); fill in the rest.

```markdown
---
id: SPEC-<feature-slug>
title: <Feature Title>
status: draft # draft | planned | in-progress | completed
created: <YYYY-MM-DD>
related_capabilities:
  - CAP-<AREA>-<slug>
related_stories:
  - US-<slug>
workflow: direct-delivery           # written by `devkit spec new` or `devkit spec proposal handoff`
workflow_hash: sha256:<hex>
---

# [SPEC-<feature-slug>] <Feature Title>

## 1. Problem Statement & Motivation
<Brief context on why this feature is needed and the expected outcome.>

## 2. User Stories
- **US-1**: As a <role>, I want <goal>, so that <value>.

## 3. Non-Goals
1. **Scope Excluded**: <Item>
   - **Rationale**: <Why, when it helps>
   - **When to Reconsider**: <Trigger, when one exists>

## 4. Acceptance Criteria & Behavioral Contracts
### Scenario 1: [AC-01] <Happy Path Scenario>
- **Given** <precondition>
- **When** <action>
- **Then** <outcome>

### Scenario 2: [AC-02] <Error / Edge Case Scenario>
- **Given** <precondition>
- **When** <invalid input or edge condition>
- **Then** <expected error response>

## 5. Security, Privacy & Compliance Considerations (optional: drop when the change has none)
<Permission boundaries, sensitive data handling, auth constraints.>
```

Leave `related_capabilities` or `related_stories` as `[]` when the feature has none yet; every listed ID must resolve (`devkit spec resolve <ID>`).
