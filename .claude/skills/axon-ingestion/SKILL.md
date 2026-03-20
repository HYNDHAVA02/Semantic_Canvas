---
name: axon-ingestion
description: Axon code intelligence integration patterns. Use when working on the ingestion pipeline, Axon CLI commands, Cypher queries against Axon's KuzuDB, or mapping Axon output to the PostgreSQL schema. Covers axon analyze, axon cypher, symbol extraction, and the upsert pipeline.
---

# Axon Ingestion Patterns

## When to Use
- Working in `packages/ingestion/`
- Modifying how Axon output maps to entities/relationships
- Adding new data extracted from Axon
- Debugging ingestion failures

## Axon CLI Reference

```bash
axon analyze .                    # Index the repo (produces .axon/ directory)
axon analyze . --full             # Force full rebuild
axon cypher "MATCH ..." --json    # Query the graph, return JSON
axon status                       # Check index status
```

## Key Cypher Queries

### All symbols (functions, classes, modules)
```cypher
MATCH (s:Symbol)
RETURN s.id AS id, s.name AS name, s.kind AS kind,
       s.file AS file, s.line AS line, s.language AS language,
       s.complexity AS complexity, s.is_exported AS is_exported,
       s.community AS community, s.is_dead AS is_dead
```

### Call relationships
```cypher
MATCH (a:Symbol)-[r:CALLS]->(b:Symbol)
RETURN a.id AS from_id, a.name AS from_name,
       b.id AS to_id, b.name AS to_name,
       r.file AS file, r.line AS line
```

### Import relationships
```cypher
MATCH (a:Symbol)-[:IMPORTS]->(b:Symbol)
RETURN a.id AS from_id, a.name AS from_name,
       b.id AS to_id, b.name AS to_name
```

### Inheritance / implementation
```cypher
MATCH (a:Symbol)-[r:INHERITS|IMPLEMENTS]->(b:Symbol)
RETURN a.id AS from_id, a.name AS from_name,
       b.id AS to_id, b.name AS to_name, type(r) AS rel_type
```

## Axon Kind → Entity Kind Mapping

| Axon kind | Our entity kind |
|-----------|----------------|
| function  | function       |
| method    | function       |
| class     | class          |
| module    | module         |
| file      | module         |
| interface | class          |
| type_alias| class          |
| enum      | class          |

## Axon Edge → Relationship Kind Mapping

| Axon edge  | Our relationship kind |
|------------|----------------------|
| CALLS      | calls                |
| IMPORTS    | imports              |
| INHERITS   | inherits             |
| IMPLEMENTS | implements           |

## Upsert Strategy

- Use `INSERT ... ON CONFLICT DO UPDATE` for idempotent upserts
- Unique key: `(project_id, name, kind)` for entities, `(project_id, from_entity_id, to_entity_id, kind)` for relationships
- Merge metadata with `||` operator: `metadata = entities.metadata || EXCLUDED.metadata`
- Update `last_seen_at` on every upsert to track freshness
- After ingestion, mark entities with `source = 'axon'` and `last_seen_at < now() - 1 hour` as `is_active = false`
- Delete stale axon relationships older than 1 hour

## Testing

Never call real Axon CLI in tests. Create fixture JSON files that mirror `axon cypher --json` output.
Test the mapper and upserter independently.
