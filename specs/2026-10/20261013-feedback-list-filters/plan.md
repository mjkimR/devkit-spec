---
id: PLAN-feedback-list-filters
spec: SPEC-feedback-list-filters
---

# Technical Plan: `SPEC-feedback-list-filters` Feedback list filters

## 1. Constitution & Invariant Review

None. The change extends `devkit spec list` inside `CAP-DOCS-document-lookup` and revises that capability's non-goal
on feedback filters (G2 direction, decision 02). Output stays within devkit's sentinel and JSON conventions
(`ARCH-08-cross-cutting`); `--where` errors reuse devkit's `ARGUMENT_INVALID`, so no new error code is defined.

## 2. Architecture Overview & Impact

- **Impacted Components**:
  - `src/devkit_spec/cli/documents.py`: the `--where` option (parsed in the command body, inside devkit's
    `boundary`, into `WhereItem`s; a malformed item raises `ArgumentError`), the frontmatter match, the severity order in
    the sort key, the feedback fields on text lines and JSON records, and `--where` in the `[NEXT_CMD]` arguments.
  - `src/devkit_spec/bundle/skills/spec-next/SKILL.md`, `src/devkit_spec/bundle/skills/spec/references/envelope.md`,
    `src/devkit_spec/bundle/skills/spec-feedback/references/sweep.md`,
    `src/devkit_spec/bundle/playbooks/feedback-hygiene/SKILL.md`: select feedback with `--where` instead of reading
    each file's `severity`.
  - `docs/capabilities/documents/CAP-DOCS-document-lookup.md`: reconciled after review (`spec-sync`).
- **New Dependencies**: None.

## 3. Component & Interface Design

### Data Contracts & Types

```python
@dataclass(frozen=True)
class WhereItem:  # one --where FIELD=A,B
    field: str
    values: frozenset[str]  # lower-cased
    given: str  # the text given, repeated in [NEXT_CMD]


def _where(given: tuple[str, ...]) -> tuple[WhereItem, ...]: ...  # ARGUMENT_INVALID on a malformed item
def _matches(document: Document, where: tuple[WhereItem, ...]) -> bool: ...  # AND over items
def _field_values(value: object) -> set[str]: ...  # scalar: its text; bool: true/false; list: its scalars


SEVERITY_ORDER = ("critical", "blocked", "workaround", "noise")  # anything else ranks after them
FEEDBACK_FIELDS = ("severity", "scope", "target")
```

- Values are compared with `str.strip().lower()`; a YAML date or number compares as its `str()` text.
- The sort key becomes `(kind order, severity rank if feedback else 0, id, path)`.
- Text lines: `severity=`, `scope=`, `target=` follow `tasks=` on feedback lines only; JSON feedback records gain the
  three keys (`null` when absent), other records are unchanged.

## 5. Error Handling & Edge Cases

- `KEY` without `=`, an empty key, or no non-empty value after splitting on `,`: `ArgumentError` naming the item,
  exit `2`, nothing on stdout. Parsing runs in the command body: an error raised in a click callback
  escapes `boundary` and is not rendered as an advisory.
- A frontmatter value that is a mapping or `null` matches nothing; a list matches when one scalar element matches.

## 6. Verification & Test Plan

- `tests/test_cli_documents.py`: one test per `AC-01`..`AC-07` (`CliRunner` on fixture workspaces, text and JSON).
- `AC-08`: `rg` over the four assets for the `--where severity=critical` command and the absence of the per-file
  instruction; `tests/test_bundle_budgets.py` keeps skills and playbooks under 8192 bytes.
- `just ci` (lint-check, Pyright, pytest, `devkit rules check`); `uv run --no-active devkit sync` then
  `devkit rules test` for the deployed rules.
- Dogfood: `devkit spec list feedback --status open --where severity=critical --history -n 0` on this repository.
