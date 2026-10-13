# RULE-traceability-link

Stories and capabilities have an M:N relationship recorded on both sides by exact document ID. A story
(`docs/stories/<area>/US-<slug>.md`) lists its capabilities in `capabilities`; a capability
(`docs/capabilities/<area>/CAP-<AREA>-<slug>.md`) lists its stories in `stories`. Paths and partial IDs never match.

See what a document links with `devkit spec refs <ID>` and what links it with `devkit spec refs <ID> --direction in`.

## Violations

- A story lists a capability that does not list the story in `stories`, or a capability lists a story that does not
  list the capability in `capabilities`. The document missing the reverse link is reported. When the run does not
  target that document (a commit that changes only the story, say), the one-sided link is reported on the document
  that declares it instead.

Add the source ID to the target's list, or run `devkit rules fix` (name the target document when the run targets
only the source: `devkit rules fix docs/capabilities/<area>/CAP-<AREA>-<slug>.md`). The fix appends the ID to the
list, creating the field when it is absent and keeping a flow `[...]` or block list in its style. It respects
`--dry-run`, is idempotent, and never guesses: a link is fixed only when both IDs are declared by exactly one
document and the field is absent or a list, and only in the documents the run targets.

Missing targets, duplicate IDs, wrong ID kinds and malformed fields are reported by `RULE-document-reference`.

## Scope

Materials are not checked. Only the repository-wide `docs/stories/` and `docs/capabilities/` trees are read;
namespace documents (`docs/packages/<name>/...`) are not supported yet. Like every devkit rule, a violation is
reported only in the files the run targets: a commit checks the files it changes, `devkit rules check` without
targets the whole workspace.

```yaml
# docs/stories/billing/US-pay-invoice.md
capabilities:
  - CAP-BILLING-invoices
```

```yaml
# docs/capabilities/billing/CAP-BILLING-invoices.md
stories:
  - US-pay-invoice
```
