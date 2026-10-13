---
name: contract-authoring
description: Read before authoring or reviewing specifications, acceptance criteria, policies, instructions, rules or workflows. Defines normative wording, measurable contracts, non-goals, examples and policy exceptions.
---

# Contract Authoring

## Normative Wording

- Avoid mathematical inequality priority slogans such as `Speed > Quality`; they can be read as absolute priority at the expense of the other operand.
- Use RFC 2119 keywords (`MUST`, `SHOULD`, `MAY`) with explicit boundaries and thresholds.
- Reserve MUST and MUST NOT for violations caught by a check/review or hard to undo, such as committing a secret, weakening a contract without approval or editing an accepted ADR. Working habits are SHOULD or "when it helps".
- Record architecture decisions and lasting policy changes overriding a MUST in an ADR. State a one-off exception within an approved scope in the review or final report.

## Scope and Verifiability

- Unstated assumptions are not permissions. Respect MUST NOT constraints and declared Non-Goals.
- A Non-Goal states its **Scope Excluded**: exactly what will not be built. Add **Rationale** and **When to Reconsider** only when they help later decisions; do not fill them for form.
- Replace vague qualifiers such as "handle errors properly" or "ensure high performance" with exact, checkable contracts for the interface: exit codes, status/error codes, output lines, payload structures and Given/When/Then acceptance scenarios. Each scenario carries an ID that tasks cover (`RULE-task-coverage`).
- Documentation code snippets and JSON payloads are non-normative examples unless explicitly designated as normative schemas.
