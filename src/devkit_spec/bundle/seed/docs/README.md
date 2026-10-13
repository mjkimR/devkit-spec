# Documentation Guide

This project manages its documentation based on **Spec-Driven Development (SDD)** and the **arc42 + C4 Model** architectural frameworks.

---

## 1. Documentation Directory Map

| Directory | Focus Area | Description |
| :--- | :--- | :--- |
| **`architecture/`** | System Architecture | System blueprints (C4 L1-L3, runtime sequences, deployment infrastructure, cross-cutting concepts) |
| **`decisions/`** | Architecture Decisions (ADR) | Context and rationale for critical technology selection and structural decisions |
| **`capabilities/`** | System Capabilities (WBS) | Permanent functional capabilities and business rules partitioned by area |
| **`stories/`** | User Stories | User-centric journeys, actor value flows, acceptance criteria (Given-When-Then) |
| **`materials/`** | Reference & Spikes | Technical spikes, benchmarks, external libraries, competitor analysis reports |
| **`development/`** | Development & Collaboration | Local environment setup, Git workflow, commit/PR conventions, CI/CD pipelines |
| **`glossary.md`** | Ubiquitous Glossary | Core domain business and technical ubiquitous terminology definitions |

---

## 2. Interaction Principles Between Documents

1. **Orthogonal M:N Relationship Between Capabilities and Stories**:
   - A user story may traverse multiple functional capability areas.
   - `capabilities/` and `stories/` cross-reference each other via Markdown Frontmatter (`stories:` and `capabilities:`).
2. **Separation of Durable Backbone (`docs/`) and Ephemeral Task Specs (`specs/`)**:
   - `docs/` is the permanent Living Spec maintained throughout the system lifecycle.
   - Sprint/ticket task specifications reside in `specs/` and are archived/cleaned upon completion.
   - Completed work reconciles changed core architecture and rules back into `docs/` (Reconciliation).

---

## 3. Harness Collaboration & Living Spec Governance

1. **AI Agent Collaboration via Skills (`MUST`)**:
   - Use `/spec <intent>` to route engineering tasks, `/spec-next` for orientation, and `/spec-feedback` for capturing friction or improvement observations.
   - Interactive collaboration and multi-step governance workflows are orchestrated via the skill layer.
2. **On-Demand Guidance Loading**:
   - Project-wide coding standards, domain constraints, and architectural guidelines are instructions, listed with their read conditions by `devkit get-context <bundle>` (the spec bundle's own by `devkit get-context spec`).
   - Deterministic checks are rules (`devkit rules check`), occasional procedures are playbooks (the `devkit-playbook` skill).
3. **Living Spec Reconciliation (`MUST`)**:
   - `docs/` is the durable source of truth. Temporary sprint checklists and PR task lists belong in `specs/`.
   - Upon task completion, all changes to contracts, capabilities, and system behaviors must be reconciled into `docs/` via the `spec-sync` skill.

---

## 4. AI-First SDD Authoring Guidelines

AI agents interpret documents with a distinct cognitive structure. Avoid these common anti-patterns:

1. **Avoid Abstract Slogans (`A > B`) -> Use RFC 2119 Normative Keywords**:
   - Absolute inequalities can prompt LLMs to over-optimize A while destroying B.
   - Use explicit guardrails and keywords (`MUST`, `SHOULD`, `MAY`). When exceptions are needed, document an ADR in `decisions/`.
2. **Avoid Vague Qualitative Modifiers -> Define Testable Contracts**:
   - Replace "handle errors properly" or "thorough testing" with verifiable criteria, status codes, and boundary conditions.
3. **Detailed Standards**:
   - Read the `contract-authoring` instruction for normative wording and measurable contracts.
   - Read the `living-spec-writing` instruction for current-state writing, ID references, and history placement rules.
