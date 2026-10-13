---
name: sr-delegate
description: Delegate a bounded task to an optional isolated support role (Scout, Challenger, Reviewer, Reconciler) with an explicit input payload, verify the returned envelope, and compare the actual diff with the injected write boundary.
---

# sr-delegate: Support Role Invocation Workflow

Use this skill when the main Developer session wants to hand exploration, criticism, an independent review, or a Living Spec draft to an isolated context. Delegation is optional and chosen by uncertainty, risk, change size, or the user's request. The role's result is an opinion with evidence; completion still rests on agreed AC, relevant checks, the final diff, and reconciliation.

---

## 1. Inputs

- Role contract: `challenger`, `reconciler`, `reviewer` or `scout`, shipped with the `spec` bundle. `devkit workflow next --unit <dir>` prints `[DELEGATE: role=<role> isolation=<level> contract=<path>]` for a stage that prefers isolation; `contract=` is the effective contract (managed or overridden). Outside a delegating stage, the managed contract is `.devkit/managed/spec/subagents/<role>.md`.
- Stage context: `devkit workflow next --unit <dir>` (which stage you are in) and `devkit workflow show --unit <dir>` (where returns go).
- Payload and return fields: the contract's **Input** and **Return** sections; envelope files are written with `devkit workflow envelope new` (Step 6).

---

## 2. Invariants

1. **Read the contract first (`MUST`)**: the role's `x-git-actions`, write boundaries, and `hosts.<host>.status` for the current host decide how you call it.
2. **No whole-tree injection (`MUST NOT`)**: pass `relevant_files`, not the repository.
3. **Boundaries are per task (`MUST`)**: inject the repository's actual declared paths into `allowed_boundaries`; contract paths are examples.
4. **Guarantee comes from the host and the diff (`MUST`)**: prompt limits are guidance. If the host status is `emulated` or `unverified`, say so in the call and rely on the post-run diff comparison. `unsupported` (no projected file) means run the procedure in the main session and say so.
5. **Support roles never touch index or HEAD (`MUST NOT`)**.
6. **Zero findings is a valid result (`MUST`)**: never ask a role to produce a minimum number of objections.

---

## 3. Procedure

### Step 1: Decide whether to delegate
- Route 1: do not delegate. Route 2: Reviewer and Reconciler only when risk or the user asks. Route 3/4: Scout and Challenger for spikes; Reviewer and Reconciler as in Route 2.
- Skip delegation when the answer is one file lookup or the change is trivial; delegation cost (payload, re-exploration, coordination) counts.

### Step 2: Build the input payload
Fill all five fields of the contract's Input: `task_goal`, `relevant_files`, `allowed_boundaries` (read scope, write scope, denied paths), `diff_scope` (base and head; required for Reviewer and Reconciler), `expected_output_format`. Record the head SHA you passed (`git rev-parse HEAD`).

### Step 3: Invoke in isolation
- Read the stage's `isolation` from `[DELEGATE: role=<role> isolation=none|preferred|required contract=<path>]` and the role's `hosts.<host>.status` for the current host. Decide and state one of: spawn an isolated subagent (`native`, `emulated` or `unverified`), run the procedure in the main session as a substitute (`unsupported`, or `preferred` when a fresh context is not available), or stop with `needs_input` (`required` and `unsupported`). Record the choice and the projection status in the envelope's `assumptions`.
- Use the host's isolated-context mechanism. `devkit sync` renders each contract into the selected agents' native agent directories; if one is missing or stale, `devkit status` reports it and `devkit sync` restores it before delegating.
  - Claude Code: the subagent named `<role>` from `.claude/agents/<role>.md` (Agent tool or `@agent-<role>`).
  - Codex CLI: `collaboration.spawn_agent` with `agent_type: <role>` from `.codex/agents/<role>.toml`. The role appears only when the project root is registered as trusted in `~/.codex/config.toml` (`[projects."<absolute git root>"] trust_level = "trusted"`); without it the spawn tool has no `agent_type` and a plain spawn carries no role instructions, so stop and ask the user to register the root.
  - Antigravity: `invoke_subagent` with the role name from `.agents/agents/<role>.md`.
  - Do not fork the main context when a fresh context is what isolates the result.
- Pass the role contract body and the payload; do not pass the main session's narrative. Ask the role to return the envelope fields (as YAML, findings as a list) and its summary.

### Step 4: Validate the returned fields
- Required fields present; `status` is one of `completed | needs_input | failed`.
- Reviewer and Challenger findings each have `evidence` and `failure_condition`.
- `failed` or stale `diff_scope` (head moved) is not completion evidence. Decide re-invocation from the failure reason and changed input only.

### Step 5: Compare the actual diff with the boundary
```bash
git status --short
git diff --name-only            # unstaged
git diff --name-only --cached   # staged (should be unchanged by the role)
```
- Scout, Challenger, Reviewer: expected diff is empty (Scout may add only to the agreed `materials/` path).
- Reconciler: every changed path must be inside the injected docs scope and this spec's `reconcile.md`. One line in a declared source or test path rejects the whole draft.
- Any path outside `allowed_boundaries`, or any change to the index or HEAD, is a boundary violation: report the paths, discard or revert the out-of-scope change, and do not reuse earlier check results.

### Step 6: Fold the result back
- **Envelope file** (Route 2 and above): record the role's return as `<unit>/envelopes/<kind>-<NN>.yaml` with kind `scout`, `challenger`, `review` or `reconciler`. You write it, never the role, and never by hand-editing YAML:
  ```bash
  devkit workflow envelope new --unit <dir> --kind review --stage review-refine \
    --summary "..." --base <ref> --head <sha> --check tests="PASS ..." --findings-file -   # findings YAML on stdin, as found
  devkit workflow envelope new --unit <dir> --kind reverify --from latest --resolve 1 --resolve 3 --waive "2=<rationale>"
  devkit workflow envelope check --unit <dir>   # reports malformed files
  ```
  Repeat `--assume`/`--unverified` for `assumptions` and `unverified_areas`. A `review` records findings as found (all open); the `reverify` closes that round. The conversation keeps the summary and the file path only. Route 1 does not require envelope files. For a proposal spike the unit is the proposal bundle: `--unit docs/proposals/PROP-<slug> --stage spike`.
- Scout/Challenger: write the comparison table and recommendation into the proposal bundle (`materials/` or `proposal.md`); keep `unverified_areas` visible for the `direction` gate (G2).
- Reviewer: fix findings, then re-verify only the changed part (tests for touched packages, `devkit rules check --staged`).
- Reconciler: review the draft diff as you would any docs change, stage only agreed paths, run `devkit rules check --staged`, and keep confirmation (`reconcile.md` `status: resolved`) for the Developer per the `sr-sync` skill.
- Commits, when authorized, are made by the Developer with `git commit -m "..."` (the commit gate runs the checks), staging only this task's agreed paths.

---

## 4. Definition of Done

- [ ] Contract read; host projection status stated when not native.
- [ ] Payload had all five fields; head SHA recorded.
- [ ] Returned fields validated; stale or failed results not used as evidence.
- [ ] Actual diff compared with `allowed_boundaries`; index and HEAD unchanged by the role.
- [ ] Result folded back into the current stage's artifact; envelope file written for Route 2 and above.
