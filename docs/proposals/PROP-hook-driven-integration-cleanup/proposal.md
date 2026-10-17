---
id: PROP-hook-driven-integration-cleanup
title: Approval-driven integration and worktree cleanup
summary: "Deliver Codex native approval followed by deterministic local integration and worktree cleanup, with scoped authorization and actionable partial results for main-agent recovery; host permission ergonomics and broader merge paths follow the first implementation."
status: accepted                      # draft | reviewing | accepted | rejected
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

# [PROP-hook-driven-integration-cleanup] Approval-driven integration and worktree cleanup

## 1. Background & Hypothesis

The strategy layer's master flow (workbench `docs/strategy-layer/01-master-flow.md`, §10, hook-based local
integration) proposes deterministic local handoff, question display and status handling through host hooks.
Codex CLI supports a native MCP confirmation form, and an interactive dry run has exercised affirmative approval
and a non-approval submission. Lifecycle hook logs also show session, prompt, tool and stop events. Evidence and
its limits are recorded in [Codex spike evidence](materials/codex-spike-evidence.md).

Integration has an operational problem: an agent may ask for the same business approval again after integration
was approved, while host permission checks can independently block merge or cleanup. The working direction is to
bind one native confirmation to an exact integration request and run a deterministic executor directly from the
confirmed tool call. Hooks remain useful for observation and later dispatch, but are not a prerequisite for the
first interactive path. The dry run establishes UI and result transport, not real Git execution authority.

The first implementation targets Codex CLI, explicit approval (`dev-integration=ask`), local fast-forward merge,
eligible local branch deletion, worktree removal and existing post-finish cleanup. It excludes network operations.
Host permission prompts may still occur: report them and expose partial progress, then refine supported permission
configuration after exercising real operations. Completion does not require eliminating all host prompts.

- **Related**: `PROP-worktree-host-compatibility` investigates access to worker worktrees; this proposal covers the
  integration and cleanup lifecycle after work is ready, including the base checkout and Git common directory.

## 2. Planning Questions & Findings

- **Q1. Host support and execution authority.** Codex CLI 0.163.0 exposed the native MCP form and returned both
  approved and unapproved dry-run results. Metadata logs contain `SessionStart`, `UserPromptSubmit`, `PreToolUse`,
  `PostToolUse` and `Stop`; there is no `PermissionRequest` evidence. Actual Git permission behavior remains a
  Development validation item. Claude Code and Antigravity are outside the first supported-host claim.
- **Q2. One approval, one scope.** Before acceptance, settle the authority boundary: prepare a request binding the
  repository and Git common directory, Unit or session task, source branch and SHA, target branch and expected SHA,
  merge method, exact cleanup targets, completion evidence and an explicit no-network policy. The executor accepts
  approval only from its trusted confirmation callback for that request, never a model-supplied approval boolean.
  Non-approval, decline, cancellation and UI/transport failure perform no integration mutations.
- **Q3. Dispatch and readiness.** The first path is one model-initiated MCP tool call whose confirmation callback
  continues into execution without another model decision. The devkit-owned adapter invokes a devkit-spec readiness
  provider for SDD policy and applicable review, checks, reconcile and blocked/question conditions before showing
  the request and again before execution. Generic policy evaluation and workflow execution remain in devkit;
  devkit-spec supplies only SDD-specific definitions and evidence interpretation.
  A session task needs its own evidence contract; a Unit envelope is not invented for it. Automatic policy dispatch
  and selection of its hook trigger are deferred; `auto` for worktree or PR usage never authorizes integration.
- **Q4. Local merge and remote effects.** The existing public `devkit.worktree.finish` contract fast-forwards and
  pushes the base upstream when `merge=True`; the first executor cannot blindly call it while promising local-only
  behavior. Before acceptance, choose a public devkit extension that explicitly excludes network operations while
  retaining guards, local branch policy and post-finish extensions. Do not remove upstream configuration or copy
  private helpers as a workaround. Required-PR policy blocks the local path. PR merge, push, remote deletion and
  squash/rebase merge evidence remain follow-up scope.
