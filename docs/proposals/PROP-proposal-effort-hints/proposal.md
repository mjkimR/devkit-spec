---
id: PROP-proposal-effort-hints
title: Separate Planning and Development effort hints on proposals
summary: Adds separate Planning and Development effort hint fields to proposal frontmatter so Backlog and Planning preserve recommended activity-effort values that Host sessions and autohub submission screens pre-fill and let the user override.
status: accepted                      # draft | reviewing | accepted | rejected
created_at: 2026-10-16
target_area: capabilities/delivery/
priority: medium                      # critical | high | medium | low
size: S                               # S | M | L | XL
boundaries:
  owns:
    - capabilities/delivery/
    - capabilities/harness/
  excludes:
    - docs/decisions/
task_kind: feature                    # feature | bugfix: the spec follows sdd-spec-<task_kind>
workflow: sdd-proposal
workflow_hash: sha256:1ef60809329fded5a496efb7757fd2d07c59a9c1ec1aef6858bbef2fb5d65fc0
---

# [PROP-proposal-effort-hints] Separate Planning and Development effort hints on proposals

- **Parent design**: the strategy layer's master flow (workbench `docs/strategy-layer/01-master-flow.md`, §2
  classification axes, §2.3 `activity-effort`, §3 `plan-intent` and `plan-accept`, §6.2 proposal Planning, §7.1
  Development, §10 autohub changes) and policy (`03-policy.md` §2 and §8 on where `activity-effort` lives).
- **Related**: `SPEC-planning-effort-safeguards` (effort proposed at `plan-intent` and shown at `plan-accept`),
  `ADR-task-kind-and-planning-depth` (axis values not stored as authoritative state on the Unit),
  `CAP-DLV-proposal-incubation`, `CAP-DLV-delivery-workflows`, `CAP-DOCS-document-lookup`, `CAP-GOV-spec-rules`,
  `CAP-HARN-agent-guidance`.

## 1. Background & Hypothesis

### 1.1 Problem

- **Recommended effort is lost between activities.** `activity-effort` (`low` | `medium` | `high`) is chosen when each
  activity starts and passed as run input; the applied value is recorded only in the run's `worker` envelope (01 §2.3,
  03 §8). However, the best moment to judge a proposal's Planning effort is when Backlog frames `plan-intent`, and the
  best moment to judge its Development effort is at the end of Planning (`direction-handoff`), when cross-package impact,
  contract surface and verification risks have just been analyzed. Without a place on the proposal to hold those
  recommendations, a later session or a different executor must re-derive them from scratch.
- **Planning effort and Development effort differ.** A single `effort` field cannot represent both activities: a
  proposal with an open architectural trade-off but a small, localized code change needs `high` Planning and `low` or
  `medium` Development; a proposal with a clear direction that touches multiple packages needs `low` or `medium`
  Planning and `high` Development.
- **`cloud-pr` submission in autohub lacks a pre-filled recommendation.** In local modes (`direct`,
  `local-orchestrated`), the Host converses with the user at activity start to propose an effort. In autohub,
  `SddExecution.svelte` currently initializes `let effort = $state<'low' | 'medium' | 'high'>('medium')` with no link to
  the selected proposal's frontmatter or the `/sdd/readiness` response, and `RepositoryView.svelte` only wires
  `specs/YYYY-MM/<bundle>` into `selectedSpec` on `onselectpath` (ignoring `docs/proposals/PROP-<slug>`). When a user
  starts a Planning review or a Development handoff run from autohub, the UI cannot pre-fill the recommended effort for
  the user to confirm or override before submitting.

### 1.2 Codebase & Cross-Package Drilling

Inspection of `devkit-spec` and `autohub` (`main`) surfaces seven concrete boundaries this proposal must settle:

1. **Strategy layer invariant (Hint vs. Authoritative State).** `01-master-flow.md` §2 states that classification and
   execution axes are not stored as fields on the Unit (with `task_kind` on `proposal.md` as the sole exception because
   binding happens at handoff). `planning_effort` and `dev_effort` must be explicitly defined in 01 §2 and §2.3 as
   **non-authoritative recommendation hints** on `proposal.md` only:
   - They never satisfy or relax any gate, exit check or review requirement.
   - `worker` envelopes remain the sole authoritative record of the effort actually applied in a run (03 §8).
   - `spec.md` never carries `planning_effort` or `dev_effort`: by the time `spec.md` exists, Planning is over and
     Development is starting.
