# [RULE-traceability-link] Bidirectional Story and Capability Links

## 1. Overview

Stories and capabilities have an M:N relationship recorded on both sides by exact document ID. A story
(`docs/stories/<area>/US-<slug>.md`) lists its capabilities in `capabilities`; a capability
(`docs/capabilities/<area>/CAP-<AREA>-<slug>.md`) lists its stories in `stories`. Paths and partial IDs never match.
Both sides are kept so an agent reading either document sees the whole relation without a reverse search.

- **Phase and severity**: `linter`, `error`. Shipped by the `spec` bundle (preset `core`).
- **What is checked**: stories and capabilities under `docs/stories/` and `docs/capabilities/` and under the same
  directories of each package registered in `[[tool.spec.namespaces]]` (`docs/packages/<name>/stories/`,
  `.../capabilities/`); links may cross packages, since IDs are repository-wide. Materials are not checked.
- **Targeting**: the document missing the reverse link is reported when the run targets it. When it does not (a commit
  that changes only the story, say), the one-sided link is reported on the document that declares it instead, so a
  change that adds only one side is caught.

See what a document links with `devkit spec refs <ID>` and what links it with `devkit spec refs <ID> --direction in`.

## 2. Cause of Violation

A story lists a capability that does not list the story in `stories`, or a capability lists a story that does not
list the capability in `capabilities`:

- On the document missing the reverse link, at line 1 (fixable when the fix applies, section 3): `<ID> is missing the
  reverse <story|capability> link to <source ID> (<source path>)`.
- On the declaring document, at the link, when the other one is not targeted: `<source ID> links <ID>, but <path>
  does not list <source ID> in <field>`.

Missing targets, duplicate IDs, wrong ID kinds and malformed fields are reported by `RULE-document-reference`.

## 3. Remediation

- **Autofix**: `devkit rules fix` appends the source ID to the target's list, creating the field (as a block list at
  the end of the header) when it is absent and keeping a flow `[...]` or block list in its style. It respects
  `--dry-run`, is idempotent, and never guesses: a link is fixed only when both IDs are declared by exactly one
  document and the field is absent or a list, and only in the documents the run targets. When the run targets only
  the source, name the target document: `devkit rules fix docs/capabilities/<area>/CAP-<AREA>-<slug>.md`.
- **By hand**: add the source ID to the target's list, or remove the one-sided link when the relation does not hold.
- **Related**: whether a story and a capability belong together is a judgment the rule cannot make; read the
  `spec:living-spec-writing` instruction (Completed Specs and Traceability) before removing a link or adding one the
  fix cannot; `devkit rules explain` prints its path as a `[RELATED: ...]` line.

## 4. Configuration

The rule has no settings. Namespaces come from `[[tool.spec.namespaces]]` in `.devkit/config.toml`; project policy
(`[rules] exclude`, `[rules.severity_overrides]`, `[rules.phase_overrides]`) applies as to every rule.

## 5. Exceptions

There is no inline suppression: a relation either holds on both sides or is removed from both. `[rules] exclude`
removes a file from every rule.

## 6. Example

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
