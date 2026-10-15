---
id: PLAN-list-unknown-status
spec: SPEC-list-unknown-status
---

# Technical Plan: `SPEC-list-unknown-status` Flag an unknown status filter in devkit spec list

## 1. Constitution & Invariant Review

None. Notices follow the existing `SpecError` notice pattern (`Level.NOTICE`), returned under `notices` and rendered
on stderr; every new code must be documented under `docs/` (`tests/test_documented_codes.py`).

## 2. Architecture Overview & Impact

- **Impacted Components**:
  - `src/devkit_spec/errors.py`: `ListStatusUnknownNotice(SpecError)`, code `SPEC_LIST_STATUS_UNKNOWN`,
    `Level.NOTICE`; the message names the unknown values and the selected kinds, the `[FIX]` lists the known
    statuses sorted (or says none occur).
  - `src/devkit_spec/cli/documents.py` (`list_cmd`): when `--status` is given, collect the lower-cased statuses of
    every indexed document of the selected kinds (all kinds when none is given), ignoring history and namespace;
    values not among them produce one notice. It joins `index.problems` in both the JSON `notices` and `_finish`.
  - `tests/test_cli_documents.py`: AC-01 to AC-05.
  - `docs/capabilities/documents/CAP-DOCS-document-lookup.md` (`spec-sync`, not a build task): the new code and
    the notice behavior. `tests/test_documented_codes.py` fails for the new code until its row is in the code table,
    so the row lands with the build commit.
- **New Dependencies**: None.

## 3. Error Handling & Edge Cases

- An empty status value (`--status ,`) keeps today's behavior: no filter and no notice.
- A document without a status contributes the empty string, which never matches a requested value.

## 4. Verification & Test Plan

- `just test` (new tests plus `tests/test_documented_codes.py`), `just lint`, `just check`, `devkit rules check`.
