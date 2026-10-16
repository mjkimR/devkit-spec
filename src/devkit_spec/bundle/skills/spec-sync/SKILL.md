---
name: spec-sync
description: Reconcile completed feature specs and discovered behaviors into the durable Living Specification (docs/capabilities/, docs/stories/), ensuring zero documentation rot.
---

# spec-sync: Living Specification Reconciliation Workflow

Use this skill immediately after `spec-review` passes and implementation is complete: the `living-spec-draft` stage (it opens on `envelope-review-passed`). It promotes what the feature spec established into the Living Spec (`docs/capabilities/`, `docs/stories/`). Read the `living-spec-writing` instruction before editing `docs/`.

---

## 1. Prerequisites & Inputs

- Completed feature files: `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/spec.md`, `tasks.md`.
- Durable documentation directory: `docs/capabilities/`, `docs/stories/`, `docs/architecture/`, `docs/decisions/`.

---

## 2. Reconciliation Principles

### Principle 1: Never Delete the Permanent Backbone
- Transient task lists belong in `specs/`. Permanent system capabilities belong in `docs/capabilities/`.
- ADRs are append-only: replace a decision with a new ADR linked through `supersedes`, never by editing the accepted one.

### Principle 2: Orthogonal M:N Traceability
- Capabilities and Stories are linked via frontmatter, both ways and by exact ID (`RULE-traceability-link`):
  - In `docs/capabilities/<area>/CAP-<AREA>-<slug>.md`:
    ```yaml
    stories:
      - US-<slug>
    ```
  - In `docs/stories/<area>/US-<slug>.md`:
    ```yaml
    capabilities:
      - CAP-<AREA>-<slug>
    ```
- Never nest one kind inside the other.

### Principle 3: No Manual README Catalogs
- Do NOT maintain index tables in directory `README.md` files; list with `devkit spec list <kind>` and `devkit spec refs <ID>`.

### Principle 4: Living Spec Currency
- If the feature modified existing behavior, update the existing `docs/capabilities/` document so it reflects the new truth.
- Rewrite the affected statement in place. Do not append dated notes, correction markers, "changed from X to Y" narration or history sections; cite the deciding ADR or spec by full ID (`` `ADR-<slug>` ``, `` `SPEC-<slug>` ``) where the reason matters. History stays in Git, ADRs and `docs/materials/`.
- If the feature added new system capabilities, create a new capability document under the appropriate area directory, from `.devkit/managed/spec/templates/capability.md` (stories: `story.md`). The file stem is the ID (`CAP-<AREA>-<slug>`, `US-<slug>`), `area` matches the directory, no slug is a sequence number (`RULE-id-convention`), and `summary` is English (`RULE-document-summary`).

---

