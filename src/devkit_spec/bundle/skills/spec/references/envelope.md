# Delegation Input and Return Envelope

Read this when delegating to a support role (`scout`, `challenger`, `reviewer`, `reconciler`), writing a review, presenting the final change report before `dev-integration`, or reporting the integration result. Role contracts ship with the spec bundle and are projected into each agent's native agent directory by `devkit sync`; the stage definition is rendered by `devkit workflow show --unit <dir>`. Envelope files follow devkit's envelope contract; this reference says how spec-driven delivery uses it. A `planning-worker` or `development-worker` run writes its own records instead ([worker records](worker-records.md)).

## 1. Input payload

Pass all five fields and never inject the whole tree; the `spec-delegate` skill's `references/payload.md` defines each field and the rows per role. Also state the host projection status for this call (`native`, `emulated`, `unsupported`) when it is not native, so the substitute guarantee is explicit.

## 2. Return envelope

A role returns the fields of a devkit envelope; the Developer records them (section 6):

```yaml
status: completed | needs_input | failed
summary: "1-3 line judgment or result"
findings:
  - issue: "Issue found or change made"
    evidence: "path:line or source URL"
    failure_condition: "Under which input or state it fails (required for challenger and reviewer)"
    suggested_action: "Recommended next step"
assumptions: ["Assumptions made inside the approved scope"]
unverified_areas: ["Scope not explored or needing confirmation"]
checks: { tests: "PASS 14/14" }        # when the role ran checks
diff_scope: { base: "<ref>", head: "<sha>" }
```

- `completed` with an empty `findings` list is a valid pass (zero findings allowed; no filler objections).
- `needs_input` names the missing input or the decision only the human can make.
- `failed` covers timeout, cancellation, tool failure, unsupported host feature, or a stale `diff_scope`. A failed or stale result is never completion evidence.
- Docs impact has no envelope key: the implementer writes it into `reconcile.md` (targets, or the no-impact reasoning in its body). Its verification at every effort is a `reconcile-check` envelope ([completion](completion.md)).
- Re-invocation or a stronger model is decided from the failure reason and changed input, not by repeating the same call.

## 3. Final change report (before `dev-integration`)

Kind `final-report`, carrying the evidence `devkit workflow next` cannot produce itself. The `final-change-report` stage needs `checks.tests`, `checks.build` and `checks.lint` starting with `PASS`:

```bash
devkit workflow envelope new --unit <dir> --kind final-report --stage final-change-report \
  --summary "..." --check tests="PASS 14/14" --check build="PASS" \
  --check lint="PASS devkit rules check --staged" --base <ref> --head $(git rev-parse HEAD)
```

Changed paths come from `git diff --name-only <base>..<head>`; docs impact and reconcile state live in `reconcile.md`; the review result is the latest review envelope. Do not repeat them. Record assumptions the user should see with `--assume`.

When open feedback marked `severity: critical` exists (`devkit spec list feedback --status open --where severity=critical`), including items the `collect-feedback` sweep just recorded, list them in the report presented to the user, one line each: `FB-<slug> → <target>`, nothing else. The summary stays in the feedback file; the line exists so the person deciding `dev-integration` sees that a feedback hygiene pass is due.

## 4. Integration result (after `spec-integrate`)

Integration writes no envelope. After the commit the Developer still runs `devkit rules check --ci --base <ref>` locally and reports the result in the conversation; that run is trusted without a file, and the repository CI re-runs the same check as the final gate (`lint-ci-clean`, a runner-class check). Report: base integrated, conflicts resolved (if any), what was re-verified, and the two separate facts that code review completed (latest review round or reverify) and integration completed. Anything written after the commit would need another commit, so nothing is.

## 5. The spec-review report

`spec-review` writes this envelope directly (kind `review`); there is no separate report format. Boundary violations, stray files and unmet scenarios are `findings` (each with `failure_condition`), check results are `checks`, and the verdict is the status: PASS → `status: completed` with no open findings, REVISE → `status: completed` with open findings, `needs_input` when verification is blocked. One format serves both the direct run and the delegated `reviewer` run.

## 6. Where reports live

A Unit (`spec` and `proposal` depth): every envelope is a file under the Unit's directory (the proposal's is dropped at handoff):

```
specs/<YYYY-MM>/<YYYYMMDD>-<slug>/envelopes/<kind>-<NN>.yaml
docs/proposals/PROP-<slug>/envelopes/<kind>-<NN>.yaml
```

- `kind`: `scout | challenger | review | reverify | reconcile-check | worker | answer | resolution | final-report` (a run's records: [worker records](worker-records.md)), or any kind matching `[a-z][a-z0-9-]*` that a workflow check names (`envelope-completed(<kind>)`, `envelope-check-pass(<kind> <key>)`, `revision-ancestor(<kind> <kind>)`). Workflow `sdd-spec-bugfix` uses `red` (`checks.reproduced`) and `green` (`checks.resolved`, `checks.preserved`), see the `spec-specify` skill's bugfix reference; the `collect-feedback` stage uses `feedback` (`checks.swept`), see the `spec-feedback` skill. `NN` is a sequence per kind; the highest is current and earlier files are history. Never overwrite; each write takes the next number.
- `review-NN.yaml` records a review round as found: every finding is `open`. `reverify-NN.yaml` closes a round: it names it in `review`, carries its findings forward with `resolution: resolved | waived` (a waived finding states its reason in `waiver`) and may add findings discovered while re-verifying. The deciding review state is the latest review round, or the latest reverify that closes it; a newer review round makes earlier reverify files history.
- Required keys: `kind` (equal to the file name kind) and `status`. A malformed file is reported as `[ENVELOPE_ERROR: ...]` and ignored.
- Everything else is optional and written only when it carries information: `stage`, `summary` (recommended), `findings`, `assumptions`, `unverified_areas`, `checks`, `diff_scope`. Do not restate other files: Git has the dates and paths, `reconcile.md` has the docs impact.
- `dev-integration` approval is not an envelope. Under `ask`, authority is the user's explicit OK, asserted with `--given dev-integration` on each `devkit workflow next --unit <dir>` after it and never written to a file, or the PR ready state where a runner binds the gate. Under `auto`, it is the reported policy delegation after required review, reconciliation and checks (`[GATE_PASSED: dev-integration ... source=policy]`). After that authorization `devkit workflow next --unit <dir>` names the `integrate` stage.
- `devkit workflow next --unit <dir>` evaluates these files (`envelope-review-passed`, `envelope-check-pass`, `envelope-completed`, `revision-ancestor`; `revision-ancestor` compares `diff_scope.head` of two kinds and needs real commit ids). Write files with `devkit workflow envelope new --unit <dir> --kind <kind> [--stage <id>]` (`review`, `reverify`, `worker`, `answer`, `resolution`: `envelope <kind>`) and authoring flags; never edit YAML: `--summary`, repeatable `--check key=PASS|FAIL|SKIP[ detail]` (how `envelope-check-pass` stages such as `feedback`, `red` and `green` get their evidence), `--assume`, `--unverified`, `--findings-file <path>|-`, `--base`, `--head $(git rev-parse HEAD)`; `envelope reverify --from latest --resolve N|all --waive N=REASON` carries findings forward. Check files with `devkit workflow envelope check --unit <dir>`.
- `session` depth keeps the report in the final response or PR body and writes no envelope at any effort; a reviewer subagent returns its result as a message. The conversation always keeps the summary and the file path, never the whole envelope.
