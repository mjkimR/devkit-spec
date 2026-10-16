---
id: PROP-hook-driven-integration-cleanup
title: Hook-driven integration and worktree cleanup
summary: "Investigate host hooks that turn one explicit integration approval, or delegated auto policy, into deterministic merge, branch cleanup and worktree removal without repeated agent approval prompts; implementation requires coordinated devkit and devkit-spec changes."
status: draft                         # draft | reviewing | accepted | rejected
created_at: 2026-10-16
target_area: capabilities/delivery/
priority: high                        # critical | high | medium | low
size: L                               # S | M | L | XL
planning_effort: high                 # low | medium | high (hint for Planning)
dev_effort: high                      # low | medium | high (hint for Development)
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

# [PROP-hook-driven-integration-cleanup] Hook-driven integration and worktree cleanup

## 1. Background & Hypothesis

The strategy layer's master flow (workbench `docs/strategy-layer/01-master-flow.md`, §10, hook-based local
integration) proposes deterministic local handoff, question display and status handling through host hooks such as
`UserPromptSubmit`, `PreToolUse` and `PostToolUse`. Their availability and execution contracts remain unverified.

Integration has a related operational problem: host permission checks can block worktree removal and branch cleanup,
and an agent may ask for explicit approval again after integration was already approved. The intended flow becomes
several manual steps even when the user wants the whole delivery finished. Existing worktree cleanup also needs
special handling after squash or rebase merges; an ancestor check alone cannot confirm those merges.

Hypothesis: a supported host hook can dispatch a deterministic integration operation using a scoped authorization
from the approval UI, or the effective `dev-integration=auto` policy. One approval should cover the displayed merge,
branch cleanup and worktree removal together. Under `auto`, the same operation should run without an approval prompt
once the path's completion conditions pass.

This is a research proposal, not a claim that hooks can run outside a host's permission boundary. Feasibility,
supported hosts and the approval UI integration must be established before choosing an implementation.

- **Related**: `PROP-worktree-host-compatibility` investigates access to worker worktrees; this proposal covers the
  integration and cleanup lifecycle after work is ready, including the base checkout and Git common directory.

## 2. Technical Spike Questions

- **Q1. Host support and execution authority.** For Claude Code, Codex and Antigravity, which documented hooks and
  approval UI callbacks are available? Can they invoke a configured integration command without another agent turn?
  Which sandbox, filesystem, command approval and Git permissions apply to that command? Reproduce the current
  denial and repeated approval cases, then test whether a supported configuration resolves them. Do not assume a
  hook bypasses permission checks or that hosts share hook names and output formats.
- **Q2. One approval, one scope.** How does an approval button bind the repository, Unit or session task, source
  branch and head SHA, target branch, merge method and cleanup targets? How is that authority passed to the executor
  without asking again for the same operations? Distinguish a workflow approval from host execution permission;
  identify any unavoidable host prompt and the configuration needed before execution can be seamless.
- **Q3. Auto dispatch.** Which event reliably triggers completion under `dev-integration=auto`, and how does the
  executor verify policy delegation and the applicable review, checks and reconcile conditions? Session tasks have
  no Unit or envelope and need their own evidence path. Policy delegation must remain distinguishable from a human
  approval; `auto` for worktree or PR usage does not authorize integration.
- **Q4. Local and PR merge.** Can existing worktree commands supply the operation, or is a new public devkit contract
  needed? How are PR-required policy, remote merge confirmation, squash/rebase merge evidence, local base updates,
  and local versus remote branch deletion handled? Which remote operations are included in the displayed approval?
- **Q5. Failure and retry.** How are duplicate hook events, concurrent attempts, head/base changes and a host exit
  handled? If merge succeeds but push or cleanup fails, can execution resume from the recorded result without
  merging twice or requesting the original approval again? What changes actually invalidate that approval?
- **Q6. Installation and trust.** Does devkit own hook projection and configuration, or integrate with a separately
  installed runner? How are configured commands, inputs and executable versions validated, installed, inspected and
  removed without overwriting user hooks? Record unsupported hosts explicitly and retain a documented manual path.

## 3. Proposed Design & Impact

Working direction to validate in Planning:

1. Prepare an integration request with its exact targets, completion evidence and cleanup scope. With `ask`, the
   approval UI shows the complete operation and one explicit approval dispatches it. With `auto`, verified policy
   delegation dispatches the same operation without a person clicking approval.
2. A host adapter or hook passes that request to a deterministic executor. The executor validates authority and
   current state, merges through the allowed local or PR path, confirms the merge and removes the task's worktree
   and eligible branches. It runs the existing post-finish cleanup for scope records and proposal remnants.
3. Return structured results for merge, push, branch deletion, worktree removal and post-finish cleanup separately.
   Preserve partial progress so another event or explicit retry continues pending steps. A denied host permission
   remains a visible blocked result with a supported remedy, not a false completion.

**Coordinated devkit changes are required.** Editing devkit-spec skills alone cannot deliver this behavior.

| Owner | Expected changes to investigate |
| :--- | :--- |
| `devkit` | SDD-independent execution and authorization contract; worktree finish and merge evidence; concurrency, retry and partial results; host hook installation/projection where appropriate; public CLI/API and tests |
| `devkit-spec` | SDD completion conditions and policy mapping; approval scope; integration skills and workflow guidance; scope/proposal post-finish behavior; Living Spec and tests |
| Host / approval UI | Supported approval callback and hook configuration, execution permissions and capability reporting; owner and availability to be established by the spike |

Implement and release the devkit public contract first, then update devkit-spec's dependency/lock and consumer
guidance together. Validate the installed pair and host projections; a local sibling edit alone is insufficient.
If the design changes the strategy layer's approval or integration contract, update its master flow and policy
documents before implementing the consuming package. Cloud/autohub integration is a separate follow-up if needed.

### 3.1 Non-Goals

- **Scope Excluded**: bypassing host permission enforcement, disabling guards, force-cleaning dirty or locked
  worktrees, or deleting branches outside the integration request.
- **Scope Excluded**: weakening required PR, review, test or blocked/question checks, or delegating `plan-intent`
  and `plan-accept` to `auto`.
- **Scope Excluded**: implementing general local orchestration, worker worktree access or an autohub approval UI.

## 4. Lifecycle & Retirement Criteria

- **Planning entry**: reproduce the reported host failures, research primary host documentation and collect actual
  hook execution results in `materials/`. Compare supported hook execution with other supported runners if a hook
  cannot deliver the requested behavior. Resolve Q1–Q6 before claiming feasibility or accepting a design.
- **Expected acceptance checks**: on every declared supported host, one `ask` approval completes merge, eligible
  branch deletion, worktree removal and post-finish cleanup with no repeated approval for the same scope; `auto`
  completes the same sequence without an approval prompt after its conditions pass. Cover local and PR paths,
  including squash/rebase cleanup where supported.
- **Recovery checks**: duplicate events do not repeat completed mutations; changed heads invalidate stale requests;
  dirty/locked or unrelated worktrees are preserved; denied permissions and failures after merge report partial
  progress and resume pending steps. Verify the coordinated devkit/devkit-spec installation and document remaining
  host limitations.
- On acceptance (`plan-accept`): record `gate:plan-accept`, set `status: accepted` and merge the Planning branch;
  Development starts with `devkit spec proposal handoff hook-driven-integration-cleanup` and coordinated devkit work.
- On rejection: change only `status: rejected`, with the user's reason in the commit message; a later hygiene pass
  writes the rejection ADR and deletes the proposal directory.
