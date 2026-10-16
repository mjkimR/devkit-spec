---
id: PLAN-proposal-effort-hints
spec: SPEC-proposal-effort-hints
---

# Technical Plan: `SPEC-proposal-effort-hints` Separate Planning and Development effort hints on proposals

## 1. Architecture Overview & Impact

- **Target Area**: `capabilities/delivery/`, `capabilities/harness/`, `capabilities/documents/`, `capabilities/governance/`
- **Design Summary**:
  - `planning_effort` and `dev_effort` (`low` | `medium` | `high`, default `medium`) are non-authoritative hint fields
    on `proposal.md` only. They preserve the recommended `activity-effort` across Backlog → Planning → Development
    without replacing `worker` envelopes as the sole execution record and without copying either field to `spec.md`.

## 2. Component Breakdown & Interface Contracts

### 2.1 Proposal Constants & Scaffolding (`src/devkit_spec/proposals/binding.py`, `scaffold.py`, `cli/proposals.py`)
- Define `EFFORTS = ("low", "medium", "high")`, `DEFAULT_EFFORT = "medium"`, `PLANNING_EFFORT = "planning_effort"`,
  `DEV_EFFORT = "dev_effort"` in `src/devkit_spec/proposals/binding.py`.
- Add `require_effort(value: str | None, option: str) -> str` in `src/devkit_spec/proposals/scaffold.py`, raising
  `ArgumentError` (`ARGUMENT_INVALID`) with `target_files=[option]` when `value` is not in `EFFORTS`.
- Extend `create_proposal` and `devkit spec proposal new` with `--planning-effort` and `--dev-effort` (default
  `medium`), write `planning_effort` and `dev_effort` into the scaffolded `proposal.md` frontmatter, and expose
  `planning_effort` and `dev_effort` on `CreatedProposal` (`to_dict()` and `[PROPOSAL: ...]`).

### 2.2 Format Rule (`src/devkit_spec/rules/spec_format.py`, `src/devkit_spec/rules/guides/RULE-spec-format/guide.md`)
- In `SpecFormatRule`, check proposal anchors (`docs/proposals/PROP-<slug>/proposal.md` and
  `docs/proposals/PROP-<slug>.md`) for optional `planning_effort` and `dev_effort` fields.
- When present on a proposal anchor and not a string in `EFFORTS`, emit a non-fixable `Violation` at `_field_line`
  naming `low`, `medium`, `high`.

### 2.3 Proposal Handoff (`src/devkit_spec/proposals/handoff.py`, `src/devkit_spec/cli/proposals.py`)
- Add `_effort(meta: dict[str, Any], field: str, proposal_rel: str) -> str | None` in `handoff.py` to validate
  `planning_effort` and `dev_effort` during preflight (`ProposalInvalidError` / `SPEC_PROPOSAL_INVALID` when present
  and not in `EFFORTS`, `None` when omitted on legacy proposals).
- Add `dev_effort: str | None = None` to `HandoffResult` (`to_dict()` and `[HANDOFF: ... dev_effort=<val>]` when
  present). Do not write `planning_effort` or `dev_effort` to `spec.md`.

### 2.4 Document Listing (`src/devkit_spec/cli/documents.py`)
- Add `PROPOSAL_FIELDS = ("task_kind", "planning_effort", "dev_effort")` and `_proposal_fields(document: Document)` in
  `src/devkit_spec/cli/documents.py` so `devkit spec list` includes `task_kind`, `planning_effort` and `dev_effort` on
  proposal documents in both JSON and `[DOCUMENT: ...]` text output.

### 2.5 Bundle Assets & Living Spec
- Update `src/devkit_spec/bundle/skills/spec/SKILL.md`, `references/classification.md`, `references/effort.md`,
  `src/devkit_spec/bundle/skills/spec-orchestrate/SKILL.md`, `src/devkit_spec/bundle/workflows/sdd-proposal.md`, and
  `src/devkit_spec/bundle/subagents/planning-worker.md`.
- Rebind existing proposals in `docs/proposals/PROP-*/proposal.md` to the updated `sdd-proposal` workflow hash and run
  `uv run devkit sync` so `.devkit/managed/` and `.devkit/installation.json` stay in sync.
- Update Living Spec documents (`CAP-DLV-proposal-incubation.md`, `CAP-DLV-delivery-workflows.md`,
  `CAP-DOCS-document-lookup.md`, `CAP-GOV-spec-rules.md`, `CAP-HARN-agent-guidance.md`, `docs/proposals/README.md`).

### Planned Boundaries:
- `capabilities/delivery/`
- `capabilities/harness/`
- `capabilities/documents/`
- `capabilities/governance/`

### Excluded Boundaries:
- `docs/decisions/`

## 3. Verification & Test Plan

- `uv run pytest` (unit and CLI tests in `tests/test_proposals.py`, `tests/test_documents.py`,
  `tests/test_spec_format_rule.py`, `tests/test_bundle.py`).
- `uv run devkit rules check` and `just ci`.
