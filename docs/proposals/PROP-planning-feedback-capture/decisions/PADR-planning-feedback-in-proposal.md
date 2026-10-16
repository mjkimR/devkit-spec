---
id: PADR-planning-feedback-in-proposal
title: Keep Planning feedback with its proposal
summary: "Planning writes feedback inside its proposal boundary. Handoff carries open observations into the spec; deletion without handoff preserves open observations in the global backlog."
proposal: PROP-planning-feedback-capture
status: draft
created_at: 2026-10-16
---

# [PADR-planning-feedback-in-proposal] Keep Planning feedback with its proposal

## 1. Context

Planning workers currently write only inside their proposal. Global feedback would require expanding every worker's
write allowance. Proposal-local feedback fits that boundary, but generic handoff currently moves extra files into
historical materials. A rejected or decomposed proposal can be deleted without handoff.

## 2. Options

| Option | Advantage | Cost |
| --- | --- | --- |
| Global month-level backlog | Survives every proposal ending without relocation | Adds a second write root to Planning |
| Proposal-local, explicit retirement (recommended) | One activity directory and one commit stream; open work follows the spec | Needs path-rule support, handoff routing and preservation before deletion |
| Proposal-local, generic materials move | Reuses handoff unchanged | Open feedback becomes historical material rather than actionable spec feedback |

## 3. Proposed decision

Use `docs/proposals/PROP-<slug>/feedback/<name>.md`, with `FB-<name>` and existing feedback frontmatter. Planning's
worker write boundary stays unchanged. At handoff, `status: open` files move to the new spec's `feedback/`; files with
`promoted`, `dismissed` or `forwarded` status follow the existing preserved-materials path. No status is changed.

On rejection or return for decomposition, keep the feedback in the proposal until it would be deleted. The Host
performing deletion moves open observations to `specs/<current-month>/feedback/<today>-<name>.md` first, in the same
commit. Do not duplicate observations across decomposed children. Settled records remain available in Git history.
Invalid input, collision or an unsafe path prevents relocation and deletion; never guess that malformed feedback is
settled. Before deleting a proposal without handoff, preserve source Git revision/path context and convert only
historical evidence mentions of retired proposal/PADR/settled-feedback IDs to the existing strikethrough convention.
Update relative links for moved feedback and validate current document references. An unresolved live dependency
prevents deletion; it is not reclassified as historical evidence. Handoff relocation participates in its existing
validation, rewrite and rollback guarantees.

## 4. Consequences

- Feedback discovery/deduplication includes live proposal-local feedback, including rejected proposals awaiting cleanup.
- Path validation and relevant guides expand; no new document kind, status, general storage root or permission is added.
- Feedback IDs, statuses and observation dates survive moves. Names are selected unused across the repository.
- Strategy 01 §6.2 is updated after acceptance and before handoff. Capture/sweep timing is specified by
  `PROP-planning-feedback-capture`; this PADR decides storage and retirement only.
