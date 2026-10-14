---
id: MAT-drift-candidate-retrospective
title: Retrospective measurement of entrypoint-based stale-document candidates
status: draft
created_at: 2026-10-08
---

> **Purpose**: measurement record from specrig, the predecessor of devkit-spec, kept as the evidence behind section 4
> of `PROP-periodic-drift-reconciliation`. It compares the documents predicted by looking up completed specs' code
> changes through the current `entrypoints` with the documents their `reconcile.md` actually updated, to measure the
> precision, recall and false-positive causes of a stale-document candidate check. The reproduction script
> (`retrospective.py`) and its full output (`retrospective-output.md`) stay in the specrig repository
> (`mjkimR/specrig`, commit `2c838bb`, `docs/materials/2026-10/20261008-drift-candidate-retrospective/`); the script
> drives the specrig CLI and must be adapted to `devkit spec list` and `devkit spec entrypoints derive` before it runs
> on another repository. Document IDs below are specrig's and do not exist in devkit-spec.

# [MAT-drift-candidate-retrospective] Retrospective measurement of entrypoint-based stale-document candidates

## Method

- Input: the 47 completed specs at specrig commit `74826664`, 30 capabilities and stories (27 declaring
  `entrypoints`, 91 declarations), and the derivation evidence of `specrig entrypoints derive --all`.
- Evaluation unit: commits that touched completed bundles, grouped by the set of bundles each changed. Commits changing
  one bundle form single units (33 evaluated); commits changing two or three form joint units (12 evaluated). Commits
  changing four or more are maintenance such as bulk identifier changes and were excluded. 11 of the 47 completed
  specs appear only in joint units, because the actual work commit carried two or three specs.
- Expected set: documents whose `entrypoints` overlap the unit's changed paths outside `docs/` and `specs/`. Documents
  created (`created_at`) after the unit's last commit did not exist then and were excluded (5 cases).
- Actual set: the capabilities and stories among the `reconcile.md` targets of the unit's specs with
  `resolution: modified`.
- Correction: many current `entrypoints` (32 of 91) were derived from a single spec, from that spec's targets and
  `_Boundary`. Leave-one-out (LOO), which drops such a declaration when evaluating its source spec, is the baseline.
- Variants: excluding targets whose change was metadata only, excluding hub paths (13 paths changed by at least 20% of
  units, 9 or more), file-granularity entrypoints only, at least two overlapping code paths per document, and hub
  exclusion combined with file granularity.

## Results

Micro-aggregated over all 45 units. The single-unit aggregate (33 units) is in the output file; precision and recall
differ by at most 0.07 per variant.

| Variant | Expected | Actual | Hits | Precision | Recall | False positives |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | 240 | 204 | 119 | 0.50 | 0.58 | 121 |
| LOO | 231 | 204 | 110 | 0.48 | 0.54 | 121 |
| LOO, metadata-only targets excluded | 231 | 180 | 108 | 0.47 | 0.60 | 123 |
| LOO, hub paths excluded | 195 | 204 | 95 | 0.49 | 0.47 | 100 |
| LOO, file granularity only | 156 | 204 | 77 | 0.49 | 0.38 | 79 |
| LOO, at least two code paths per document | 122 | 204 | 70 | 0.57 | 0.34 | 52 |
| LOO, hub exclusion and file granularity | 122 | 204 | 62 | 0.51 | 0.30 | 60 |

- The baseline (LOO) is precision 0.48, recall 0.54: one candidate in two is a document absent from the reconcile
  record, and close to half of the documents actually updated are not candidates.
- LOO removed only 9 hits; the circularity introduced by backfilled declarations does not inflate the figures much.
- No noise filter lifts precision above 0.6. The best, "at least two code paths per document", cuts false positives
  from 121 to 52 but drops recall to 0.34. Hub exclusion and file granularity remove false positives and hits in
  similar proportion, leaving precision unchanged.
- Individual specs vary widely. SPEC-cli-command-layout, mostly file moves, reconciled no capability or story (actual
  0) yet had 9 expected; SPEC-skill-entry-consolidation had 1 of 13. Narrow feature specs (handoff link rewriting,
  rule config override) score 1.00 on both.

## Causes of False Positives

Of the top 10 entrypoints by LOO false positives, 4 are directories and 6 files. File-level false positives come from
shared files that many features change (`cli/internal/scaffold/proposal.go`, `proposal_handoff.go`,
`template/agents/skills/sr-sync/SKILL.md`, `.specrig/governance/rules/imports_gen.go`). The same files produce hits
about as often (for example `proposal.go`: 5 false positives and 5 hits for CAP-LIFE-proposal-incubation-and-handoff).
False positives therefore come less from wrong declarations than from the fact that a path cannot tell whether a change
to a shared file changes what its owning document says. Only 4 of the top 10 false-positive code paths meet the hub
criterion (9 or more units), so hub exclusion leaves most causes in place.

### Judged False-Positive Sample

For each of the top 10 false-positive entrypoints, the first false-positive unit was judged against the commit diff
and the document at the time. `missed-update`: behavior, a command or a path the document described changed and was not
updated. `updated-elsewhere`: an update was needed and was made in another commit. `noise`: only parts the document does
not describe changed.

