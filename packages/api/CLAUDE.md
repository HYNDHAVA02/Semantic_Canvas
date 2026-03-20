# packages/api

FastAPI server. Two interfaces from one service:
1. REST API (dashboard) — standard CRUD endpoints
2. MCP server (AI agents) — 13 tools for querying and writing project knowledge

Deployed as a single Cloud Run service.

## Structure

```
src/
  main.py                    # FastAPI app factory, lifespan, middleware
  config.py                  # Pydantic BaseSettings, reads env vars
  db/
    schema.sql               # Canonical PostgreSQL schema (source of truth)
    migrate.py               # Migration runner
    pool.py                  # asyncpg connection pool setup
    migrations/              # Sequential .sql migration files (001_initial.sql, etc.)
  repositories/              # One per table, raw SQL
    base.py                  # Base repository with pool access
    entities.py
    relationships.py
    decisions.py
    conventions.py
    activity.py
    documents.py
    search.py                # Cross-table semantic + keyword search
  mcp/
    server.py                # MCP protocol handler (stdio + SSE)
    registry.py              # Tool registry — maps tool names to handlers
    tools/                   # One file per tool
      list_entities.py
      get_entity.py
      get_relationships.py
      blast_radius.py
      search.py
      get_decisions.py
      get_conventions.py
      get_recent_activity.py
      get_dead_code.py
      log_decision.py
      log_convention.py
      log_activity.py
      add_entity.py
      add_relationship.py
  rest/
    router.py                # Main FastAPI router, mounts sub-routers
    controllers/
      entities.py
      relationships.py
      decisions.py
      conventions.py
      activity.py
      projects.py
      webhooks.py            # GitHub webhook receiver
    dto/                     # Pydantic request/response models
      entities.py
      relationships.py
      common.py              # Pagination, error responses
  auth/
    middleware.py             # FastAPI middleware: JWT (dashboard) + PAT (agents)
    firebase.py              # Firebase token verification
    pat.py                   # Personal API Token validation
    models.py                # AuthContext(user_id, project_id, role)
  embeddings/
    service.py               # fastembed wrapper, generates vector(384)
  tasks/
    queue.py                 # TaskQueue protocol + LocalTaskQueue + CloudTasksQueue
    handlers.py              # Task handler: dispatch ingestion jobs
  services/
    blast_radius.py          # Recursive CTE logic, used by both MCP + REST
tests/
  conftest.py               # Fixtures: test DB, test client, factories
  test_repositories/
  test_mcp_tools/
  test_rest/
  test_auth/
  factories.py              # Test data factories
```

## Patterns

- Repositories: raw SQL via asyncpg. Every method takes a `conn` (or uses pool). Parameterized queries only.
- MCP tools: thin wrappers. Validate input (Pydantic), call repository, return result. No business logic.
- REST controllers: thin wrappers. Validate DTO, check auth, call repository, return response.
- Shared logic (blast radius, search ranking) lives in `services/`.
- Auth: middleware extracts `AuthContext` from JWT (dashboard) or PAT (agent). All downstream code receives `AuthContext`, never raw tokens.

## Environment Variables

```
DATABASE_URL=postgresql://canvas:canvas@localhost:5432/semantic_canvas
REDIS_URL=redis://localhost:6379
FIREBASE_PROJECT_ID=<your-firebase-project>
TASK_QUEUE_BACKEND=local              # or cloud_tasks
GCP_PROJECT_ID=<your-gcp-project>     # only needed for cloud_tasks
CLOUD_TASKS_QUEUE=<queue-name>        # only needed for cloud_tasks
CLOUD_TASKS_LOCATION=<region>         # only needed for cloud_tasks
INGESTION_SERVICE_URL=<cloud-run-url> # only needed for cloud_tasks
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

## Testing

```bash
pytest                     # unit tests (mocked DB)
pytest -m integration      # integration tests (needs docker postgres)
pytest -k "test_mcp"       # MCP tool tests only
```

Each MCP tool test: seed test DB → call tool via handler → assert response shape and data.
Each repository test: seed test DB → call method → assert SQL executed correctly.
