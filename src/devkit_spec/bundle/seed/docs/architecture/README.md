# Architecture Documentation

System blueprint directory rendering C4 Model diagrams via Mermaid on top of arc42 structure.

## 1. File Naming & Numbering Conventions

- Fixed Chapter Documents: `ARCH-<NN>[-<n>]-<slug>.md`. `<NN>` is the arc42 chapter number and `<n>` is an optional sub-document number (1-9). Numbers indicate reading order rather than allocation sequence; use only the chapters listed below.
- Supplementary Documents: Deep-dive documents independent of chapters are named `ARCH-<slug>.md` without a number, linked from relevant chapters.
- Frontmatter `id` matches the file stem, verified by `RULE-id-convention`.

| NN | arc42 Chapter | Document in this Directory |
| :--- | :--- | :--- |
| 01 | Introduction and Goals | Background, Goals, Non-Goals, Stakeholders |
| 02 | Architecture Constraints | (As needed) |
| 03 | System Scope and Context | C4 L1 Context, External Interfaces |
| 04 | Solution Strategy | (As needed) |
| 05 | Building Block View | `05-1` Containers (C4 L2), `05-2` Components (C4 L3) |
| 06 | Runtime View | Core scenario sequence diagrams |
| 07 | Deployment View | Deployment & runtime environments |
| 08 | Cross-cutting Concepts | Cross-cutting concerns (logging, security, etc.) |
| 09 | Architecture Decisions | Managed by `../decisions/` (No ARCH file) |
| 10 | Quality Requirements | (As needed) |
| 11 | Risks and Technical Debts | (As needed) |
| 12 | Glossary | Managed by `../glossary.md` (No ARCH file) |

## 2. Frontmatter Schema

```yaml
---
id: ARCH-03-context        # Matches file stem
title: Document Title
status: active             # draft | active | deprecated
---
```
