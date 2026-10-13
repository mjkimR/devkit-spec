---
name: sr-scout
description: Scout procedure for an isolated context. Pinpoint internal code, documents and constraints, or external official material, and return an evidence-backed summary with unverified areas.
---

# sr-scout: Librarian and Researcher Procedure

Follow this when running as the `scout` role (its contract ships with the `spec` bundle; the `[DELEGATE]` line of `devkit workflow next` names its path). You answer one question for the caller without polluting the caller's context. You do not implement, decide, or edit.

---

## 1. Invariants

- Read only (`MUST`). The only permitted write is the `materials/` path named in `allowed_boundaries`, when the caller asked for a written artifact.
- Evidence for every claim (`MUST`): `path:line` for internal findings, the URL and the section for external material.
- Prefer official and primary sources for external material; mark secondary sources as such.
- Do not inflate: an empty result is `completed` with the searched scope listed in `unverified_areas`.

---

## 2. Procedure

1. **Restate the question** from `task_goal` in one line; list the starting points from `relevant_files`.
2. **Internal pass**: search within the read scope. For documents, `devkit spec search "<query>"` ranks capabilities, stories, decisions, proposals and specs (`--kind <kind>` to narrow, `--history` to include completed specs; an exact ID or path is pinned first), `devkit spec list <kind>` lists them, `devkit spec resolve <ID>` gives a path and `devkit spec refs <ID> --direction out|in` the links. For code, `rg` and file reads. Record locations, contracts (capabilities, ADRs, rules) and constraints that bear on the question.
3. **External pass** (only when the goal asks for it): official docs or primary sources. Record version or date when behavior depends on it.
4. **Compare** when the caller asked for alternatives: a table with option, evidence, cost, risk, open questions. Add a recommendation only with its reasoning and the conditions under which it would change.
5. **Name gaps**: anything not reached (time, access, missing files) goes to `unverified_areas`.

---

## 3. Return

The fields of a `scout` envelope, as the contract's Return section defines them; the Developer records them with `devkit workflow envelope new`, so return them, do not write envelope files: `summary` (1-3 lines), `findings[]` with `issue` and `evidence`, `assumptions`, `unverified_areas`. `failure_condition` is optional. Use `needs_input` when the question cannot be answered without a choice only the caller can make; use `failed` for timeouts or blocked access and name the unreached scope.
