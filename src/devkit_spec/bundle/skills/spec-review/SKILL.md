---
name: spec-review
description: Perform thorough verification against git diff and tests before declaring task or feature completion. Detects unexplained scope drift, phantom completions, and unstated requirement drifts.
---

# spec-review: Pre-Completion Verification Workflow

Use this skill when all implementation tasks in `tasks.md` are marked complete (`tasks-all-checked` opens the `review-refine` stage), or before submitting a pull request. This serves as the mechanical Quality Gate to prevent "phantom completion" (where an agent claims work is done without actually fulfilling the contracts or running tests).

---

## 1. Prerequisites & Inputs

- Feature files: `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/spec.md`, `plan.md`, `tasks.md`.
- Working tree with all implementation changes committed or staged.

---

## 2. Verification Workflow & Converge Invariants

### Principle 1: Append-Only Convergence
- **NEVER rewrite or delete original tests or acceptance criteria** in `spec.md` just to force a failing test to pass.
- If an unforeseen technical limitation or architectural friction arises:
  - DO NOT silently weaken the assertions.
  - Record it as a review finding. A contract change returns to the `direction` gate (G2) for the user's decision before any contract is edited (`devkit workflow return --unit <dir> --to direction`).

### Principle 2: Baseline Trust & Mechanical Verification
- Evaluate gates by the actual omissions they catch and their operating cost.
- Do NOT introduce redundant, heavy LLM semantic re-evaluations. Rely on deterministic, mechanical execution: `git diff` checks, compile/build passes, test suites, and linters.

### Step 1: Mechanical Git Diff Inspection
- Run `git status -s` and `git diff` against the base branch (e.g., `main` or feature branch root).
- Check for:
  - **Scope drift**: Did the changes touch files outside the declared `_Boundary:` in `tasks.md` without a stated reason? `_Boundary:` is expected scope; an explained extension is not a finding. A delegated write scope is strict: any change outside it is a finding. Implemented non-goals or unrequested features are always findings.
  - **Stray Files**: Are there leftover debug scripts, `.DS_Store`, or temporary scratch files?
  - **Dead Code / Debug Prints**: Check for `print`/`console.log` debugging, commented-out code blocks, or mock bypass flags.

### Step 2: Contract & Acceptance Criteria Validation
- Compare actual code and test outputs against every `[AC-NN]` Given/When/Then scenario in `spec.md`:
  - [ ] Happy path scenario tested and passing.
  - [ ] Edge cases and boundary conditions tested and passing.
  - [ ] Error payload schemas and status codes match exact contracts.
- Check Non-Goals: Verify that no excluded scope was accidentally or partially implemented.
- Bugfix bundles: the Red and Green envelopes exist and the regression test is kept (`devkit workflow envelope check --unit <dir>`).

### Step 3: Run Deterministic Verification Gates
- Execute the test suite: unit tests, integration tests, end-to-end tests (e.g., `just test`).
- Run the linters and formatters (e.g., `just lint`) and the spec rules: `devkit rules check --staged` for staged changes, `devkit rules check --ci --base <ref>` for a committed branch.
- Ensure exit code is 0 with zero warnings/errors.

### Step 4: Capture Unstated Requirements & Drift
- Did implementation reveal new requirements, API changes, or unexpected constraints not covered in the original `spec.md`?
- If yes, record each as a finding in the review envelope. One that changes a contract returns to the `direction` gate; one inside the agreed contract is fixed or waived in the reverify round.

---

### Delegated execution (Reviewer role)
- This skill may be executed by the `reviewer` role in an isolated context (its role contract, invoked through `spec-delegate`; `devkit workflow next` shows `[DELEGATE]` for this stage). The Developer running it directly is the default; both produce the same envelope.
- When delegated: inputs are the actual diff (`diff_scope`), the relevant contracts and the Developer's check results, not the implementer's narrative. The Reviewer MUST NOT modify source, tests, spec files or docs, and MUST NOT stage or commit; discovered requirements are returned as findings.
- Every finding carries `evidence` (path:line) and a `failure_condition`. Zero findings is a valid PASS; do not manufacture defects. A review of a stale head is returned as `needs_input` and is not completion evidence.
- After fixes, re-verify only the changed part rather than re-running the whole review.

### Optional feedback breakpoint

After `review-refine` passes and before `living-spec-draft`, an executor may pause for user feedback or proceed automatically. An external runner owns that option and its wait/resume state; it adds no stage, check or approval file. Intermediate commits are independent of waiting. Feedback that changes implementation returns to build/reverify for the affected part; a direction change returns to the `direction` gate. This breakpoint does not replace the `integration` gate (G3), and Living Spec reflection still completes before G3.

## 3. Review Report

The review envelope is the report, for a direct run and a delegated Reviewer run alike. For Route 2 and above, record the findings as found (all open):

```bash
devkit workflow envelope new --unit <dir> --kind review --stage review-refine \
  --status completed --summary "<scenarios confirmed and by what>" \
  --check tests="PASS <command and count>" --check lint="PASS devkit rules check --staged" \
  --base <ref> --head $(git rev-parse HEAD) --findings-file - <<'EOF'
- issue: "<what was found>"
  evidence: "path:line"
  failure_condition: "<under which input or state it fails>"
  suggested_action: "<recommended next step>"
EOF
```

This writes the next `envelopes/review-NN.yaml`; omit `--findings-file` for a pass. After fixes, close the round with `devkit workflow envelope new --unit <dir> --kind reverify --stage review-refine --from latest --resolve <N> --waive <N>=<reason>` (`--resolve all` when every finding is fixed), which writes `reverify-NN.yaml`; `devkit workflow next --unit <dir>` reads it for `envelope-review-passed`. Do not record fixes inside the review file itself. Route 1 (`s-lane`) states the same content in the session response.

- Unexplained scope drift, stray files and unmet scenarios are findings, each with `evidence` and `failure_condition`.
- Check results go in `checks`; the summary states which scenarios were confirmed and by what.
- PASS is `status: completed` with no open findings; REVISE is `status: completed` with findings; `needs_input` when verification is blocked.

---

## 4. Definition of Done (DoD) for Review
- [ ] `git diff` physically inspected.
- [ ] No unexplained scope drift and no non-goal implemented.
- [ ] No test or acceptance criterion weakened to make a check pass.
- [ ] All verification test commands executed and confirmed green.
- [ ] Unstated discoveries recorded as review findings.
- [ ] Clear verdict rendered to the user.