2. **Handoff timing vs. Development effort consumption.** The moment `dev_effort` is read differs by execution mode
   (01 §7.1):
   - In **`direct` and `local-orchestrated`**, the Host starts `dev-<slug>` and runs `devkit spec proposal handoff
     <slug>` **before** spawning the Development worker (`spec-orchestrate`). Because `handoff` deletes `proposal.md`
     (step 7 of `handoff_proposal` in `src/devkit_spec/proposals/handoff.py`), `dev_effort` would vanish with
     `proposal.md` unless `handoff` surfaces it in `HandoffResult` (`[HANDOFF: ... dev_effort=<value>]` and JSON
     `dev_effort`).
   - In **`cloud-pr`**, the user submits the Development run in autohub **before** `handoff` runs (the Cloud Agent runs
     `devkit spec proposal handoff <slug>` as the first step of the run on `dev-<slug>`, 01 §7.1). At submission time in
     autohub, the target in the repository is still the `accepted` proposal (`docs/proposals/PROP-<slug>/proposal.md`),
     so autohub can read `dev_effort` directly from the proposal frontmatter (via the viewer or `/sdd/readiness`) and
     pre-fill the effort selector before the user submits `POST /api/v1/projects/{project_id}/runs` with
     `activity_effort`.
3. **Updating `dev_effort` during Planning without YAML re-serialization.** In `sdd-proposal`, the Planning executor
   (`direct` Host, `planning-worker`, or Cloud Agent) already edits `proposal.md` on `plan-<slug>`. If the spike or
   challenger pass reveals that implementation or Living Spec reconciliation crosses multiple packages or contracts, the
   Planning executor updates `dev_effort` in `proposal.md` before `direction-handoff`. In `cloud-pr` (or if the user
   wants to adjust `dev_effort` at `plan-accept`), `autohub`'s deterministic `accept_plan` commit (`sdd/units.py`
   `set_status`) only rewrites `status: reviewing` → `status: accepted` unless `accept_plan` also accepts an optional
   `dev_effort` override or leaves `dev_effort` to the Planning run.
4. **Validation in `RULE-spec-format` and `handoff`.** Currently `RULE-spec-format` (`src/devkit_spec/rules/spec_format.py`)
   validates `id`, `title`, `status` and anchor `namespace`, while `handoff.py` validates `status`, `needs_decompose`,
   `namespace`, `summary` and `task_kind` (`_task_kind`). If `planning_effort` or `dev_effort` is present on
   `proposal.md` with a typo (for example `highh` or an integer), `RULE-spec-format` (linter phase) and `handoff`
   preflight should catch it early rather than letting autohub or a skill silently fall back to `medium`.
5. **Browsing and indexing (`devkit spec list proposal`).** In `src/devkit_spec/cli/documents.py`, `list` prints extra
   kind-specific fields only for `feedback` (`_feedback_fields`: `severity`, `scope`, `target`). Proposals currently
   emit only `status`, optional `planning_branch`, `tasks=None`, `namespace` and `title`. Exposing `task_kind`,
   `planning_effort` and `dev_effort` on proposal items in `devkit spec list proposal` (both `[DOCUMENT: ...]` sentinel
   and JSON `documents[]`) makes them immediately available to `spec-next` and CLI consumers, and `--where
   planning_effort=high` already works through `_matches`.
6. **autohub Viewer and Execution Panel wiring.**
   - `RepositoryView.svelte` line 299 currently sets `selectedSpec = path.match(/^(specs\/\d{4}-\d{2}\/[^/]+)/)?.[1] || ''`,
     which ignores `docs/proposals/PROP-<slug>` even though `SddExecution.svelte` accepts both specs and proposals.
   - `SddViewer.svelte` (`dispatchItemSelected`) already receives `(path, frontmatter)` from both `KnowledgeViews.svelte`
     (Proposals/Specs tabs) and `loadBlob` (Files tab), but `onselectpath?: (path: string) => void` drops `frontmatter`.
   - `SddUseCase.readiness` (`sdd/usecases.py`) and `SddService.evaluate` (`sdd/services.py`) already inspect the
     unit's anchor on the PR head (`read_status(root, spec_dir)`). Returning `recommended_effort` (or `planning_effort` /
     `dev_effort`) in `SddReadiness` covers the case where the user types the unit directory and PR number directly into
     `SddExecution.svelte` without clicking in `SddViewer` first.
