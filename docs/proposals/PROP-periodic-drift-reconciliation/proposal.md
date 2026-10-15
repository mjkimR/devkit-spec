---
id: PROP-periodic-drift-reconciliation
title: Periodic spec-code drift check and user-driven reconciliation sweep
summary: "Explores a lightweight drift check between the Living Spec and code plus a user-driven sweep that decides per finding whether to update the spec, fix the code or waive it: the Tier 2 reconciliation of ADR-dual-source-of-truth-and-periodic-reconciliation."
status: draft                         # draft | reviewing | accepted | rejected
created_at: 2026-10-14
target_area: capabilities/delivery/
priority: medium                      # critical | high | medium | low
size: M                               # S | M | L | XL
boundaries:
  owns:
    - capabilities/delivery/
  excludes:
    - docs/decisions/
# handoff_workflow: bugfix            # workflow after handoff (default: direct-delivery)
workflow: incubated-delivery
workflow_hash: sha256:c6cf386f9eb37b061d626d4bc701dd4e01f43674666d160179f69da5c391463e
---

# [PROP-periodic-drift-reconciliation] Periodic spec-code drift check and user-driven reconciliation sweep

- **Parent decision**: `ADR-dual-source-of-truth-and-periodic-reconciliation`

## 1. Background & Hypothesis

### 1.1 Problem

- Per `ADR-dual-source-of-truth-and-periodic-reconciliation`, spec and code are complementary ledgers at different
  levels of abstraction.
- Even when `spec-sync` carries the core delta of each work unit, the interfaces, flags and terms the spec
  (`docs/capabilities/`, `docs/stories/`) names drift slightly from the code over time.
- Apart from reading by eye, nothing detects this, so drift is noticed only after it has piled up, and the large
  cleanup that follows is costly and tiring.

### 1.2 Hypothesis

- A **lightweight drift check** based on static analysis and heuristics lets the user notice drift before it crosses a
  threshold.
- Instead of the agent rewriting documents on its own, an interactive **reconciliation sweep** ("check report, user's
  intent, paired cleanup") keeps the Living Spec fresh at minimal effort.

## 2. Technical Spike Questions

- **Q1. Detection targets with acceptable precision.** Which of the candidates in 3.1 produce findings worth a user's
  attention? Section 4 records one candidate already rejected on data.
- **Q2. Check strength.** How strict can the check be before cleanup feels like homework? Collect how often, and in
  what form, cleanup sessions are needed when the bundle runs in other repositories.
- **Q3. Command or skill.** Whether detection needs a command (working name `devkit spec drift`) or the sweep can be a
  procedure over existing commands (`devkit spec list --file`, `devkit spec refs`, `devkit rules check`), for example a
  playbook next to `feedback-hygiene`.

## 3. Proposed Design & Impact

### 3.1 Lightweight Drift Detection

- **Candidate targets**:
  - Whether CLI flags and main interfaces or symbols named in `docs/capabilities/` exist in the code.
  - Whether file paths and module references are valid (`RULE-code-entrypoints` already checks declared
    entrypoints).
  - Living Spec documents left unchanged for long while the code they anchor changed.
- **Output**: suspected mismatches as sentinel lines or a Markdown report, following the agent-first output contract.

### 3.2 User-Driven Reconciliation

For each finding the agent offers three branches to the user:

1. **Update the spec**: the code is the new truth; rewrite the document to match.
2. **Fix the code**: the spec's intent is right and the code regressed; handle it as a bug.
3. **Waive**: out of scope for now, or an intentional temporary gap.

The sweep refactors documents interactively, through a dedicated skill or playbook (Q3).

## 4. Rejected Candidate: Entrypoint-Based Stale-Document Hints

- **Source**: code-entrypoints work, implemented as `CAP-TRACE-code-entrypoints` (entrypoint metadata and
  reverse lookup by path).
- **Examined**: join a change's Git paths with entrypoints and show the documents whose code changed but which were
  not updated, as non-blocking candidates and as input to the periodic check.
- **Conclusion: rejected.** `MAT-drift-candidate-retrospective` looked up the code paths of 47 completed specs
  (45 evaluation units) against the entrypoints of the time and compared them with the reconcile targets. Excluding
  self-derived declarations (leave-one-out), precision is 0.48 and recall 0.54. No noise filter (hub paths excluded,
  file granularity only, at least two code paths per document) raises precision above 0.5 while keeping recall at
  0.5, so the data gives no threshold. Of ten false-positive pairs (not random: the first unit for each top
  entrypoint), eight were changes to what the document does not describe (file moves and splits, internal helper
  swaps, generated files, details delegated to other documents) and two were real updates fixed later in another
  commit.
- **What remains**: both late updates were places where a document restated a cross-cutting convention in prose
  (where the integration approval is recorded, the spec path format). Prose drift at that semantic level is caught
  neither by path lookup, nor by the path validity check of 3.1, nor by devkit's `RULE-cli-contract`, which checks
  only command citations. The main cause of lost recall is documents with narrow declarations, which no threshold
  fixes.
- **Reopen condition**: the same measurement on another repository gives leave-one-out precision of at least 0.6
  together with recall of at least 0.5. Integration into the `spec-review` skill is then designed separately.

## 5. Lifecycle & Retirement Criteria

- **Priority**: low until the bundle runs in other repositories; mature this proposal from the drift patterns observed
  there.
- Preliminary decisions: a PADR for the detection threshold and noise policy if Q1 settles on a check; the parent
  decision stays `ADR-dual-source-of-truth-and-periodic-reconciliation`.
- On acceptance: set `status: accepted` and run `devkit spec proposal handoff periodic-drift-reconciliation`.
- On rejection: record a rejection ADR in `docs/decisions/` and delete the proposal directory.
