---
name: db-patterns
description: PostgreSQL and pgvector query patterns for Semantic Canvas. Use when working on repositories, writing SQL queries, implementing search, blast radius traversal, or database migrations. Covers asyncpg usage, pgvector semantic search, recursive CTEs, and the repository pattern.
---

# Database Patterns

## When to Use
- Working in `packages/api/src/repositories/`
- Writing or modifying SQL queries
- Implementing search (keyword + semantic)
- Implementing blast radius (recursive CTE)
- Creating migrations

## Repository Pattern

```python
class EntitiesRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def list_by_project(self, project_id: UUID, kind: str | None = None) -> list[dict]:
        query = "SELECT * FROM entities WHERE project_id = $1"
        params: list = [project_id]
        if kind:
            query += " AND kind = $2"
            params.append(kind)
        query += " ORDER BY name"
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
```

## Semantic Search (pgvector)

```sql
-- Find entities similar to a query embedding
SELECT id, name, kind, metadata,
       1 - (embedding <=> $1::vector) AS similarity
FROM entities
WHERE project_id = $2
  AND embedding IS NOT NULL
ORDER BY embedding <=> $1::vector
LIMIT $3;
```

Generate the query embedding in Python:
```python
from fastembed import TextEmbedding
model = TextEmbedding("BAAI/bge-small-en-v1.5")
embedding = list(model.embed([query_text]))[0].tolist()
```

## Keyword Search (pg_trgm)

```sql
-- Fuzzy name search
SELECT id, name, kind, similarity(name, $1) AS score
FROM entities
WHERE project_id = $2
  AND name % $1  -- trigram similarity > threshold
ORDER BY score DESC
LIMIT $3;
```

## Combined Search (keyword + semantic)

Run both queries, merge results by ID, rank by combined score:
```python
async def search(self, project_id: UUID, query: str, limit: int = 10):
    embedding = self._embed(query)
    # Run both concurrently
    semantic, keyword = await asyncio.gather(
        self._semantic_search(project_id, embedding, limit * 2),
        self._keyword_search(project_id, query, limit * 2),
    )
    # Merge and rank (reciprocal rank fusion)
    return self._fuse_results(semantic, keyword, limit)
```

## Blast Radius (Recursive CTE)

```sql
-- Forward impact: what does this entity affect?
WITH RECURSIVE blast AS (
    SELECT to_entity_id AS entity_id, 1 AS depth
    FROM relationships
    WHERE from_entity_id = $1 AND project_id = $2

    UNION

    SELECT r.to_entity_id, b.depth + 1
    FROM relationships r
    JOIN blast b ON r.from_entity_id = b.entity_id
    WHERE r.project_id = $2 AND b.depth < $3
)
SELECT DISTINCT e.id, e.name, e.kind, b.depth
FROM blast b
JOIN entities e ON e.id = b.entity_id
ORDER BY b.depth, e.name;
```

## Migration Format

```sql
-- Migration: 002_add_complexity_column
-- Date: 2026-03-18
-- DOWN: ALTER TABLE entities DROP COLUMN IF EXISTS complexity_score;

ALTER TABLE entities ADD COLUMN complexity_score INTEGER;
```

## Rules

- Always use parameterized queries (`$1`, `$2`). Never `f""` or `.format()`.
- Use `asyncpg.Pool` for connection management, not individual connections.
- Return `list[dict]` from repositories (convert `asyncpg.Record` via `dict(row)`).
- Use `INSERT ... ON CONFLICT DO UPDATE` for upserts.
- Embedding column: `vector(384)`. HNSW index: `vector_cosine_ops`.
- Test against a real Postgres instance (Docker), not mocks.