7. **Carry-over on decomposition and supersede.** When Backlog decomposes a draft (`--decomposed-from`,
   `PROP-backlog-roadmap-and-issues`) or closes an accepted proposal by supersede (`--supersedes`, 01 §7.4), the new
   draft's effort should be judged for the new scope (defaulting to `medium` unless `--planning-effort` /
   `--dev-effort` are passed), rather than blindly copying the parent's effort.

### 1.3 Hypothesis

Adding `planning_effort` and `dev_effort` (`low` | `medium` | `high`, scaffolded as `medium`) as explicit **hint
fields** on `proposal.md` preserves the recommended `activity-effort` across Backlog → Planning → Development while
keeping `worker` envelopes as the only execution evidence:

- Local Host sessions read `planning_effort` (at `plan-intent` / Planning start) and `dev_effort` (at `plan-accept` /
  Development start, or from `handoff` output) as the initial recommendation to confirm with the user.
- autohub pre-fills the `Activity effort` selector in `SddExecution` (and future Proposals action modals) from
  `planning_effort` when starting a Planning review and from `dev_effort` when starting Development / handoff, while
  allowing the user to change the value before submitting the run.

## 2. Technical Spike Questions

- **Q1. Frontmatter keys, defaults and existing proposals.**
  - **Recommendation**: Use `planning_effort` and `dev_effort` (`low` | `medium` | `high`). `devkit spec proposal new`
    always scaffolds both with `medium` (alongside `priority: high`, `size: M`, `task_kind: feature`) and accepts
    `--planning-effort` and `--dev-effort`. For existing proposals or hand-written drafts that omit either key,
    readers (`handoff`, `list`, `autohub`) treat a missing key as `None` (falling back to `medium` at UI/Host proposal
    time) without requiring a migration of historical proposals, while `RULE-spec-format` validates the value whenever
    the key is present.
- **Q2. Lifecycle across Backlog and Planning (`plan-intent` → `spike` → `plan-accept`).**
  - **Recommendation**:
    1. **Backlog (`plan-intent`)**: When creating a draft, the Host sets `planning_effort` (and provisional
       `dev_effort`, default `medium`) using the 01 §2.3 criteria (`high` if reversing an upstream/accepted decision,
       creating a contract/document kind, or affecting multiple packages) and confirms `planning_effort` with the user
       at `plan-intent`.
    2. **Planning (`spike` / `direction-handoff`)**: Before finishing Planning, the executor (`direct` Host,
       `planning-worker`, or Cloud Agent) reviews `dev_effort` against the settled design and target boundaries and
       updates `dev_effort` in `proposal.md` if the expected implementation/reconcile thoroughness changed.
    3. **Acceptance (`plan-accept`)**: The `plan-accept` summary shows (a) each Planning run's applied `activity_effort`
       and support-role envelopes (`SPEC-planning-effort-safeguards`), and (b) the recommended `dev_effort` for
       Development.
- **Q3. Handoff contract (`devkit spec proposal handoff`).**
  - **Recommendation**: `handoff` validates `planning_effort` and `dev_effort` if present (`SPEC_PROPOSAL_INVALID` when
    not `low` | `medium` | `high`), includes `dev_effort` on `HandoffResult` (`[HANDOFF: PROP-<slug> spec=SPEC-<slug>
    dir=... workflow=... dev_effort=medium]` when present, and JSON `"dev_effort": "medium" | null`), and **does not**
    write either field to `spec.md`. That way a local Host that runs `handoff` first still has `dev_effort` in hand when
    proposing Development effort or spawning `development-worker`.
