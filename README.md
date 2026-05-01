# Exercise 01 — Node Registry (FastAPI + PostgreSQL + Docker Compose)

> **Distributed Systems & Parallel Programming — UNLu 2026**
>
> This exercise is part of the continuous assessment for the course. Throughout the semester you will solve hands-on exercises that are graded automatically. Each exercise builds on the previous one and reinforces concepts you will need for the major assignments: REST APIs, Docker, Compose, Kubernetes, messaging, etc.
>
> The goal is not just to "pass the tests" but to understand what you are building. Tests validate the output — comprehension is on you.

## Course topics covered

This exercise covers the following topics from the course syllabus:

| Unit | Topic | How it applies here |
|------|-------|-------------------|
| **U1.6** | Client-Server communication, HTTP, JSON | You build a REST API that nodes use to register and discover peers |
| **U1.8** | Remote Procedure Call (RPC) | REST endpoints as the modern equivalent of RPC — a client invokes a remote operation and gets a structured response |
| **U4.3** | Docker: images, Dockerfile, Docker Hub | You containerize the API following production best practices |
| **U4.3** | Docker Compose: multi-container applications | You orchestrate the API + PostgreSQL as a multi-service stack |
| **U5.1** | DevOps and CI/CD | Automated grading simulates a CI pipeline — your code must pass tests on every push |

### What you will practice

- Designing a **REST API** with proper HTTP methods, status codes, and JSON schemas
- Using **SQLAlchemy** with PostgreSQL for persistent storage in a distributed service
- Writing a **production-ready Dockerfile** (non-root, slim image, layer caching)
- Composing **multi-container applications** with Docker Compose
- Understanding **service discovery** — this Node Registry is the foundation pattern behind tools like Consul, etcd, and Eureka

---

## Automated grading

Every time you push to your fork, we will run a set of hidden tests that validate whether you have included all the required details and covered the expected behavior. Within 10 minutes you will receive a ✅/❌ comment directly on your latest commit.

Hidden tests cover:
- All 6 endpoints with edge cases and validation errors
- PostgreSQL integration (real DB, not mocked)
- Dockerfile best practices: non-root user, slim image, pinned version (no `:latest`), `EXPOSE`, `HEALTHCHECK`, multi-stage build, layer caching, no hardcoded secrets, image under 200MB
- `.dockerignore` exists and excludes `.git`
- docker-compose.yml: 2+ services, `depends_on`, port mapping, no hardcoded passwords
- Data persists between requests
- Soft delete behavior (status = inactive, not hard delete)

You have a maximum of **5 submissions**. It's a nice challenge — let's build it together.

**Deadline: Friday, April 10, 2026 at 23:59 UTC-3** (3 late days allowed with penalty)

---

## Context

In a distributed system, nodes need a way to discover each other. A **Node Registry** is a central service where nodes register themselves and query for peers — like the Node D from TP1, but built as a production-ready microservice.

## Objective

Build a REST API with **FastAPI** backed by **PostgreSQL**, containerized with **Docker Compose**.

## How to submit

1. **Fork** this repo
2. Implement the solution
3. Run locally: `docker compose up --build`
4. Verify: `curl http://localhost:8080/health`
5. Push to your fork — grading is automatic (within 10 minutes)

---

## Endpoints

| Method | Path | Description | Success | Error |
|--------|------|-------------|---------|-------|
| `GET` | `/health` | Health check with DB status | 200 | - |
| `POST` | `/api/nodes` | Register a new node | 201 | 409 (duplicate), 422 (validation) |
| `GET` | `/api/nodes` | List all active nodes | 200 | - |
| `GET` | `/api/nodes/{name}` | Get a node by name | 200 | 404 |
| `PUT` | `/api/nodes/{name}` | Update a node's host/port | 200 | 404, 422 |
| `DELETE` | `/api/nodes/{name}` | Soft-delete a node (set status=inactive) | 204 | 404 |

### `GET /health`

```json
{
  "status": "ok",
  "db": "connected",
  "nodes_count": 3
}
```

`nodes_count` is the number of **active** nodes (status = "active").

### `POST /api/nodes`

Request body:
```json
{
  "name": "node-alpha",
  "host": "192.168.1.10",
  "port": 8081
}
```

Response (201):
```json
{
  "id": 1,
  "name": "node-alpha",
  "host": "192.168.1.10",
  "port": 8081,
  "status": "active",
  "created_at": "2026-04-01T12:00:00",
  "updated_at": "2026-04-01T12:00:00"
}
```

