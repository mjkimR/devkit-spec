---
id: ARCH-06-runtime-view
title: Runtime View
summary: Key runtime sequences of devkit-spec with devkit, namely starting a spec bundle and following its workflow, incubating and handing off a proposal, the commit gate running the spec rules on a staged snapshot, and the worktree lifecycle with scope registration, sweep and prune.
status: active
created_at: 2026-10-13
---

# [ARCH-06-runtime-view] Runtime View

- **arc42**: §6 Runtime View
- Components named here: `ARCH-05-2-components`. Contracts of each command: the capabilities linked per scenario.

---

## 1. Overview

devkit-spec has no long-running process. Every scenario is a sequence of short `devkit` invocations made by the
agent (or by Git hooks and CI), each reading the files afresh. State lives in files: the Living Spec and bundles in
the working tree, workflow bindings and decision records in the unit (devkit's), and the scope registry in the Git
common directory.

---

## 2. Scenario 1: `spec` depth, from inline Planning to the first stage

The agent classifies an intent with the `spec` skill, creates a spec bundle in inline Planning and lets devkit's
workflow engine name the next step (`CAP-DLV-spec-bundles`, `CAP-DLV-delivery-workflows`, `CAP-DLV-project-policy`).

```mermaid
sequenceDiagram
    autonumber
    actor Agent as AI coding agent
    participant DK as devkit CLI
    participant Spec as devkit spec (cli)
    participant Lib as devkit_spec.proposals
    participant WF as devkit.workflow
    participant FS as Working tree

    Agent->>DK: devkit get-context spec
    DK-->>Agent: constitution + instruction read conditions
    Agent->>DK: devkit spec policy
    DK->>Spec: lazy import devkit_spec.cli
    Spec-->>Agent: [GATE_POLICY ...] [STAGE_POLICY ...] [GIT_POLICY ...] [ROUTING_POLICY ...]
    Agent->>DK: devkit spec new <slug> [--workflow sdd-spec-bugfix]
    DK->>Spec: new
    Spec->>Lib: create_spec
    Lib->>WF: resolve and validate workflow (Workspace)
    Lib->>FS: write spec.md (+ plan.md, tasks.md unless sdd-spec-bugfix), skeleton-marked, spec.md bound
    Spec-->>Agent: [SPEC: SPEC-<slug> path= workflow=] [NEXT_CMD: devkit workflow next --unit <dir>]
    Agent->>DK: devkit workflow next --unit <dir>
    DK-->>Agent: current stage, unmet checks, [WAITING: human gate:plan-intent] or [NEXT_SKILL: ...]
```

- A missing default workflow leaves `spec.md` unbound with a `SPEC_UNBOUND` notice; an explicit workflow that does not
  resolve fails before anything is written (`SPEC_WORKFLOW_INVALID`).
- The agent records the user's explicit `plan-intent` with `devkit workflow answer --unit <dir> --request
  gate:plan-intent --action accept --by user` and commits: that state is Development's input. Under `ask` it asserts a
  `dev-integration` OK with `--given dev-integration` on each later `next`, writing nothing
  (`ADR-integration-approval-asserted`); under `auto` the gate passes by policy (`source=policy`).

---

## 3. Scenario 2: Proposal incubation and handoff

`proposal`-depth work starts as a draft proposal bound to `sdd-proposal`, is planned on its `plan-<slug>` branch and
becomes a spec bundle at the start of Development once the user accepted it (`CAP-DLV-proposal-incubation`,
`ADR-task-kind-and-planning-depth`).

```mermaid
sequenceDiagram
    autonumber
    actor Agent as AI coding agent
    actor User as Developer
    participant Spec as devkit spec proposal
    participant WF as devkit workflow
    participant FS as Working tree
    participant Reg as Scope registry

    Agent->>Spec: proposal new <slug> [--task-kind bugfix] [--summary ...]
    Spec->>FS: docs/proposals/PROP-<slug>/ (proposal.md bound to sdd-proposal)
    Spec-->>Agent: [PROPOSAL: ...] [NEXT_CMD: devkit workflow next --unit <dir>]
    User-->>Agent: confirms the draft
    Agent->>WF: workflow answer --request gate:plan-intent --action accept --by user
    Agent->>Spec: proposal padr <slug> <title> (Planning, on plan-<slug>)
    Agent->>FS: record observed proposal feedback before last work commit
    Agent->>WF: collect-feedback sweep, fresh feedback envelope before each Planning return
    Agent->>WF: workflow next --unit docs/proposals/PROP-<slug>
    WF-->>Agent: [WAITING: human gate:plan-accept]
    User-->>Agent: accepts the direction
    Agent->>WF: workflow answer --request gate:plan-accept --action accept --by user (+ status: accepted)
    Agent->>Spec: proposal handoff <slug> (Development, on dev-<slug>)
    Spec->>Spec: validate slug, approval, needs_decompose, namespace, summary, task_kind, binding, every target path
    Spec->>FS: write specs/<YYYY-MM>/<YYYYMMDD>-<slug>/, bind sdd-spec-<task_kind>
    Spec->>FS: copy target-docs.md, promote PADRs to ADRs
    Spec->>FS: move open feedback into spec, settled feedback and materials into docs/materials
    Spec->>FS: rewrite links and ID references, remove the proposal and its gate records
    opt the proposal recorded plan-intent and plan-accept
        Spec->>WF: carry gate:plan-intent and gate:plan-accept to the spec under the same names
    end
    opt linked worktree
        Spec->>Reg: register the bundle's scope
    end
    Spec-->>Agent: [HANDOFF ...] [PROMOTED_ADR ...] [REWRITTEN ...] [SCOPE ...] [NEXT_CMD ...]
```

- Handoff refuses without `status: accepted` (`SPEC_PROPOSAL_NOT_APPROVED`) and a proposal marked
  `needs_decompose: true` (`SPEC_PROPOSAL_NEEDS_DECOMPOSE`).
- The proposal unit's gate records and envelopes are dropped with it; its `plan-intent` and `plan-accept` records are
  carried to the spec under the same names (`[CARRIED_GATE]`), and a failure there is a
  `SPEC_PROPOSAL_GATE_NOT_CARRIED` warning that leaves the handoff done.
- A failure while writing the bundle, ADRs, feedback or materials removes what was written, restores moved feedback
  and keeps the proposal
  (`SPEC_PROPOSAL_HANDOFF_FAILED`); a failed scope registration is a `SPEC_SCOPE_REGISTER_FAILED` warning and the
  handoff stays done.
- devkit's own `devkit workflow handoff` is not used: it rebinds a unit in place and cannot move a proposal bundle
  into the spec layout.

---

## 4. Scenario 3: Commit gate running the spec rules on a snapshot

The commit gate and CI judge exactly what is committed (`CAP-GOV-spec-rules`, `ADR-rules-implemented-in-the-package`).

```mermaid
sequenceDiagram
    autonumber
    actor Agent as AI coding agent
    participant Git
    participant Gate as devkit gate (pre-commit)
    participant Rules as devkit rules
    participant RuleFile as .devkit/managed/spec/rules/<name>/rule.py
    participant Impl as devkit_spec.rules
    participant Index as DocumentIndex

    Agent->>Git: git commit
    Git->>Gate: pre-commit hook
    Gate->>Rules: rules-check: staged snapshot, run_project_rules (in the hook's process)
    Rules->>Rules: evaluate in place when the working tree holds the staged tree, else materialize it; read config, receipt and rule files from it
    Rules->>RuleFile: load rule classes
    RuleFile->>Impl: subclass of the package's rule
    Rules->>Impl: check(ctx) per targeted file (changed files of the diff)
    Impl->>Index: document_index(ctx) through ctx.cache (the snapshot)
    Impl->>Impl: ctx.snapshot: changed and deleted paths, base, mode
    Impl-->>Rules: violations on targeted files
    Rules-->>Gate: blocking violations
    Gate-->>Git: refuse the commit (GATE_RULES_FAILED) or let it pass
```

- `RULE-reconcile-contract` requires every `modified` target of a resolved `reconcile.md` changed in the snapshot's
  diff; `RULE-code-entrypoints` also reports current documents declaring a path the diff deletes.
- `devkit rules check --ci --base <ref>` runs the same evaluation on merge-base through HEAD in CI.
- A malformed `[tool.spec]` table fails the run (`SPEC_CONFIG_INVALID`, which devkit keeps with the rule's ID,
  exit `2`) instead of being reported as a violation.

---

## 5. Scenario 4: Worktree lifecycle with the scope registry

In `direct` mode under `[tool.spec] worktree = "required"` every `spec` and `proposal` activity runs in its own
worktree, and under `"auto"` the activities that need one do (`local-orchestrated` always uses one); the skills keep the
registry current, and devkit-spec's `devkit.post_finish` extension cleans up after a successful finish
(`CAP-COLL-work-scope-registry`, `ADR-cleanup-after-worktree-finish`).

```mermaid
sequenceDiagram
    autonumber
    actor Agent as AI coding agent
    participant WT as devkit worktree
    participant Spec as devkit spec
    participant Reg as Registry (<git-common-dir>/devkit-spec-scope/)

    Agent->>WT: worktree start dev-<slug> (in the base)
    WT-->>Agent: [NEXT_CMD: cd <base>-wt-dev-<slug>] (setup + devkit sync ran there)
    Agent->>Spec: spec new <slug> (spec depth) or proposal handoff <slug> (proposal depth)
    Agent->>Spec: scope register --spec <dir> (handoff registers itself)
    Spec->>Reg: record + owner token (token saved in the worktree's git dir)
    loop spec-tasks writes tasks.md, spec-sync writes reconcile.md
        Agent->>Spec: scope update --spec <dir>
        Spec->>Reg: compare revision, write record, append journal
        Spec-->>Agent: pairs + [SCOPE_ACK: status=applied overlaps=...]
    end
    Note over Agent: dev-integration approval
    Agent->>WT: worktree finish dev-<slug> [--merge] (in the base)
    WT-->>Agent: [WORKTREE_FINISHED: ...] or a refusal, e.g. WORKTREE_BLOCKED (task stays registered, no extension)
    WT->>Spec: post-finish extension (devkit.post_finish)
    Spec->>Reg: remove the finished worktree's records (revision unchanged)
    Spec-->>Agent: [NOTICE] removed scope record / empty proposal directory
```

- `overlaps=` above 0 informs scheduling and integration order; it never blocks work.
- An update that does not apply prints `[SCOPE_ACK: status=failed|stale|timeout ...]` and its error
  (`SPEC_SCOPE_STALE_REVISION`, `SPEC_SCOPE_TIMEOUT`, ...); `--request-id` makes a retry idempotent.
- `devkit spec scope release -w <worktree>` withdraws an abandoned task instead of the sweep.
- The extension's two cleanups are independent: a failed proposal prune arrives as a `SPEC_PROPOSAL_CLEANUP_FAILED`
  warning (fix: `devkit spec proposal prune <slug>`) and the record removal still runs; a failed record removal
  arrives as its own warning (`SPEC_SCOPE_TIMEOUT`, `SPEC_CONFIG_INVALID`, ...) whose fix ends with
  `devkit spec scope sweep --apply`. The finish itself has already succeeded.

---

## 6. Concurrency and Delivery Guarantees

1. **Registry operations** hold an exclusive `flock` on `<shared>/<namespace>/.lock` for read, compare and write
   (devkit's `file_lock`), and publish a record by atomic rename (`atomic_write_text`); updates use optimistic
   revisions (`SPEC_SCOPE_STALE_REVISION`).
2. **Writers validate first**: `spec new` and `proposal handoff` check every input and target path before the first
   write and undo their writes on a file system failure; `entrypoints derive --apply` changes only the `entrypoints`
   block of each document and reports a document it cannot write (`SPEC_ENTRYPOINTS_APPLY_FAILED`) while writing the
   others.
3. **No shared mutable state between commands** other than the registry: the document index is rebuilt per load, and
   devkit owns the unit's binding and decision records.