- **Q4. Hint vs. authoritative record when overridden.**
  - **Recommendation**: If the user overrides the hint at activity start (in conversation or in autohub's UI), the
    proposal file does **not** need a retroactive commit just to match the override: the run executes at the
    user-chosen effort and records it in the run's `worker` envelope (`activity_effort`). At `plan-accept`, if a
    Planning run's `worker` envelope `activity_effort` is lower than `proposal.md`'s `planning_effort` (for example,
    `planning_effort: high` in `proposal.md`, but the run executed at `medium`), the `plan-accept` summary notes the
    difference alongside the support-role check so the user can see whether the downgrade was intentional.
- **Q5. Exposure in `devkit spec list proposal` and autohub UI.**
  - **Recommendation**:
    - In `devkit spec list`, add `_proposal_fields(document)` (like `_feedback_fields`) emitting `task_kind`,
      `planning_effort` and `dev_effort` on proposal records in JSON and text sentinel output.
    - In `autohub`, update `RepositoryView.svelte` / `SddViewer.svelte` so selecting a proposal or spec passes both the
      unit path and its frontmatter (or unit metadata), and include `recommended_effort` in `SddReadiness` (`read_effort`
      in `sdd/units.py`: `planning_effort` when the proposal is `draft` / `reviewing` on `plan-<slug>`, `dev_effort`
      when handing off / starting `dev-<slug>`). `SddExecution.svelte` pre-fills `effort` from that recommendation and
      keeps the `<select>` editable before the user clicks `Start execution`.

## 3. Proposed Design & Impact

### 3.1 `proposal.md` Frontmatter & Scaffolding (`devkit-spec`)

```yaml
---
id: PROP-<slug>
title: <title>
summary: "<one or two English sentences>"
status: draft                         # draft | reviewing | accepted | rejected
created_at: YYYY-MM-DD
target_area: capabilities/<area>/
priority: high                        # critical | high | medium | low
size: M                               # S | M | L | XL
planning_effort: medium               # low | medium | high (hint for Planning)
dev_effort: medium                    # low | medium | high (hint for Development)
boundaries:
  owns:
    - capabilities/<area>/
  excludes:
    - docs/decisions/
task_kind: feature                    # feature | bugfix: the spec follows sdd-spec-<task_kind>
---
```

- **Constants (`src/devkit_spec/proposals/binding.py` or `scaffold.py`)**:
  - `EFFORTS = ("low", "medium", "high")`, `DEFAULT_EFFORT = "medium"`.
  - `PLANNING_EFFORT = "planning_effort"`, `DEV_EFFORT = "dev_effort"`.
- **`devkit spec proposal new` (`src/devkit_spec/proposals/scaffold.py`, `src/devkit_spec/cli/proposals.py`)**:
  - New options `--planning-effort` and `--dev-effort` (default `medium`; invalid values raise `ArgumentError` /
    `ARGUMENT_INVALID` with `target_files=["--planning-effort"]` or `["--dev-effort"]`).
  - `CreatedProposal` includes `planning_effort: str` and `dev_effort: str` in `to_dict()` and `[PROPOSAL: ...]`
    sentinel output.
- **`RULE-spec-format` (`src/devkit_spec/rules/spec_format.py`)**:
  - On any proposal anchor (`docs/proposals/PROP-<slug>/proposal.md` or `docs/proposals/PROP-<slug>.md`), if
    `planning_effort` or `dev_effort` is present in frontmatter, it MUST be one of `low`, `medium`, `high`
    (non-fixable `ERROR`, remediation naming the three valid values).
  - On `spec.md` anchors, `planning_effort` and `dev_effort` are not part of the spec schema.
- **`devkit spec proposal handoff` (`src/devkit_spec/proposals/handoff.py`, `src/devkit_spec/cli/proposals.py`)**:
  - Preflight validates `planning_effort` and `dev_effort` when present in `proposal.md` (`ProposalInvalidError` /
    `SPEC_PROPOSAL_INVALID` if not a valid effort string; `None` when omitted on legacy proposals).
  - `HandoffResult` gains `dev_effort: str | None = None`: included in `to_dict()` (`"dev_effort"`) and appended to
    `[HANDOFF: <proposal> spec=<spec> dir=<dir> workflow=<workflow> dev_effort=<effort>]` when present.
  - Neither field is written to `spec.md`.
- **`devkit spec list` (`src/devkit_spec/cli/documents.py`)**:
  - Proposal items include `task_kind`, `planning_effort` and `dev_effort` (`None` when absent on legacy files) in JSON
    `documents[]` and on `[DOCUMENT: ...]` lines.

### 3.2 Workflow & Agent Guidance (`devkit-spec` bundle)

- **`src/devkit_spec/bundle/skills/spec/references/classification.md` & `effort.md`**:
  - Backlog sets `--planning-effort` and `--dev-effort` when running `devkit spec proposal new` and states both in the
    `plan-intent` confirmation request.
  - When starting Planning or Development of a proposal, the Host reads `planning_effort` or `dev_effort` (or
    `HandoffResult.dev_effort`) as the default proposal, states the reason, and lets the user confirm or override it.
- **`src/devkit_spec/bundle/workflows/sdd-proposal.md` & `subagents/planning-worker.md`**:
  - Step 4/5 of `planning-worker` (and the `direct` Planning procedure) checks whether `dev_effort` in `proposal.md`
    matches the settled design's risk (for example, raising `dev_effort` to `high` when the spike reveals multi-package
    or new-contract impact) and updates `proposal.md` before the final work commit.
  - The `plan-accept` request shows the recommended `dev_effort` for Development alongside the Planning effort and
    support-role summary, and notes when a Planning run's applied `activity_effort` differed from `planning_effort`.

