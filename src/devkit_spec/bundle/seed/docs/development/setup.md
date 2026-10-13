# Local Setup Guide

A guide for team members and AI coding agents to clone, build, and run the project locally.

---

## 1. Prerequisites
<!-- Specify required runtimes and tools -->
- **Language / Runtime**: <!-- e.g., Python >= 3.12, Node.js >= 20.x, Go >= 1.24 -->
- **Package Manager**: <!-- e.g., uv, pnpm, cargo, etc. -->
- **Infrastructure**: <!-- e.g., Docker & Docker Compose -->

---

## 2. Clone Repository & Install Dependencies
```bash
# 1. Clone repository
git clone <repository-url>
cd <repository-directory>

# 2. Install dependencies
<package-install-command>
```

---

## 3. Environment Variables Configuration (.env)
1. Copy `.env.example` to `.env.local`:
   ```bash
   cp .env.example .env.local
   ```
2. Primary environment variables:
   | Variable | Required | Default (Local) | Description |
   | :--- | :--- | :--- | :--- |
   | `DATABASE_URL` | Yes | <!-- Local connection string --> | Local database connection URL |
   | `SECRET_KEY` | Yes | <!-- Default secret --> | Secret key for signing/encryption |

---

## 4. Run Local Infrastructure & Application
```bash
# Start local infrastructure (e.g., Docker Compose)
docker compose up -d

# Apply DB migrations
<db-migrate-command>

# Start application server
<app-start-command>

# Run tests
<test-run-command>
```
