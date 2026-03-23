"""Entities repository — CRUD + search for the entities table."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.repositories.base import BaseRepository, _to_pgvector


class EntitiesRepository(BaseRepository):
    """Data access for the entities table."""

    async def list_by_project(
        self,
        project_id: UUID,
        kind: str | None = None,
        source: str | None = None,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """List entities with SQL pagination. Returns (rows, total)."""
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2

        if kind:
            conditions.append(f"kind = ${idx}")
            params.append(kind)
            idx += 1

        if source:
            conditions.append(f"source = ${idx}")
            params.append(source)
            idx += 1

        if active_only:
            conditions.append("is_active = true")

        where = " AND ".join(conditions)

        total_row = await self._fetch_one(
            f"SELECT count(*) AS cnt FROM entities WHERE {where}", *params
        )
        total = total_row["cnt"] if total_row else 0

        params.append(limit)
        params.append(offset)
        query = f"""
            SELECT id, name, kind, source, source_ref, metadata,
                   is_active, last_seen_at, created_at, updated_at
            FROM entities
            WHERE {where}
            ORDER BY name
            LIMIT ${idx} OFFSET ${idx + 1}
        """
        rows = await self._fetch_all(query, *params)
        return rows, total

    async def get_by_name(
        self, project_id: UUID, name: str
    ) -> dict[str, Any] | None:
        """Get a single entity by name within a project."""
        return await self._fetch_one(
            """
            SELECT id, name, kind, source, source_ref, metadata,
                   is_active, last_seen_at, created_at, updated_at
            FROM entities
            WHERE project_id = $1 AND name = $2
            ORDER BY is_active DESC
            LIMIT 1
            """,
            project_id,
            name,
        )

    async def get_by_id(self, entity_id: UUID) -> dict[str, Any] | None:
        """Get a single entity by ID."""
        return await self._fetch_one(
            """
            SELECT id, project_id, name, kind, source, source_ref, metadata,
                   is_active, last_seen_at, created_at, updated_at
            FROM entities
            WHERE id = $1
            """,
            entity_id,
        )

    async def create(
        self,
        project_id: UUID,
        name: str,
        kind: str,
        source: str = "manual",
        source_ref: str | None = None,
        metadata: dict[str, Any] | None = None,
        embedding: list[float] | None = None,
    ) -> dict[str, Any]:
        """Create a new entity or update if it already exists."""
        import json

        meta_json = json.dumps(metadata or {})

        return await self._fetch_one(
            """
            INSERT INTO entities (project_id, name, kind, source, source_ref, metadata, embedding)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::vector)
            ON CONFLICT (project_id, name, kind)
            DO UPDATE SET
                source_ref = COALESCE(EXCLUDED.source_ref, entities.source_ref),
                metadata = entities.metadata || EXCLUDED.metadata,
                embedding = COALESCE(EXCLUDED.embedding, entities.embedding),
                is_active = true,
                last_seen_at = now(),
                updated_at = now()
            RETURNING id, name, kind, source, metadata, created_at, updated_at
            """,
            project_id,
            name,
            kind,
            source,
            source_ref,
            meta_json,
            _to_pgvector(embedding),
        )  # type: ignore[return-value]

    async def get_dead_code(
        self, project_id: UUID, kind: str | None = None
    ) -> list[dict[str, Any]]:
        """List entities flagged as dead code by Axon."""
        conditions = [
            "project_id = $1",
            "metadata->>'is_dead_code' = 'true'",
            "is_active = true",
        ]
        params: list[Any] = [project_id]
        idx = 2

        if kind:
            conditions.append(f"kind = ${idx}")
            params.append(kind)

        where = " AND ".join(conditions)
        return await self._fetch_all(
            f"""
            SELECT id, name, kind, metadata->>'file' AS file,
                   (metadata->>'line')::int AS line
            FROM entities
            WHERE {where}
            ORDER BY name
            """,
            *params,
        )
