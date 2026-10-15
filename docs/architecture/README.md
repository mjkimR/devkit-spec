# Architecture Documentation

The architecture of devkit-spec in arc42 chapters, with C4 diagrams in Mermaid. Each chapter is an ID-bearing
document; refer to it by its ID (`devkit spec resolve <ID>` gives the path).

## 1. Chapters

| NN | arc42 Chapter | Document | Covers |
| :--- | :--- | :--- | :--- |
| 01 | Introduction and Goals | `ARCH-01-introduction-and-goals` | Mission, goals, non-goals, quality goals, stakeholders |
| 02 | Architecture Constraints | (none) | Constraints live in `ARCH-08-cross-cutting` and the decisions |
| 03 | System Scope and Context | `ARCH-03-context` | C4 L1, the boundary with devkit, external systems |
| 04 | Solution Strategy | (none) | `ADR-rebuild-spec-on-devkit` and `ADR-mount-under-the-devkit-command-line` hold it |
| 05 | Building Block View | `ARCH-05-1-containers`, `ARCH-05-2-components` | C4 L2: the wheel's bundle, command group and library; C4 L3: the package modules |
| 06 | Runtime View | `ARCH-06-runtime-view` | Spec bundle start, proposal handoff, commit gate, worktree lifecycle |
| 07 | Deployment View | `ARCH-07-deployment` | Installation, files on disk, development environment, CI |
| 08 | Cross-cutting Concepts | `ARCH-08-cross-cutting` | Output contract, codes, configuration, rule targeting, devkit surface, paths, language, platforms |
| 09 | Architecture Decisions | `docs/decisions/` | ADRs (`devkit spec list decision`) |
| 10 | Quality Requirements | (none) | Quality goals in `ARCH-01-introduction-and-goals`; contracts in the capabilities |
| 11 | Risks and Technical Debts | (none) | |
| 12 | Glossary | [glossary.md](../glossary.md) | |

## 2. Conventions

- Chapter documents are `ARCH-<NN>[-<n>]-<slug>.md`: `<NN>` is the arc42 chapter number (never 09 or 12), `<n>` an
  optional sub-document number (1-9). Numbers give reading order, not allocation order.
- A deep-dive document outside the chapters is `ARCH-<slug>.md` without a number, linked by ID from its chapter.
- The frontmatter `id` equals the file stem (`RULE-id-convention`); `summary` is required (`RULE-document-summary`).

```yaml
---
id: ARCH-03-context        # the file stem
title: System Scope & Context
summary: <one or two English sentences: what the document defines>
status: active             # draft | active | deprecated
created_at: 2026-10-13
---
```
