---
id: ARCH-05-1-containers
title: Containers View
status: draft
---

# [ARCH-05-1-containers] Containers View

- **arc42**: §5 Building Block View, Level 1 / C4 Model Level 2 (Container)

---

## 1. C4 Level 2: Container Diagram
<!-- High-level deployable execution units (Web App, API Server, Worker, Database) and communication protocols -->

```mermaid
flowchart LR
    subgraph Clients ["Clients Layer"]
        Web["Web Frontend<br>[Container: SPA / Web App]"]
    end

    subgraph Backend ["Backend Services Layer"]
        API["API Server<br>[Container: Web API Framework]"]
        Worker["Worker Process<br>[Container: Background Worker]"]
    end

    subgraph Data ["Data Layer"]
        DB[("Database<br>[Container: RDBMS / NoSQL]")]
        Cache[("Cache / Message Broker<br>[Container: In-Memory / Broker]")]
    end

    Web -->|"HTTPS / JSON"| API
    API -->|"TCP / SQL"| DB
    API -->|"Enqueue"| Cache
    Worker -->|"Dequeue"| Cache
    Worker -->|"TCP / SQL"| DB
```

---

## 2. Container Inventory & Technology Stack
| Container | Role & Responsibilities | Technology Stack | Deployment Runtime |
| :--- | :--- | :--- | :--- |
| **`web`** | User interface presentation | <!-- e.g., Svelte 5 / React / Vue --> | Static Hosting / CDN |
| **`api`** | Business logic & API serving | <!-- e.g., Go / Python FastAPI / Node --> | Container (Docker / Cloud Run) |
| **`worker`** | Asynchronous background processing | <!-- Tech stack --> | Background Worker |
| **`db`** | Persistent relational data store | <!-- e.g., PostgreSQL / MySQL --> | Managed Database |
| **`cache`** | In-memory cache & message broker | <!-- e.g., Redis --> | Managed In-Memory Store |

---

## 3. Inter-Container Communication & Contracts
- **Client <-> API Server**: RESTful API / GraphQL (OpenAPI contract), Bearer Token authentication.
- **API Server <-> Database**: Connection pooling, ORM or query builder.
- **API Server <-> Worker**: Async task queue or pub/sub messaging.
