---
name: spec-specify
description: Turn a feature request or a defect report into a verifiable spec.md in specs/ (Given/When/Then acceptance criteria, explicit non-goals), creating the bundle bound to its workflow with `devkit spec new` and routing to the feature or bugfix reference.
---

# spec-specify: Specification Router

Use this skill when a spec bundle `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` needs its `spec.md`: a new feature or substantial enhancement (Route 2, or after `devkit spec proposal handoff`), or a formal bugfix (workflow `bugfix`). This file holds the prerequisites, the bundle creation, the choice of reference and the contracts both references share; the procedure itself is in `references/`.

## 1. Prerequisites

- Check whether an active spec already covers this work: `devkit spec list spec` (completed bundles are left out unless `--history`). Completed specs are work history, not inputs; the current contract lives in `docs/capabilities/` and `docs/stories/`.
- Look for overlap, extension or conflict with the Living Spec: `devkit spec search "<query>"` (`--kind capability`, `--kind decision`), `devkit spec list capability decision`, and `devkit spec refs <ID> --direction in` for what depends on a document the change touches.
- Read `devkit spec policy`: `[GATE_POLICY: direction policy=auto ...]` permits decisions inside the requested scope with reported assumptions; `policy=ask` requires confirmation of concrete new direction choices. Existing approvals and explicit user instructions take precedence; unresolved scope still needs input.
- Read the `contract-authoring` instruction before writing acceptance criteria and non-goals, and `living-spec-writing` before citing Living Spec documents.

## 2. Create or open the bundle

- **Handed-off bundle** (`devkit spec proposal handoff`): it already exists and is bound; `spec.md`, `plan.md` and `tasks.md` carry the skeleton marker. Rewrite `spec.md` in place, keeping the carried content that still holds.
- **New bundle**: `devkit spec new <slug> --title "<Title>" --summary "<English sentence>"` for a feature (workflow `direct-delivery`), `devkit spec new <slug> --title "<Title>" --workflow bugfix` for a defect. It creates `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/` with skeleton `spec.md`, `plan.md` and `tasks.md`, sets the ID `SPEC-<slug>` and binds the bundle. In a monorepo the bundle takes the namespace of the current directory (`namespace=` in the output); create a package's bundle from the package directory or pass `--namespace <name>`. Never hand-make the bundle or its binding. The slug is kebab-case, has no date or sequence number and is unique among specs (`RULE-id-convention`).
- Read the workflow the bundle follows: `devkit workflow show --unit <dir>`; `devkit workflow next --unit <dir>` names the current stage and what is unmet.

## 3. Choose the reference

| Situation | Reference |
| :--- | :--- |
| New capability, enhancement, contract change; bundle bound to `direct-delivery` | [feature](references/feature.md): discovery questions, user story, acceptance scenarios, output standard |
| Defect with contract impact or uncertainty; bundle bound to `bugfix`, or the intent is to fix observed wrong behavior | [bugfix](references/bugfix.md): defect characterization (`kind: bugfix`), reproduction evidence before the fix, resolution and preservation evidence after it |

Read one reference, not both. A small, low-risk defect is Route 1 (workflow `s-lane`) and needs no `spec.md`.

## 4. Shared contracts

- **Non-goals** state **Scope Excluded**. Add **Rationale** and **When to Reconsider** when they help a later reader decide; do not fill them for form.
- **Acceptance criteria**: every H3 under the H2 whose title contains `Acceptance Criteria` is one scenario with exactly one `[AC-NN]` ID (`AC-` and at least two digits, unique in the spec) and Given/When/Then lines (`RULE-task-coverage`). Explanatory tables and prose go in paragraphs, never in an H3 there. Renumbering an ID later breaks the task links; add new IDs instead.
- **Measurable Then**: no "fast", "robust", "properly"; use verifiable bounds (exit code, status code, exact output line, count).
- **References**: cite capabilities, stories and ADRs by full ID in backticks (`` `CAP-<AREA>-<slug>` ``), never by Markdown path or a date- or number-based ID. Write example or fixture IDs in a scenario as plain text: in backticks or brackets they are references and must resolve; `related_capabilities` and `related_stories` hold bare `CAP` and `US` IDs that resolve (`RULE-document-reference`).
- **Invariants**: review `docs/architecture/` and the affected capabilities. If a `MUST` has to change, say that an ADR is required before implementation.
- **Clarification**: ask at most 3 questions per batch, each with 2 to 3 options and a recommended default; mark unresolved points `[NEEDS CLARIFICATION]`.
- **Only what the change needs**: drop an optional output section that does not apply instead of writing "N/A".
- **Self-validation** before finishing: completeness (personas, inputs, outputs, edge cases), clarity (every AC measurable), consistency (non-goals and invariants respected), scenario IDs unique.

## 5. Definition of Done

- [ ] User and agent agree on the boundary (feature) or on current, expected and preserved behavior (bugfix).
- [ ] Every non-goal states what is excluded; every AC is mechanically checkable.
- [ ] `spec.md` written in the reference's output standard, keeping the `id`, `workflow` and `workflow_hash` frontmatter the bundle was created with, and an English `summary` of what the spec changes (`RULE-document-summary`).
- [ ] The skeleton marker line `<!-- devkit:skeleton -->` is removed from `spec.md`; until then `not-skeleton(spec.md)` keeps the `specify` (feature) or `characterize` (bugfix) stage open. The markers in `plan.md` and `tasks.md` are removed by `spec-plan` and `spec-tasks`.
- [ ] `devkit rules check <dir>` reports no spec-rule violation other than coverage the tasks have not been written for yet.
- [ ] Ready for `spec-plan` (feature: still the `specify` stage; bugfix: the `plan-tasks` stage once `direction` holds).