| # | Document | Commit | Verdict | Reason |
| :--- | :--- | :--- | :--- | :--- |
| 1 | US-core-engineering-workflow-routing | `4a20b57` | noise | G3 exit changed to `approval-given` and `--given`, but the document does not describe the approval envelope and its scenario output still matches. |
| 2 | CAP-LIFE-core-engineering-workflow | `4a20b57` | updated-elsewhere | "G3 approval and integration results are recorded as files in `envelopes/`" became wrong with this commit and was fixed only six commits later, in the unrelated `bd5dbef` (a rule fix). |
| 3 | US-proposal-bundle-incubation-and-handoff | `ec22bb8` | noise | Handoff's frontmatter parser replaced (internal). The story's scenarios are unchanged. |
| 4 | CAP-LIFE-proposal-incubation-and-handoff | `ec22bb8` | noise | Same hunk; the document does not describe frontmatter parsing. |
| 5 | US-proposal-bundle-incubation-and-handoff | `40a71df` | noise | Pure move splitting `proposal.go` into three files; the bundle's reconcile recorded zero output difference. |
| 6 | CAP-LIFE-proposal-incubation-and-handoff | `40a71df` | noise | Same move; the document names no code paths. |
| 7 | CAP-LIFE-core-engineering-workflow | `40a71df` | noise | `command/workflow.go` split into a package; the document describes only `workflow next` behavior. |
| 8 | CAP-GOV-rule-verification-and-hygiene | `d83665b`, `a90c4b1` | noise | Envelope path exception added to `gates.go`. The document delegates that detail to CAP-LIFE-spec-reconciliation, which was updated in the same commit. |
| 9 | CAP-LIFE-spec-reconciliation | `a41566f` | updated-elsewhere | `sr-sync` changed the spec path format to `specs/{YYYY-MM}/{YYYYMMDD}-{slug}/`; the document's path statement was fixed the same day in another commit (`0e24e3d`). |
| 10 | CAP-GOV-rule-verification-and-hygiene | `a9fe516` | noise | One blank-import line in the generated `imports_gen.go`; the new rule got its own capability in the same commit. |

Verdicts: noise 8, updated-elsewhere 2, missed-update 0. Noise came from file moves and splits, internal helper swaps,
generated files and details delegated to other documents. Both needed updates were places where a document restated a
cross-cutting convention (the envelope set, the spec path format) in prose, and both were fixed late in other commits.
Verdict 2 is the kind of case such a check should have caught.

The sample is not random: for each top entrypoint the first unit by name was taken, and the 10 pairs cluster in 6
units (`40a71df` 3 pairs, `4a20b57` and `ec22bb8` 2 each). The verdict ratio shows a tendency in false-positive causes,
not an estimate over all false positives.

## Limits of Recall

- Missed documents concentrate in narrowly declared documents. CAP-HARN-skill-trio-and-playbooks was missed in 14
  units, the most: it changes when skill bodies (`template/agents/skills/`) change, but its `entrypoints` were two
  playbook paths. CAP-HARN-cache-and-derived-data follows (7 units).
- SPEC-entrypoint-derivation missed 21 of 23 actual updates because they were `entrypoints` backfills (metadata).
  Excluding metadata-only targets raises recall from 0.53 to 0.59.
- 93 actual targets were not changed in the unit's commits (`unobserved`). Counted per target entry, 64 paths did not
  exist at commit time (paths before a bulk identifier change, or documents created later) and 40 were updated in
  other commits. A per-commit check cannot see these by construction.

## Limitations

- In-sample measurement: the `entrypoints` were derived from these specs' records, and LOO drops only declarations with
  a single source, so circularity remains for declarations with two or more sources.
- "Actual" is the reconcile record. Omissions in it inflate false positives by as much; the judged sample gauges the
  size, but it is clustered.
- In the all-unit aggregate, targets of a spec in a joint unit are counted again in its single unit and other joint
  units (for example SPEC-friction-report-option belongs to three units). The single-unit aggregate has no duplicates,
  and both aggregates reach the same conclusion.
- One repository over a short period (2026-10-04 to 08). A commit that heavily restructured paths
  (SPEC-cli-command-layout) is part of the data.

## Recommendation

Reject the check of section 4 of `PROP-periodic-drift-reconciliation` (warning on entrypoint reverse-lookup candidates
per commit or spec), for three reasons. First, the baseline is precision 0.48, recall 0.54, and none of the five noise
filters tested raises precision above 0.5 while keeping recall at 0.5: the data gives no threshold. Second, eight of
ten judged false positives were noise. The sample is clustered and is no estimate, but applying that ratio to the 121
false positives and recounting updated-elsewhere as hits still gives precision of about 0.58: two candidates in five
only cost checking. Third, close to half of the actual updates are not candidates, and the cause is narrowly declared
documents (CAP-HARN-skill-trio-and-playbooks) and updates outside the commit, not a threshold. The two real missed
updates found in the sample were prose restatements of cross-cutting conventions (where the G3 approval is recorded,
the spec path format): semantic prose drift. Path lookup cannot tell it apart from other false positives, and neither
the path validity check of section 3.1 (the `envelopes/` path still existed) nor `RULE-cli-contract` (command citations
only) catches it. The reopen condition is a measurement with the same script on another repository giving LOO
precision of at least 0.6 together with recall of at least 0.5.
