# packages/ingestion

Server-side Axon ingestion pipeline. Runs as a GCP Cloud Run Job triggered by Cloud Tasks. Locally runs as a Docker container invoked by the API's local task queue.

## What It Does

1. Receives a job payload: `{project_id, repo_url, branch, clone_token}`
2. Shallow clones the repo to a temp directory
3. Runs `axon analyze .` (produces KuzuDB graph in `.axon/`)
4. Queries Axon's graph via `axon cypher` CLI for symbols, calls, imports, heritage, dead code
5. Maps Axon output to the PostgreSQL schema (entities + relationships)
6. Generates embeddings for new/changed entities via fastembed
7. Upserts everything into Postgres
8. Logs the ingestion as an activity entry
9. Cleans up temp directory

## Structure

```
src/
  main.py                  # Entry point — receives job payload, orchestrates pipeline
  axon_runner.py           # Runs axon CLI commands, parses output
  extractor.py             # Queries Axon graph, extracts symbols/edges
  mapper.py                # Maps Axon types to our entity/relationship schema
  upserter.py              # Batch upserts to PostgreSQL via asyncpg
  embeddings.py            # fastembed wrapper (same model as API)
  config.py                # Pydantic settings
tests/
  conftest.py
  test_extractor.py        # Tests with mock Axon CLI output
  test_mapper.py           # Tests type mapping logic
  test_upserter.py         # Tests SQL generation (against test DB)
  fixtures/                # Sample Axon JSON output for testing
    sample_symbols.json
    sample_calls.json
    sample_heritage.json
```

## Key Details

- Axon is a Python package: `pip install axoniq`
- Axon CLI: `axon analyze .` indexes the repo, `axon cypher "MATCH ..."` queries the graph
- Axon uses KuzuDB internally — we don't access KuzuDB directly, only via `axon cypher`
- Axon generates embeddings with bge-small-en-v1.5 (384-dim) — we use the same model via fastembed
- Timeout: 5 minutes max per job (most repos take 5-30 seconds)
- Temp directory: clone to `/tmp/sc-<job-id>/`, delete after completion regardless of success/failure

## Testing

```bash
pytest                     # all tests (Axon CLI is mocked)
pytest -m integration      # needs postgres
```

Never call real Axon in tests. Use fixtures with sample JSON output.
The `axon cypher --json` flag returns JSON arrays — fixture files mirror this format.

## Environment Variables

```
DATABASE_URL=postgresql://canvas:canvas@localhost:5432/semantic_canvas
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
CLONE_TIMEOUT=120
ANALYZE_TIMEOUT=300
```
