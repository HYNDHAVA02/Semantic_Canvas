Create a database migration for: $ARGUMENTS

1. Look at existing migrations in `packages/api/src/db/migrations/` to determine the next sequence number
2. Create a new migration file: `NNN_<description>.sql`
3. Write the UP migration (the changes)
4. Add a comment block at the top with the DOWN migration (rollback SQL)
5. Update `packages/api/src/db/schema.sql` to reflect the new state (this file is the canonical schema)
6. If adding columns with embeddings, remember: `vector(384)` and add an HNSW index

Format:
```sql
-- Migration: NNN_<description>
-- Date: YYYY-MM-DD
-- DOWN: <rollback SQL on one line>

<UP migration SQL>
```

After creating, run the migration locally:
```
cd packages/api && python -m src.db.migrate
```
