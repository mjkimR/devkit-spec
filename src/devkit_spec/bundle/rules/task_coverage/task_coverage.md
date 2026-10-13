# RULE-task-coverage

Every acceptance criterion of an active spec is covered by a task, and every task references only criteria the spec
defines. The rule checks each `specs/**/tasks.md` against the `spec.md` beside it; a spec without `tasks.md` yet is
not checked, and neither is a spec with `status: completed`.

## Acceptance criteria

Every H3 under the H2 whose title contains `Acceptance Criteria` carries exactly one `[AC-NN]` ID: `AC-` followed by
two or more digits, compared as written (`AC-01` and `AC-001` differ). IDs are unique within the spec, and the spec
defines at least one. H3s under other sections are not criteria.

```markdown
## 4. Acceptance Criteria & Behavioral Contracts
### Scenario 1 [AC-01]: Valid input is accepted
### Scenario 2 [AC-02]: Invalid input is rejected
```

## Task references

A checklist task (`- [ ]`, `- [x]`, also with `*` or `+`) covers an ID written in its text as `[AC-01]`, or listed on
a direct child line (indented two spaces deeper) `- _Requirements: AC-01, AC-02_`. A task may cover several IDs and an
ID may be covered by several tasks. Nested tasks count too.

```markdown
- [ ] **Task 1**: Domain types and validation [AC-01]
- [ ] **Task 2**: CLI wiring and its error output
  - _Boundary: src/cli/_
  - _Requirements: AC-01, AC-02_
```

Nothing else covers an ID: tables, prose, blockquotes, frontmatter, fenced code, HTML comments, a `_Requirements:_`
line that is not a direct child of a task (unindented, or under a non-task item), and a checklist item indented four
or more spaces that is not the direct child of a task (indented code).

## Violations

- An acceptance criterion H3 without exactly one valid ID, a duplicate ID, or no criteria at all: give each scenario
  its own `[AC-NN]` ID and update the task references.
- `acceptance criteria without a task`: assign each listed ID to a task.
- `tasks reference undefined acceptance criteria`: correct the reference to an ID the spec defines.
- `invalid requirement ID`: every entry of a `_Requirements:_` line must be a well-formed ID.
- A missing or unreadable `spec.md` beside `tasks.md`, or spec frontmatter that does not parse: restore or repair it.

There is no automatic fix. The rule checks the ID links only; whether the tasks really fulfil the criteria is for tests
and review.

## Scope

Changing either file can break the pair, so the pair is checked when `spec.md` or `tasks.md` is targeted, and each
violation is reported on the file it belongs to: a commit that adds `[AC-03]` to `spec.md` reports the uncovered ID on
`tasks.md`. Files matched by `[rules] exclude` are never reported. A completed spec's pair is work history, checked only
when `spec.md` or `tasks.md` is named as an explicit target (`devkit rules check specs/.../tasks.md`).
