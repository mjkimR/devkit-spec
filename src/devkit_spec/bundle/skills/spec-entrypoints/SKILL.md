---
name: spec-entrypoints
description: Derive docs-spec-code links from a spec bundle's tasks.md (_Boundary) and reconcile.md (targets), review the candidates, and write the chosen ones into capability/story entrypoints. Use during spec-sync for the current bundle, or across completed specs to backfill empty entrypoints.
---

# spec-entrypoints: Entrypoint Derivation and Sync

Use this skill when a spec bundle has both `tasks.md` and `reconcile.md` (normally inside `spec-sync`, after the reconcile record is written), or when capability/story documents lack `entrypoints` and completed specs can supply them. The command joins declarations mechanically; this skill supplies the review that decides what is written. Path contract: `devkit rules explain RULE-code-entrypoints`.

---

## 1. Inputs

- Code side: every `_Boundary` value in the bundle's `tasks.md`. `N/A`, globs, absolute paths and paths under `docs/` or `specs/` are reported as `[SKIPPED: ...]` with a reason.
- Document side: `reconcile.md` `targets` under `docs/capabilities/` or `docs/stories/` (including the same directories under `docs/packages/<name>/`) whose resolution is not `waived`. Other targets are `reason=not-entrypoint-bearing`.
- A candidate under another candidate of the same bundle is folded into the ancestor (`folded_into=`) and is never written.

---

## 2. Procedure for the current bundle

1. **Derive**: `devkit spec entrypoints derive --spec specs/<YYYY-MM>/<YYYYMMDD>-<slug>`. Read the `[CANDIDATES: <doc> ...]` line of each document: `new=` lists paths it does not declare yet, `declared=` paths an equal or ancestor entrypoint covers, `missing=` paths absent from the working tree (never written), `folded=` paths a same-bundle directory candidate covers.
2. **Review** before writing. Drop a document when the bundle touched it only for metadata or wording (its reconcile target is `modified`, but the code paths belong to another capability). Keep a directory candidate only when the document really owns that package; prefer the file-level candidate when a task's boundary was broad. A pair is a declaration join, not proof that the code implements that document.
3. **Apply** the chosen pairs only: `devkit spec entrypoints derive --spec <dir> --apply --target <CAP-or-US-id> --code <path> [--code ...]`. `--target` picks documents, `--code` keeps candidates equal to or under a path, `--exclude` drops hub paths every bundle touches (root `AGENTS.md`, `README.md`, agent guides). Without them every bearing target and candidate of the bundle is written. A candidate folded into a same-bundle ancestor is reported as `[SKIPPED: ... kind=apply reason=folded]` and never written; to declare the file instead of the directory, apply with `--all` (folding is per bundle) or edit the boundary. The command appends to the existing list (a document whose `entrypoints` is not a list of paths is left unchanged and reported as `SPEC_ENTRYPOINTS_APPLY_FAILED`), keeps every other frontmatter byte, writes directories with a trailing `/`, and is idempotent (a rerun reports `new=0` for what it wrote).
4. **Verify**: `devkit rules check <document>` (`RULE-code-entrypoints` checks that every written path exists) and `devkit spec list capability --file <path>` (or `story`) for one written path: the document must be listed.
5. **Record**: a document whose `entrypoints` changed is a Living Spec change; make sure it is a `modified` target in the bundle's `reconcile.md`.

---

## 3. Backfill across completed specs

1. `devkit spec entrypoints derive --all` aggregates every `completed` and `in-progress` bundle; each path carries its spec count, `src/a.py(2)` (`--format json` for the spec IDs). Add `--status` to change the filter.
2. Choose a threshold from the distribution: `--min-count 2` keeps pairs two or more specs agree on and removes most one-off joins. Inspect the remaining `new=` paths per document; `--format json` helps when the list is long.
3. Apply per document so each decision is explicit: `devkit spec entrypoints derive --all --min-count <n> --apply --target <id> --code <path> ...`, adding `--exclude` for hub paths. Directories and files under them collapse to the directory. Then run `devkit rules check`.
4. Report which documents were filled and which stayed empty with the reason (`missing-path`, no candidates, candidates rejected in review). Backfill of many documents is a Living Spec change: record it through the current bundle's `reconcile.md` or an S-Lane report.

---

## 4. Definition of Done

- [ ] Every written path exists and `devkit rules check` passes.
- [ ] Each written document was reviewed, not applied blindly from the full candidate list.
- [ ] Documents with changed `entrypoints` are reconcile targets (or reported in S-Lane).
- [ ] Rejected or deferred candidates are stated in the report when they matter later.
