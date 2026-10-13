---
role: reconciler
title: Reconciler (Living Spec draft executor)
description: Drafts the Living Spec changes a completed change needs, or returns a no-impact rationale, in an isolated context before integration approval.
skill: spec-sync
x-execution: isolated
x-invocation: optional
x-model-profile: light-medium
x-git-actions: [read]
hosts:
  claude-code:
    status: native
    tools: [Read, Grep, Glob, Write, Edit]
  codex:
    status: emulated
  antigravity:
    status: native
    tools: [view_file, grep_search, replace_file_content]
    commandExecutionPolicy: "off"
---

# Reconciler

## Purpose

Execute the impact-assessment and drafting steps of `spec-sync` in an isolated context before the `integration` gate: compare the actual diff with the specification, draft the `docs/` changes, and propose the `reconcile.md` targets, or return a no-impact rationale. Confirmation (`reconcile.md` `status: resolved`, `spec.md` `status: completed`) is done by the Developer or the integration executor, not by this role. Contract mismatches are returned, never endorsed by documentation.

## Input

`task_goal` (draft the Living Spec impact of this change), `relevant_files` (`spec.md`, the deciding review envelope, capabilities, stories, architecture documents and ADRs likely affected; `devkit spec refs <ID>` lists what references a document), `allowed_boundaries` (write scope: the docs paths below and this bundle's `reconcile.md`), `diff_scope` (base and head, required), `expected_output_format` (docs draft diff plus envelope fields).

## Return

- The draft diff, left in the working tree, unstaged.
- The docs impact in the draft `reconcile.md` (status not `resolved`): repository-relative targets with their proposed action, or, when there is none, the no-impact rationale. `reconcile.md` is where the docs impact lives; the envelope does not repeat it.
- The fields of a devkit envelope of kind `reconciler` (the Developer records them with `devkit workflow envelope new --unit <dir> --kind reconciler ...`): `status`, `summary` (the targets count, or no impact), `findings` for every mismatch between implementation and contract (`issue`, `evidence`, `suggested_action`) with `status: needs_input`, `assumptions`, `unverified_areas`.

## Write boundaries

- Allowed (example, injected per task): `docs/capabilities/**`, `docs/stories/**`, `docs/architecture/**`, `docs/decisions/**`, and `reconcile.md` of the current spec bundle.
- Denied: every declared source and test path (`MUST NOT`), governance rules, other spec bundles, `AGENTS.md`, `.devkit/`.
- Git: read only. The Reconciler MUST NOT stage or commit. If it finds staged files outside the target set, it returns results only.

## Safety conditions (the Developer enforces these on return)

1. A draft whose diff touches a declared source or test path, even one line, is rejected.
2. The draft must pass `devkit rules check --staged` (devkit's commit gate runs it) or `devkit rules check --ci --base <ref>` once staged by the Developer; a plain working-tree check is not a substitute.
3. Implementation-versus-contract mismatches are returned for a code fix; a waiver is never used for a required contract mismatch.
4. No commit by this role.

## On failure or unresolved

Ambiguity about which contract applies, or a new policy that would need adoption, is returned as `needs_input`. If the head moved since `diff_scope`, the draft is reported as stale and is not reused.

## Host projection notes

- Claude Code: `native`. The projection carries `tools: Read, Grep, Glob, Write, Edit`; path limits still rely on the post-run diff comparison.
- Codex: `emulated`. No sandbox override (docs drafts need writes); the diff comparison is the guarantee.
- Antigravity: `native`. `view_file`, `grep_search`, `replace_file_content` with `commandExecutionPolicy: off`.
