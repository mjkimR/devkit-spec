---
id: ARCH-07-deployment
title: Deployment View
status: draft
---

# [ARCH-07-deployment] Deployment View

- **arc42**: §7 Deployment View / C4 Model Deployment Diagram

---

## 1. Deployment Topology
<!-- Infrastructure layout, subnets, load balancers, and compute resource configuration for staging and production -->

```mermaid
flowchart TD
    subgraph ClientLayer ["Client Layer"]
        Browser["User Browser / Mobile App"]
    end

    subgraph IngressLayer ["Ingress & CDN"]
        CDN["CDN / SSL Termination / Load Balancer"]
    end

    subgraph ServiceLayer ["Application Cluster"]
        AppNode["API Service Container<br>(Auto-scaling Group)"]
        WorkerNode["Background Worker Container"]
    end

    subgraph DataLayer ["Data Infrastructure"]
        PrimaryDB[("Primary Database<br>(Managed Instance)")]
        CacheStore[("In-Memory Cache / Broker")]
    end

    Browser --> CDN
    CDN --> AppNode
    AppNode --> PrimaryDB
    AppNode --> CacheStore
    WorkerNode --> PrimaryDB
    WorkerNode --> CacheStore
```

---

## 2. Infrastructure Inventory by Environment
| Environment | Compute Platform | Database | Domain / Host Address |
| :--- | :--- | :--- | :--- |
| **Local** | Docker Compose / Local Host | Local Container | `localhost:8000` |
| **Staging** | <!-- Staging compute platform --> | <!-- Staging DB instance --> | <!-- Staging URL --> |
| **Production** | <!-- Production compute platform --> | <!-- Production DB instance --> | <!-- Production URL --> |

---

## 3. Secrets Management & Environment Variables
1. **Never Commit Secrets to Codebase**: API keys and DB credentials must never be committed to Git (`MUST NOT`).
2. **Secret Providers**: Inject secrets securely at runtime via cloud secret managers (AWS Secrets Manager, GCP Secret Manager, Vault).
3. **Local Development**: Use `.env.local` ignored by `.gitignore`.
