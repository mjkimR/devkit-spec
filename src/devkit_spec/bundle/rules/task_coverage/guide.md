# [RULE-task-coverage] Acceptance Criteria Task Coverage

## 1. Overview

Every acceptance criterion of an active spec is covered by a task, and every task references only criteria the spec
defines, so no criterion is forgotten in the plan and no task builds against a criterion that does not exist. The
rule checks the ID links only; whether the tasks really fulfil the criteria is for tests and review.

- **Phase and severity**: `linter`, `error`. Shipped by the `spec` bundle (preset `core`).
- **What is checked**: each `specs/**/tasks.md` against the `spec.md` beside it. A spec without `tasks.md` yet is not
  checked, and neither is a spec with `status: completed`.
- **Targeting**: changing either file can break the pair, so the pair is checked when `spec.md` or `tasks.md` is
  targeted, and each violation is reported on the file it belongs to: a commit that adds `[AC-03]` to `spec.md`
  reports the uncovered ID on `tasks.md`. Files matched by `[rules] exclude` are never reported. A completed spec's
  pair is work history, checked only when `spec.md` or `tasks.md` is named as an explicit target
  (`devkit rules check specs/.../tasks.md`).

### Acceptance criteria

Every H3 under the H2 whose title contains `Acceptance Criteria` carries exactly one `[AC-NN]` ID: `AC-` followed by
two or more digits, compared as written (`AC-01` and `AC-001` differ). IDs are unique within the spec, and the spec
defines at least one. H3s under other sections are not criteria.

### Task references

A checklist task (`- [ ]`, `- [x]`, also with `*` or `+`) covers an ID written in its text as `[AC-01]`, or listed on
a direct child line (indented two spaces deeper) `- _Requirements: AC-01, AC-02_`. A task may cover several IDs and an
ID may be covered by several tasks. Nested tasks count too.

Nothing else covers an ID: tables, prose, blockquotes, frontmatter, fenced code, HTML comments, a `_Requirements:_`
line that is not a direct child of a task (unindented, or under a non-task item), and a checklist item indented four
or more spaces that is not the direct child of a task (indented code).

## 2. Cause of Violation

On `spec.md`:

- An acceptance criterion H3 without exactly one valid ID: `acceptance criterion heading must carry exactly one
  [AC-NN] ID, found <n>`.
- A duplicate ID: `duplicate acceptance criterion ID <ID>`.
- No criteria at all: `no acceptance criteria defined`.
- A missing or unreadable `spec.md` beside `tasks.md`: `the paired spec.md cannot be read: <reason>`.
- Spec frontmatter that does not parse: `invalid spec frontmatter: <reason>`.

On `tasks.md`:

- An entry of a `_Requirements:_` line that is not a well-formed ID: `invalid requirement ID '<value>'`.
- Defined IDs no task covers: `acceptance criteria without a task: <IDs>`.
- Covered IDs the spec does not define: `tasks reference undefined acceptance criteria: <IDs>`.

## 3. Remediation

Not fixable. Give each scenario its own `[AC-NN]` ID and update the task references to it; assign each uncovered ID
to a checklist task with `[AC-XX]` or a direct `_Requirements: AC-XX_` line; correct a reference to an ID the spec
defines; list only well-formed IDs (`_Requirements: AC-01, AC-02_`); restore a readable `spec.md` or repair its YAML
frontmatter.

When a criterion is added, split or rewritten rather than renumbered, read the `spec:contract-authoring` instruction
(Scope and Verifiability) for how an acceptance scenario is made checkable;
`devkit rules explain` prints its path as a `[RELATED: ...]` line.

## 4. Configuration

The rule has no settings. Project policy in `.devkit/config.toml` (`[rules] exclude`, `[rules.severity_overrides]`,
`[rules.phase_overrides]`) applies as to every rule.

## 5. Exceptions

There is no inline suppression. A criterion that no task implements is either dropped from the spec or given a task;
`[rules] exclude` removes a file from every rule.

## 6. Examples

```markdown
## 4. Acceptance Criteria & Behavioral Contracts
### Scenario 1 [AC-01]: Valid input is accepted
### Scenario 2 [AC-02]: Invalid input is rejected
```

```markdown
- [ ] **Task 1**: Domain types and validation [AC-01]
- [ ] **Task 2**: CLI wiring and its error output
  - _Boundary: src/cli/_
  - _Requirements: AC-01, AC-02_
```
