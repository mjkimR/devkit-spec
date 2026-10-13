---
name: living-spec-writing
description: Read before authoring, editing or reviewing docs/ or specs/ documents. Defines current-state writing, history placement, completed-spec treatment, story-capability traceability and internal document references.
---

# Living Spec Writing

## Current State and History

- `docs/` is a current-state ledger, not a changelog. Rewrite affected statements in place when behavior or a decision changes, citing the source ID (ADR, MAT, SPEC) where the reason matters.
- Do not add dated headings, correction notes ("corrected on ...", "changed from X to Y") or history sections to capabilities, stories, architecture, development guides, the glossary or proposals.
- Change history belongs in Git, append-only ADRs (replace through `supersedes`) and dated `docs/materials/`. Frontmatter dates and ADR/material dates are metadata, not prose history.
- Temporary checklists and PR task lists belong in `specs/`, never directly in `docs/`.

## Completed Specs and Traceability

- A spec with `status: completed` remains in place as work history. It is not a default discovery or orientation target; read `docs/capabilities/` and `docs/stories/` for the current contract. Later behavior changes start a new spec. Editing a completed spec is not prohibited.
- Stories and capabilities form an orthogonal M:N relationship. Link them through YAML `stories:` in capabilities and `capabilities:` in stories, both ways (`RULE-traceability-link`); do not physically nest either inside the other.

## References

- Refer to ID-bearing internal documents with full IDs in prose and exact IDs in relationship fields; omit Markdown paths.
- Keep external URLs, images, code paths and documents without IDs as ordinary links. Code examples, non-ID inline code and H1 self IDs are not reference edges.
- Use `devkit spec resolve <ID> [<ID>...]` to find repository-relative paths and `devkit spec refs <ID> --direction out|in` for reference discovery; `RULE-document-reference` checks every reference.