- **Q5. Failure and main-agent recovery.** The first path runs under the main agent, which interprets devkit's
  structured partial results and detailed advisory directives, inspects Git state and performs the supported
  corrective action. Reuse existing worktree error/result contracts rather than introducing a durable retry
  journal or automatic recovery runner. Before acceptance, settle what each step reports and when changed targets
  invalidate authorization. Validate source, target and cleanup identities before mutations; the agent must not
  broaden cleanup or repeat an already completed merge blindly. A confirmed merge followed by failed cleanup is
  partial progress, not a failed merge. Changed scope needs fresh approval; execution-permission failure alone
  does not change the approved scope. Ambiguous state requires inspection, not an assumed successful retry.
- **Q6. Installation and trust.** devkit owns the host hook infrastructure, MCP adapter, native confirmation transport
  and public executor. devkit-spec consumes public extension points; it does not install a second host adapter or
  duplicate hook infrastructure. Before acceptance, define the provider contract and a minimal inspectable
  setup/removal path that preserves existing configuration. Project trust,
  hook trust, integration approval and host execution permissions are separate. Initial manual configuration is
  acceptable; automatic hook projection, other hosts and permission-prompt reduction are follow-up work.

## 3. Proposed Design & Impact

Working direction for the first implementation:

1. The devkit-owned MCP adapter prepares an immutable local integration request, obtaining SDD-specific completion
   evidence from a devkit-spec provider through a public extension point. devkit owns the generic request schema,
   target discovery and policy mechanics. Show repository, task, source/target SHAs, fast-forward merge, local
   cleanup targets and excluded network effects in the Codex native MCP confirmation form. Bind an affirmative
   response to that request inside the devkit adapter.
2. A public devkit executor validates the request and its authority, rechecks state and provider-supplied readiness,
   and merges locally. It runs from the retained base checkout or an installed runtime,
   not the worktree being removed. It removes only the requested eligible worktree and local branch, respecting
   `delete_branch=no`, dirty/locked state and protected/base branches. It runs devkit-spec's post-finish extensions
   for scope records and empty proposal remnants. No integration mutations occur for a non-approved request.
3. Return structured per-step results for merge, branch deletion, worktree removal and post-finish cleanup, with
   network operations explicitly excluded. Use devkit's normal output/advisory contract for the CLI and structured
   MCP results for the adapter. On failure, identify completed steps, the failing operation, observed Git state
   and a concrete next action through the existing advisory protocol. The main agent handles inspection and
   corrective commands; no background retry, durable execution journal or automatic restart recovery is required.
4. Treat denied host permissions as blocked or partial results with a supported remedy. A workflow approval does
   not bypass the host boundary. Count business approvals, setup/trust prompts and execution-permission prompts
   separately during real-operation validation; a dry run cannot establish their counts for real mutations.

**Coordinated devkit changes are required.** Editing devkit-spec skills alone cannot deliver this behavior.

| Owner | First implementation responsibility |
| :--- | :--- |
| `devkit` | Host hook infrastructure and lifecycle, MCP adaptation, native confirmation and trusted callback binding, generic request/execution and policy mechanics, explicit local-only behavior, ref and cleanup validation, structured partial results and actionable advisories; public CLI/API, setup/inspection/removal and tests |
| `devkit-spec` | Consumer/provider integration through public devkit extension points: SDD policy definitions and completion evidence, review/reconcile/blocked-question interpretation, Unit/session-specific evidence, integration guidance, existing scope/proposal post-finish behavior and consumer tests |
| Host configuration | Supported execution permissions and capability reporting; no promise that workflow approval removes host prompts |

The devkit request and transport contracts must work without devkit-spec installed: another methodology can supply
its own readiness provider. devkit must not import SDD document models, capability/story identifiers or proposal
rules. devkit-spec must not reimplement the host/MCP bridge, approval UI plumbing or Git executor.
Reuse existing `devkit.finish_guard` and `devkit.post_finish` extension points where they fit; add only the public
provider contract the approved flow needs. The first release needs the Codex adapter and minimum hook support
required by this path, not an unrelated general orchestration framework.

