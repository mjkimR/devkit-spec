---
id: ARCH-05-2-components
title: Components View
summary: The components inside each container and their responsibilities (C4 level 3).
status: draft
---

# [ARCH-05-2-components] Components View

- **arc42**: §5 Building Block View, Level 2 / C4 Model Level 3 (Component)

---

## 1. C4 Level 3: Component Diagram
<!-- Internal layers, modules, and component interactions within key containers (e.g., API Server) -->

```mermaid
flowchart TD
    subgraph Presentation ["Presentation Layer (Router / Controller)"]
        Router["Router / Controller<br>[Component: Endpoints & Request Validation]"]
    end

    subgraph Application ["Application Layer (UseCase / Workflow)"]
        UseCase["UseCase / Workflow<br>[Component: Transaction & Orchestration]"]
    end

    subgraph Domain ["Domain Layer (Domain Service / Entity)"]
        DomainService["Domain Service<br>[Component: Business Logic & Rules]"]
    end

    subgraph Infrastructure ["Infrastructure Layer (Repository / Client)"]
        Repo["Data Repository<br>[Component: DB Access]"]
        ExtClient["External Client<br>[Component: Third-party API Client]"]
    end

    Router --> UseCase
    UseCase --> DomainService
    UseCase --> Repo
    UseCase --> ExtClient
```

---

## 2. Layered Architecture Invariants
Preserve separation of concerns across architectural layers:

1. **Presentation (Router / Controller)**:
   - Request payload validation, HTTP status mapping, dependency injection.
   - Business logic and direct database queries are prohibited (`MUST NOT`).
2. **Application (UseCase / Workflow)**:
   - Use case orchestration, transaction boundaries (Commit / Rollback).
   - Protocol-agnostic logic decoupled from HTTP frameworks (`SHOULD`).
3. **Domain (Domain Service / Entity)**:
   - Pure business rules and domain invariants independent of external infrastructure.
4. **Infrastructure (Repository / Client)**:
   - Concrete implementations for persistence, cache, and external third-party communication.

---

## 3. Codebase Directory Mapping
```text
src/
├── api/             # Routers, Middlewares, Handlers
├── features/        # Feature/domain modules (UseCases & Services)
└── infrastructure/  # DB Repositories, External Clients, Config
```
