# Semantic Canvas

A shared project memory layer for AI coding agents. AI tools (Cursor, Claude Code, Copilot, etc.) connect via MCP to query and write project context — entities, relationships, decisions, conventions, and activity.

## Architecture

Three packages in a monorepo:

- **packages/api/** — FastAPI server. Serves REST (dashboard) + MCP (AI agents) + GitHub webhook receiver. Deployed on GCP Cloud Run.
- **packages/ingestion/** — Axon pipeline. Clones repos, runs `axon analyze`, extracts code relationships, upserts to Postgres. Runs as GCP Cloud Run Job triggered by Cloud Tasks.
- **packages/web/** — Next.js 15 dashboard. Browse, search, edit the knowledge base. Deployed on Vercel.
- **infra/** — Terraform for all GCP infrastructure.

## Stack

- Python 3.12+ for API and ingestion (FastAPI, asyncpg, Pydantic, fastembed)
- TypeScript for dashboard (Next.js 15, Tailwind, React Query)
- PostgreSQL 16 + pgvector (Cloud SQL in prod, Docker locally)
- Redis (Memorystore in prod, Docker locally)
- Cloud Tasks + Cloud Run Jobs for async ingestion (simple queue locally)
- Firebase Auth for dashboard users, Personal API Tokens for agents
- Terraform for GCP infrastructure
- Docker Compose for local development

## Key Commands

```bash
# Local dev
docker compose up -d                  # start postgres + redis
cd packages/api && uvicorn src.main:app --reload  # start API
cd packages/web && pnpm dev           # start dashboard

# Test
cd packages/api && pytest             # API tests
cd packages/api && pytest -m integration  # needs postgres running
cd packages/ingestion && pytest       # ingestion tests
cd packages/web && pnpm test          # dashboard tests

# Lint + type check
cd packages/api && ruff check . && mypy src/
cd packages/ingestion && ruff check . && mypy src/

# Database
cd packages/api && python -m src.db.migrate  # run migrations
cd packages/api && python -m src.db.seed     # seed sample data

# Infrastructure
cd infra && terraform plan            # preview GCP changes
cd infra && terraform apply           # apply GCP changes

# Docker build (same images used locally and in Cloud Run)
docker build -f packages/api/Dockerfile -t semantic-canvas-api .
docker build -f packages/ingestion/Dockerfile -t semantic-canvas-ingestion .
```

## Database

PostgreSQL 16 + pgvector. Schema in `packages/api/src/db/schema.sql`.

Six core tables: `entities`, `relationships`, `decisions`, `conventions`, `activity_log`, `document_chunks`. All have `project_id` for multi-tenancy. Searchable tables have `vector(384)` embedding column (bge-small-en-v1.5 via fastembed).

Raw SQL via asyncpg. Parameterized queries only. Never interpolate user input. Repository pattern — one repository class per table in `packages/api/src/repositories/`.

## MCP Server

Primary product interface. 13 tools (8 read, 5 write). Tool definitions in `packages/api/src/mcp/tools/`. Each tool: validate with Pydantic, call repository, return result. MCP transport: stdio (local agents) and SSE (remote agents).

## Code Conventions

- Python: ruff for linting/formatting, mypy for type checking (strict mode)
- Type hints on all function signatures, no `Any` (use `object` or generics)
- Pydantic models for all external input validation
- Repository pattern: one class per table, raw SQL via asyncpg
- Error handling: return `Result[T, AppError]` pattern, don't raise in business logic
- File naming: snake_case for Python files, kebab-case for TypeScript
- Imports: stdlib → third-party → local (enforce via ruff isort)
- Every public function has a docstring
- Tests co-located as `test_*.py` in `tests/` directory
- Factories for test data, not raw fixtures

## Task Queue Abstraction

`packages/api/src/tasks/queue.py` defines a `TaskQueue` protocol with `enqueue()`. Two implementations:
- `LocalTaskQueue` — runs tasks in-process (local dev)
- `CloudTasksQueue` — enqueues to GCP Cloud Tasks (production)

Swapped via `TASK_QUEUE_BACKEND` env var (`local` or `cloud_tasks`).

## Git Workflow

- Branch from `main`: `feat/`, `fix/`, `refactor/`, `chore/`
- Conventional commits: `feat: add blast-radius tool`
- PRs require passing CI (lint + typecheck + test)
- Squash merge to main
- CI deploys to Cloud Run on merge to main

## What NOT to Do

- Don't add SQLAlchemy or any ORM — raw SQL via asyncpg only
- Don't add Celery or any Python task queue — use the TaskQueue abstraction (local queue or Cloud Tasks)
- Don't build a graph visualization / canvas UI — dashboard is simple CRUD
- Don't run Axon locally or in tests — mock Axon output in tests
- Don't use `Any` type — use `object`, `Unknown`, or proper generics
- Don't put business logic in MCP tools or REST controllers — logic lives in repositories or service classes
- Don't store secrets in code or .env files in production — use Secret Manager
