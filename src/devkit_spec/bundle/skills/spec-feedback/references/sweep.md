# Feedback Sweep

Read this for a workflow stage sweep or a user-requested session sweep. The recording constraints of the `spec-feedback` skill (section 2) apply to every observation.

## Entry

Only an explicit user message requesting a session sweep selects the user branch. An agent-chosen invocation of `/spec-feedback` remains autonomous; it does not become a user request.

- **User-requested session sweep**: when the user asks `/spec-feedback` to collect session observations or perform a retrospective, cover the whole session whatever autonomous capture, coverage or stage policy says, and write no envelope, even when a spec bundle exists. A request to record one named observation follows the recording procedure instead.
- **Workflow stage**: `devkit workflow next --unit <dir>` names `collect-feedback` after `living-spec-draft` and before `final-change-report` in Development, or after `spike` and before `direction-handoff` in Planning; its exit check is `envelope-check-pass(feedback swept)`. For Development, one sweep per spec bundle; the envelope passes even with zero observations. When the project switched the stage off (`[workflow.stages] collect-feedback = "off"`, shown by `devkit spec policy` as `[STAGE_POLICY: collect-feedback state=off]` and by `next` as `[SKIPPED: collect-feedback reason=stages.collect-feedback=off]`), do not run a stage sweep autonomously; report the stage as skipped.

Read `devkit spec policy` before the sweep. With `capture=requested-only`, an autonomous stage sweep records no
observations: write its feedback envelope with `--check "swept=PASS skipped=capture.requested-only"` and a summary
of the policy skip, then report it as skipped. A `session` task reports the skip without an envelope. A stage switched off
produces no sweep envelope. Explicit user requests follow the user branch regardless of these restrictions.

Use observed command output, instructions or file state as evidence. Promotion, dismissal, forwarding and feedback `status` changes stay in a separate feedback-hygiene session.

## Procedure

1. **Collect**: scan this session and `git diff` for unrecorded observations:
   - repository-owned rules, skills, instructions, playbooks, workflows, role contracts, script/CLI tools, templates,
     overrides and Living Spec documents (`scope: repo`): these are the base targets;
   - upstream tools used in the session, including devkit and devkit-spec, when `coverage=repo-and-upstream` or
     explicitly requested (`scope: upstream`);
   - relevant observations whose owner is uncertain or spans assets (`scope: unknown`), to classify during hygiene.
   The user never supplies ownership or destination classification.
2. **Deduplicate**: `devkit spec list feedback --status open --all-namespaces -n 0` lists every open feedback file, completed spec bundles included (`--query <text>` narrows by ID or title); follow `[PAGE: ... next=<offset>]` with `--offset` when a limit is set. Each line carries `target`; read a candidate's `kind` and `category` when its `target` matches: the same `target` and nature is a duplicate. Skip it and retain its ID for the report.
3. **Record** each remaining observation with the recording procedure (one file, configured detail). Use the current proposal feedback directory during Planning, the spec feedback directory during Development, or the month-level directory without a Unit.
4. **Report by entry**:
   - **User request**: write no envelope. Report recorded IDs, duplicate IDs, and the open and critical counts of this work (`--where severity=critical` lists the critical ones). If critical items exist, recommend a separate feedback-hygiene session; do not run it without the user's request. Do not repeat task summaries or test gates. If context loss prevents full coverage, state the gap instead of claiming a complete sweep.
   - **Unit stage (proposal or spec)**: record the sweep envelope:

     ```bash
     devkit workflow envelope new --unit <dir> --kind feedback --stage collect-feedback \
       --summary "<coverage, recorded IDs and duplicate IDs>" \
       --check "swept=PASS recorded=<n> duplicates=<n>"
     ```

     `swept` is `FAIL <reason>` only when the session could not be covered; name the gap with `--unverified "<gap>"` and leave the stage open. Return one line: `> Feedback sweep: <n> recorded, <n> duplicates (envelopes/feedback-NN.yaml)`.

For the `report-session` stage of a `session` task (no spec bundle, no unit), apply the stage policy, do steps 1 to 3 against the month-level directory, and report in the session report without an envelope.


## Planning run coverage

Before every Planning return to the user (including questions), sweep this run and its committed accumulated records.
Deduplicate existing observations across the full open backlog and write a new `feedback` envelope under the
proposal's `envelopes/`, at `collect-feedback`, before its single `worker` envelope and last commit.
An earlier PASS does not cover later work, even when `next` already passes the stage. This is an executor
procedure, not a new engine freshness check. Uncovered context is `swept=FAIL <gap>` plus `--unverified`;
do not claim complete coverage for a failed/partial run.

Apply the same stage-off/requested-only rules as Development. Stage-off produces no sweep envelope but does not turn
off observed capture. Requested-only writes new policy-skip evidence without autonomous observations. Zero observations
passes. A separate explicit user-requested sweep writes no envelope and does not replace required stage evidence.

Acceptance and rejection both use the records made before the run returned; rejection invokes no new agent and makes
no claim about subsequent conversation coverage. Before any Planning run there are no run observations. A rejected
proposal retains its feedback until the Host preserves open files before cleanup. Handoff drops Planning envelopes;
Development runs its own sweep.
