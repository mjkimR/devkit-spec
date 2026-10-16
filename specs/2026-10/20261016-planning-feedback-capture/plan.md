---
id: PLAN-planning-feedback-capture
spec: SPEC-planning-feedback-capture
---

# Technical Plan: `SPEC-planning-feedback-capture`

## Constitution and invariants

`ADR-planning-feedback-in-proposal` authorizes storage and retirement. Preserve devkit public imports, error/output
contracts, preflight-before-write and rollback. No dependency or new CLI. Strategy prerequisite: workbench 72dd79d.

## Components and interfaces

1. Extend rules/id_convention.py path derivation/collection and rules/spec_format.py missing-ID derivation. Existing
   document index and namespace behavior should suffice; demonstrate with actual lookup/reference/namespace tests.
2. In proposals/handoff.py preflight direct feedback into open/settled routes using existing parsing and slug checks.
   Exclude open files from generic extras, include them in destination checks, the existing move transaction and
   exact/source relocation maps. Settled feedback remains generic extras under materials. Refuse feedback source
   symlinks/nested Markdown; preserve non-feedback sidecars normally. A focused proposals/feedback.py is allowed.
3. Add shared collect-feedback before direction-handoff; update location/sweep skills, direct Planning, worker and
   delegation contracts, and workflow signals. Update Host cleanup/decomposition procedures to preserve feedback
   and context before deletion without inventing a CLI or automatic disposition.

## Failure handling

Invalid status/frontmatter/identity, unreadable sources and unsafe/conflicting paths fail preflight. Existing
move_path/written/moved/leftovers machinery covers feedback including cross-device copying. Inject failure after a
feedback move and assert full restoration. Link rewriting keeps its existing best-effort notices after writes.

## Verification

AC-01: rule path/H1/autofix, lookup/refs/namespace tests. AC-02..04: mixed routing, links, open-only/no-materials,
empty bundles, invalid input, symlinks, collisions and rollback/cross-device coverage. AC-05/06/08: semantic review of
concrete source instructions for every executor and ending. AC-07: actual synced workflow evaluation for zero/failed/
policy-skip/off and unchanged person gates, shared-stage validation. Run just lint, just check, just test, just
rules-check, changed bundled rule tests and cumulative committed rules checks. Independent code/reconcile reviews.