### 3.3 autohub Integration (`autohub`)

- **Readiness & Unit inspection (`modules/hub/app/features/project_management/sdd/`)**:
  - `units.py`: add helper `read_efforts(root: Path, unit: str) -> dict[str, str | None]` reading `planning_effort` and
    `dev_effort` from `proposal.md` frontmatter when `is_proposal(unit)`.
  - `schemas.py` (`SddReadiness`) & `usecases.py` (`SddUseCase.readiness`): return `recommended_effort: Literal["low",
    "medium", "high"] | None = None` (for a proposal on `plan-<slug>`, `planning_effort`; for a proposal or handoff on
    `dev-<slug>`, `dev_effort`).
- **Repository Viewer & Execution UI (`modules/hub-ui/src/lib/features/project-management/repositories/`)**:
  - `KnowledgeViews.svelte`: display `planning_effort` / `dev_effort` badges on proposal cards/headers so operators see
    the expected thoroughness in the Proposals tab.
  - `RepositoryView.svelte` & `SddViewer.svelte`: extend selection callback so clicking a proposal (`docs/proposals/PROP-<slug>`)
    or spec (`specs/<YYYY-MM>/<bundle>`) populates `selectedSpec` in `SddExecution.svelte` and passes the proposal's
    hint (`planning_effort` when `status` is `draft`/`reviewing`, `dev_effort` when `status` is `accepted`) as the
    initial `effort` state.
  - `SddExecution.svelte` (and the future Proposals start/handoff action modal in 01 §10): pre-fills the `Activity
    effort` selector with the hint (defaulting to `'medium'` when absent), updates it if `/sdd/readiness` returns
    `recommended_effort` and the user has not manually overridden it, and submits the user's chosen `activity_effort`
    to `POST /api/v1/projects/{project_id}/runs`.

### 3.4 Non-Goals

- **Scope Excluded**: storing `activity-effort` on `spec.md` or treating proposal hint fields as execution evidence.
  `worker` envelopes remain the sole record of applied effort.
- **Scope Excluded**: adding hint fields for work mode (`direct` | `local-orchestrated` | `cloud-pr`) or model settings
  (`model-effort`).
- **Scope Excluded**: changing `session` or inline `spec` Planning; neither uses a proposal Unit.
- **Scope Excluded**: blocking `plan-accept` or `handoff` when the user overrides the hint with a different effort at
  run start.

## 4. Lifecycle & Retirement Criteria

- **Order of change**: update the strategy layer (`docs/strategy-layer/01-master-flow.md` §2, §2.3, §3, §6.2, §7.1, §10,
  `02-architecture.md` §3, and `03-policy.md` §8) first in workbench; `devkit-spec` and `autohub` then follow.
- On acceptance (`plan-accept`): record `gate:plan-accept`, set `status: accepted` and merge the Planning branch;
  Development starts with `devkit spec proposal handoff proposal-effort-hints`.
- On rejection: change only `status: rejected`, with the user's reason in the commit message; a later hygiene pass
  writes the rejection ADR and deletes the proposal directory.