Validations:
- `name`: required, unique → 409 if duplicate
- `host`: required, non-empty
- `port`: required, integer between 1 and 65535

### `GET /api/nodes`

Returns an array of **all** nodes (including inactive).

### `GET /api/nodes/{name}`

Returns the node or 404 with `{"detail": "Node not found"}`.

### `PUT /api/nodes/{name}`

Request body (partial update — any combination of fields):
```json
{
  "host": "10.0.0.5",
  "port": 9090
}
```

Returns the updated node or 404.

### `DELETE /api/nodes/{name}`

**Soft delete**: sets `status` to `"inactive"` and returns 204 (no body). Returns 404 if node doesn't exist.

---

## Data Model

Table: `nodes`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | SERIAL | PRIMARY KEY |
| `name` | VARCHAR | UNIQUE, NOT NULL |
| `host` | VARCHAR | NOT NULL |
| `port` | INTEGER | NOT NULL |
| `status` | VARCHAR | DEFAULT 'active' |
| `created_at` | TIMESTAMP | DEFAULT NOW() |
| `updated_at` | TIMESTAMP | DEFAULT NOW() |

---

## What to deliver

| File | Description |
|------|-------------|
| `src/app.py` | FastAPI application with all endpoints |
| `src/models.py` | SQLAlchemy model for the `nodes` table |
| `src/database.py` | Database connection and session management |
| `src/schemas.py` | Pydantic schemas for request/response validation |
| `Dockerfile` | Production-ready (non-root, slim image, EXPOSE 8080) |
| `docker-compose.yml` | API service + PostgreSQL service |
| `requirements.txt` | Python dependencies |
| `.env.example` | Example environment variables (do NOT commit `.env`) |

---

## Docker requirements

### Dockerfile

Your Dockerfile must follow **production best practices**. All of these are tested:

| # | Requirement | Why |
|---|-------------|-----|
| 1 | **Pin base image version** — use `python:3.14-slim`, never `:latest` | Reproducible builds; `:latest` changes without notice |
| 2 | **Non-root user** — add a `USER` directive (not root, not uid 0) | Security: if the container is compromised, the attacker has limited permissions |
| 3 | **Multi-stage build** — use 2+ `FROM` instructions | Smaller final image: build deps stay in the builder stage |
| 4 | **Layer caching** — `COPY requirements.txt` + `RUN pip install` BEFORE `COPY . .` | Avoids reinstalling all deps on every code change |
| 5 | **`EXPOSE 8080`** | Documents the port; required for some orchestrators |
| 6 | **`HEALTHCHECK`** | Allows Docker/Compose/K8s to detect unhealthy containers |
| 7 | **No hardcoded secrets** — no `ENV PASSWORD=...` or `ENV SECRET_KEY=...` | Secrets belong in env vars at runtime, not baked into the image |
| 8 | **Final image under 200MB** | Slim images deploy faster and have smaller attack surface |

### .dockerignore

Create a `.dockerignore` file that excludes at minimum:

```
.git
__pycache__
*.pyc
.env
venv/
.venv/
```

This prevents unnecessary files from being sent to the Docker build context.

### docker-compose.yml

| Requirement | Details |
|-------------|---------|
| **Two services** | `api` (your app) and `db` (PostgreSQL) |
| **DB image** | `postgres:17-alpine` |
| **depends_on** | `api` must depend on `db` |
| **Port mapping** | `api` exposes port `8080` on the host |
| **No hardcoded passwords** | Use `env_file` or `${VAR}` references, not plain text passwords in the YAML |
| **Environment variables** | Pass `DATABASE_URL` to the API service |

### .env.example

```
POSTGRES_USER=noderegistry
POSTGRES_PASSWORD=noderegistry
POSTGRES_DB=noderegistry
DATABASE_URL=postgresql://noderegistry:noderegistry@db:5432/noderegistry
```

Copy to `.env` before running. Never commit `.env` to git.

---

## Running locally

```bash
# Start the stack
docker compose up --build -d

# Check health
curl http://localhost:8080/health

# Register a node
curl -X POST http://localhost:8080/api/nodes \
  -H "Content-Type: application/json" \
  -d '{"name": "node-alpha", "host": "192.168.1.10", "port": 8081}'

# List nodes
curl http://localhost:8080/api/nodes

# Stop
docker compose down -v
```