Implement and release the devkit public contract first, then update devkit-spec's dependency/lock and consumer
guidance together. Validate the installed pair and Codex adapter; a local sibling edit alone is insufficient.
If the design changes the strategy layer's approval or integration contract, update its master flow and policy
documents before implementing the consuming package.

### 3.1 Non-Goals & Follow-up Scope

- **Scope Excluded**: bypassing host permission enforcement, disabling guards, force-cleaning dirty or locked
  worktrees, or deleting branches outside the integration request.
- **Scope Excluded**: weakening required PR, review, test or blocked/question checks, or delegating `plan-intent`
  and `plan-accept` to `auto`.
- **Scope Excluded**: implementing general local orchestration, worker worktree access, a custom approval UI or
  cloud/autohub integration.
- **Scope Excluded**: a durable execution journal, autonomous recovery runner, exactly-once execution framework or
  cross-session automatic resumption. The initial main-agent path uses existing Git checks, partial results and
  advisory directives. Reconsider only if unattended execution becomes required or observed failures show these
  contracts cannot support reliable agent-directed recovery.
- **Follow-up retained here**: `dev-integration=auto` dispatch after readiness/policy delegation is verified;
  implementation depends on the shared request/executor contract and requires separate policy-source evidence.
- **Follow-up retained here**: PR/remote operations and squash/rebase cleanup after remote authority and merge
  evidence are defined; required-PR workflows retain their existing path in the meantime.
- **Follow-up retained here**: other host adapters, automatic installation/projection and permission ergonomics
  after actual-operation evidence identifies the needed supported configurations. Preserve a manual path.

These follow-ups are not first-release acceptance conditions. Before handoff removes this proposal, transfer each
retained item into a tracked feedback or proposal with its dependencies and verification scope.

## 4. Lifecycle & Retirement Criteria

- **Planning entry**: use the persisted Codex UI and hook evidence; no empty production project or exhaustive
  cross-host spike is required. Review the coordinated public contract and package ownership before implementation.
- **Before `plan-accept`**: with host/MCP/executor ownership assigned to devkit, settle its public readiness-provider
  and installation contracts, the trusted approval-to-request boundary, explicit local-only devkit operation,
  Unit/session readiness evidence, stale-request rules and actionable partial-result semantics
  (Q2–Q6). Confirm the release order and any strategy-layer contract changes. These are design decisions;
  real-mutation permission behavior and prompt reduction do not block acceptance of this bounded direction.
- **Development acceptance checks**: in an isolated clone or disposable Git fixture on Codex CLI, one affirmative
  business approval executes the approved fast-forward merge, eligible local cleanup and post-finish extensions;
  non-approval/decline/cancel executes none. No push, fetch, remote deletion or PR operation occurs. Report any host
  permission prompts separately and never repeat the business approval for an unchanged request solely because a
  later step needs execution permission. Verify required-PR and `delete_branch=no` policy behavior.
- **Failure checks**: changed source/target identities before merge invalidate stale requests; dirty/locked or
  unrelated worktrees are preserved. An ordinary merge or cleanup failure, including permission denial, returns
  completed-step results and a concrete advisory action so the main agent can inspect and recover. Exercise a
  failure after merge and verify the agent can finish cleanup through supported commands without merging again
  or expanding the approved scope. After process termination, inspect Git state before further mutations; no
  automatic resumption guarantee is made. Verify the installed devkit/devkit-spec/adapter set.
- **Evidence boundary**: passing the UI spike is not evidence of successful merge, cleanup, permission handling,
  automatic dispatch or retry. Do not claim the first implementation supports deferred hosts or merge paths.
- On acceptance (`plan-accept`): record `gate:plan-accept`, set `status: accepted` and merge the Planning branch;
  devkit implements its owned scope directly from this accepted proposal under its repository workflow; no devkit
  spec bundle or devkit-spec handoff is required for that work. Retain this proposal and its evidence as the
  development reference. Any later devkit-spec consumer changes follow this repository's own delivery workflow.
- On rejection: change only `status: rejected`, with the user's reason in the commit message; a later hygiene pass
  writes the rejection ADR and deletes the proposal directory.
