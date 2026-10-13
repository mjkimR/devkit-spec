---
id: ARCH-03-context
title: System Scope & Context
status: draft
---

# [ARCH-03-context] System Scope and Context

- **arc42**: §3 System Scope and Context / C4 Model Level 1 (System Context)
- Background, goals, and stakeholders reside in `ARCH-01-introduction-and-goals`.

---

## 1. C4 Level 1: System Context Diagram
<!-- High-level relationships between system boundaries, actors, and external systems -->

```mermaid
flowchart TD
    User["End User<br>[Person]"] -->|"Requests / Interactions"| System["Target System<br>[Software System]"]
    Admin["Administrator<br>[Person]"] -->|"Management & Monitoring"| System

    System -->|"API Calls"| ExtService["External System<br>[External System]"]
```

---

## 2. External System Interfaces
| External System | Protocol | Data Format | Integration Purpose | Fallback Strategy |
| :--- | :--- | :--- | :--- | :--- |
| <!-- System Name --> | HTTPS / REST | JSON | <!-- Purpose --> | <!-- Failure handling policy --> |
