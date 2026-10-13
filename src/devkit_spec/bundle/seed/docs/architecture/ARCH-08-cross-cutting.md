---
id: ARCH-08-cross-cutting
title: Cross-cutting Concepts
summary: Concepts that apply across the system: security, errors, logging, configuration and conventions.
status: draft
---

# [ARCH-08-cross-cutting] Cross-cutting Concepts

- **arc42**: §8 Cross-cutting Concepts

---

## 1. AI-First SDD Documentation Principles & Normative Levels

### 1.1 Human-Centric Habits vs. AI-First Traps
Traditional documentation assumes human intuition and tacit knowledge, whereas AI agents interpret written instructions literally. Avoid these cognitive traps:

| Human-Centric Habit | AI Agent Risk (Trap) | AI-First SDD Authoring Standard |
| :--- | :--- | :--- |
| **Abstract Priority Slogans** (`A > B`) | Lexicographic over-engineering optimizing A while destroying B | **No inequalities**. Use explicit guardrails and RFC 2119 normative keywords |
| **Qualitative Modifiers** ("properly", "sufficiently") | Ambiguous standards prompting hallucinated mock tests or skipped checks | **Enforce verifiability**. Specify exact HTTP status codes, schemas, and boundaries |
| **Implicit Taboos** | Assuming unstated prohibitions are permitted | **Declare negative constraints**. Specify `MUST NOT` and 3-element Non-Goals |
| **Verbose Rhetoric** | Context window waste and attention dispersion missing core rules | **Fact-first density**. Use concise sentences, bullets, and schema tables |
| **Ambiguous Reference Examples** | Hardcoding dummy values or variable names as permanent rules | **Separate non-normative examples from normative contracts** |

### 1.2 RFC 2119 Normative Levels
Express rule authority explicitly using the following keywords:
- **`MUST` / `MUST NOT`**: Absolute requirements or prohibitions. Violations require a prior ADR.
- **`SHOULD` / `SHOULD NOT`**: Recommended practices. Exceptions require explicit technical justification and trade-off rationale.
- **`MAY`**: Truly optional features or behaviors.

---

## 2. Authentication & Authorization
- **User Authentication**: <!-- e.g., JWT Bearer Token, Session Cookie -->
  - Access Token TTL and transport mechanism
  - Refresh Token TTL and storage policy
- **Machine-to-Machine (M2M)**: <!-- API Key, mTLS, etc. -->
- **Authorization (RBAC / ABAC)**: <!-- Role and permission models -->

---

## 3. Common Error Standards
- **Error Response Format**: RFC 7807 (Problem Details) or consistent JSON error payload schema.
- **HTTP Status Code Mapping**:
  - `400 Bad Request`: Client syntax / validation errors
  - `401 Unauthorized`: Authentication failure (missing / expired token)
  - `403 Forbidden`: Insufficient permissions
  - `404 Not Found`: Target resource not found
  - `409 Conflict`: State conflict (duplicate key, lock contention)
  - `500 Internal Server Error`: Unhandled server-side exception

---

## 4. Observability & Logging
1. **Structured JSON Logging**:
   - Production logs output single-line JSON format (`MUST`).
   - Common fields: `timestamp`, `level`, `trace_id` (or `request_id`), `message`.
2. **PII Masking**:
   - Sensitive personal information (passwords, resident numbers, credit card numbers) must never be logged in plain text (`MUST NOT`).

---

## 5. Transaction Management & Consistency Guarantees
- **Internal Transactions**: ACID transaction boundaries within DB (commit per UseCase boundary).
- **External Transactions**: Compensating transactions or idempotency enforcement for external integrations.
