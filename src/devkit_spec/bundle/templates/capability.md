---
id: CAP-<AREA>-<slug>
title: Capability Title (e.g., Payment Authorization and Cancellation)
summary: "One or two English sentences: what this capability provides and its boundary"   # required, English (RULE-document-summary); quote it, it may contain ": "
area: <area>              # Must match parent directory docs/capabilities/<area>/ (auth | billing | order, etc.)
status: draft             # draft | active | deprecated
stories:
  - US-<slug>
---

# [CAP-<AREA>-<slug>] Capability Title

<!-- File path is docs/capabilities/<area>/CAP-<AREA>-<slug>.md and id matches file name. <AREA> is uppercase abbreviation of area; no sequence numbers. -->

## 1. Summary
<!-- Summarize core purpose and value of this capability in 2-3 sentences -->

## 2. Scope & Boundary
- **In-Scope**: Explicit scope and responsibilities handled by this capability.
- **Out-of-Scope**: Responsibilities handled by other capabilities or external systems (Non-Goals: Scope Excluded, with Rationale and When to Reconsider when they help).

## 3. Business Rules & Policies
<!-- Core business rules. Use RFC 2119 keywords (MUST, SHOULD, MAY) for normative force -->
1. **[Rule 1 Name]**: <!-- Rule specification and RFC 2119 keyword (MUST). Violation requires prior ADR -->
2. **[Rule 2 Name]**: <!-- Rule specification and RFC 2119 keyword (MUST). -->
3. **[Rule 3 Name]**: <!-- Rule specification and RFC 2119 keyword (SHOULD NOT). -->

## 4. Interfaces & Data Contracts
- **Primary API Endpoints / Events**:
  - `POST /api/v1/...`
  - `event.topic.name` (Pub/Sub event)
- **Core Data Schema / Entity References**:
  - Relevant tables or entities
