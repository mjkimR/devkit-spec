---
id: FB-envelope-head-accepts-unknown-commit
title: devkit workflow envelope new accepts a --head that names no commit
scope: upstream
kind: friction
category: tool-error
target: devkit workflow envelope new --head
skill: spec-review
agent: claude-code
origin: agent
severity: workaround
recurring: false
status: open
created_at: 2026-10-15
---

# [FB-envelope-head-accepts-unknown-commit] devkit workflow envelope new accepts a --head that names no commit

## 1. Friction / Question (friction, question)

- **Context**: Recording the review envelope of `SPEC-handoff-unit-records` with a hand-typed `--head`.
- **Expectation**: `--head` is the reviewed commit ("diff_scope head commit id (hexadecimal; required for
  revision-ancestor)"), so a value that names no commit in the repository is refused when the envelope is written.
- **Actual**: a mistyped, hexadecimal but non-existent abbreviation was written as is, and `devkit workflow envelope
  check` reported the envelope valid. The mistake surfaced only by rereading the file; a revision check would catch it
  much later, or a stale-head comparison would misread it.
- **Workaround (or Interpretation Chosen)**: corrected the uncommitted envelope to the full commit id before
  committing it.
- **Suggestion**: resolve `--head` (and `--base`) with `git rev-parse --verify <rev>^{commit}` in `envelope new` when
  the workspace is a Git repository, and store the full id; refuse an unknown revision with `[FIX]`.

## Evidence

```text
$ devkit workflow envelope new --unit specs/2026-10/20261015-smoke-check --kind review --stage review-refine \
    --summary x --base HEAD --head 871987c8          # no such commit in the repository
[ENVELOPE: specs/2026-10/20261015-smoke-check/envelopes/review-01.yaml kind=review seq=01 status=completed open_findings=0]
$ devkit workflow envelope check --unit specs/2026-10/20261015-smoke-check
[OK: 1 envelopes]
```