### Principle 5: Draft Delegation and Integration-Stage Confirmation
- The implementer writes and resolves the reflection and `reconcile.md` at every `activity-effort`. Verification: `low` your own check; `medium` the `reviewer` checks the written result; `high` a separate read-only `reconciler` verifies it (`spec-delegate`). You fix what it finds. Each verification is a `reconcile-check` envelope (the `spec` skill's `references/completion.md`). A `session` task has none: a needed Living Spec change raises it to `spec`.
- Implementation-versus-contract mismatches are returned for a code fix (the stage returns to `build-verify`, or `fix-verify` for a bugfix), not endorsed by documentation or waived.
- Confirmation (`reconcile.md` `status: resolved`, spec `status: completed`) is done by the Developer or the integration executor (`spec-integrate`). Resolve before the `dev-integration` gate. Intermediate commits do not complete this stage; the final check is `devkit rules check --ci --base <ref>`.

## 3. Reconciliation Workflow

### Step 1: Identify Impact on Permanent Backbone
- Read `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/spec.md` and review actual code changes. `devkit spec refs <ID> --direction in` and `devkit spec search "<topic>"` find the documents a changed behavior is described in.
- Determine:
  1. Does this add a new User Story? -> Create `docs/stories/<area>/US-<slug>.md`.
  2. Does this add a new System Capability? -> Create `docs/capabilities/<area>/CAP-<AREA>-<slug>.md`.
  3. Does this update an existing capability? -> Edit the existing CAP document.
  4. Does this alter overall architecture? -> Update `docs/architecture/` diagrams/sections.

### Step 2: Document Reconciliation Record
The `spec` skill's `references/completion.md` holds the evidence rules (waivers, required mismatches) and the distinction between mandatory reconciliation and optional promotion. Retain resolved records in place.
- Create `specs/<YYYY-MM>/<YYYYMMDD>-<slug>/reconcile.md` to document the handoff: one target per Living Spec file changed (`docs/capabilities/...`, `docs/stories/...`, `docs/architecture/...`, `docs/decisions/...`), and the no-impact reasoning in the body when there is none. Check results belong in the final change report envelope, not here.

```yaml
---
reconcile_id: REC-<slug>
feature: SPEC-<slug>
status: pending            # pending | resolved
targets:
  - file: docs/capabilities/<area>/CAP-<AREA>-<slug>.md
    resolution: modified   # modified | waived (with a substantive rationale)
---
```
- In a registered task worktree, then run `devkit spec scope update --spec <dir>` (`SPEC_SCOPE_TOKEN_MISSING`: not registered, skip); `[SCOPE_ACK]` overlaps inform scheduling, never block.

### Step 2a: Hand Off Deferred Work
- Apply the Deferred Work Handoff in the `spec` skill's `references/completion.md` before deleting a source proposal or marking the current spec completed.
- Link each concrete retained follow-up to an existing open PROP or create a draft one (`devkit spec proposal new <slug>`), with source, remaining scope, deferral reason, restart conditions, and acceptance checks. Record the destination in `reconcile.md` and verify it through `devkit spec list proposal`.
- Do not transfer unmet requirements still in the agreed scope to make the current feature appear complete.

### Step 2b: Sync Entrypoints from the Bundle
- Run the `spec-entrypoints` skill for this bundle: derive (doc, code) candidates, review them, apply the chosen ones.
- A document whose `entrypoints` changed is a `modified` target in `reconcile.md`.

### Step 3: Run Deterministic Lint Gates
- Execute `devkit rules check --staged` for staged changes or `devkit rules check --ci --base <ref>` for a committed branch; state which scope was checked. It verifies:
  - Valid frontmatter with `id`, `title` and `status` (`RULE-spec-format`).
  - Bidirectional traceability between stories and capabilities (`RULE-traceability-link`; `devkit rules fix <document>` appends a missing reverse link).
  - IDs derived from paths and references by resolvable full ID (`RULE-id-convention`, `RULE-document-reference`).
  - Spec status agreeing with `tasks.md` and `reconcile.md` (`RULE-spec-lifecycle`), and a well-formed reconcile record (`RULE-reconcile-contract`).
  - Every declared `entrypoints` path exists (`RULE-code-entrypoints`).
- Run the project's own lint (e.g., `just lint`) where it covers Markdown and Mermaid diagrams in the updated docs.

### Step 4: Archive or Mark Completed Feature Spec
- Set `reconcile.md` `status: resolved` once every target is reflected or waived, then set `status: completed` in the frontmatter of `spec.md` (`devkit rules fix <dir>/spec.md` does it once every task is checked and the reconcile record is resolved). The `living-spec-draft` stage exits on `frontmatter(reconcile.md status resolved)` and `anchor-status-completed`; task progress is computed from the checkboxes and never written.
- Documentation updates go in the same commit as the feature code or the one right after it (`git commit`; devkit's commit gate runs the staged checks).

---

## 4. Definition of Done (DoD) for Sync
- [ ] New/updated capabilities and stories documented in `docs/`.
- [ ] Bidirectional frontmatter links verified.
- [ ] `reconcile.md` written in the feature spec directory and `resolved`.
- [ ] `devkit rules check` (`--staged` or `--ci --base <ref>`) and the project lint pass with 0 errors.
- [ ] Concrete deferred work has a discoverable PROP and source link, or there is no retained follow-up.
- [ ] Feature spec marked as completed.
