"""Relationships repository — CRUD + query for the relationships table."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from src.repositories.base import BaseRepository

# Columns selected for all relationship queries (with joined entity names).
_SELECT_COLS = """
    r.id, r.project_id, r.from_entity_id, r.to_entity_id,
    r.kind, r.source, r.source_ref, r.metadata,
    r.created_at, r.updated_at,
    fe.name AS from_entity_name, fe.kind AS from_entity_kind,
    te.name AS to_entity_name, te.kind AS to_entity_kind
"""

_JOIN = """
    FROM relationships r
    JOIN entities fe ON fe.id = r.from_entity_id
    JOIN entities te ON te.id = r.to_entity_id
"""


class RelationshipsRepository(BaseRepository):
    """Data access for the relationships table."""

    async def list_by_project(
        self,
        project_id: UUID,
        kind: str | None = None,
        source: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """List relationships with SQL pagination. Returns (rows, total)."""
        conditions = ["r.project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2

        if kind:
            conditions.append(f"r.kind = ${idx}")
            params.append(kind)
            idx += 1

        if source:
            conditions.append(f"r.source = ${idx}")
            params.append(source)
            idx += 1

        where = " AND ".join(conditions)

        total_row = await self._fetch_one(
            f"SELECT count(*) AS cnt {_JOIN} WHERE {where}", *params
        )
        total = total_row["cnt"] if total_row else 0

        params.append(limit)
        params.append(offset)
        query = (
            f"SELECT {_SELECT_COLS} {_JOIN} WHERE {where} "
            f"ORDER BY fe.name, te.name LIMIT ${idx} OFFSET ${idx + 1}"
        )
        rows = await self._fetch_all(query, *params)
        return rows, total

    async def list_for_entity(
        self,
        entity_id: UUID,
        kind: str | None = None,
        direction: str | None = None,
    ) -> list[dict[str, Any]]:
        """List relationships involving an entity.

        Args:
            entity_id: The entity to query relationships for.
            kind: Optional relationship kind filter.
            direction: 'from' (outgoing), 'to' (incoming), or None (both).
        """
        if direction == "from":
            conditions = ["r.from_entity_id = $1"]
        elif direction == "to":
            conditions = ["r.to_entity_id = $1"]
        else:
            conditions = ["(r.from_entity_id = $1 OR r.to_entity_id = $1)"]

        params: list[Any] = [entity_id]
        idx = 2

        if kind:
            conditions.append(f"r.kind = ${idx}")
            params.append(kind)
            idx += 1

        where = " AND ".join(conditions)
        query = f"SELECT {_SELECT_COLS} {_JOIN} WHERE {where} ORDER BY fe.name, te.name"
        return await self._fetch_all(query, *params)

    async def create(
        self,
        project_id: UUID,
        from_entity_id: UUID,
        to_entity_id: UUID,
        kind: str,
        source: str = "manual",
        source_ref: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a relationship or update if it already exists."""
        meta_json = json.dumps(metadata or {})

        return await self._fetch_one(  # type: ignore[return-value]
            """
            INSERT INTO relationships
                (project_id, from_entity_id, to_entity_id, kind, source, source_ref, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
            ON CONFLICT (project_id, from_entity_id, to_entity_id, kind)
            DO UPDATE SET
                source_ref = COALESCE(EXCLUDED.source_ref, relationships.source_ref),
                metadata = relationships.metadata || EXCLUDED.metadata,
                updated_at = now()
            RETURNING id, project_id, from_entity_id, to_entity_id,
                      kind, source, metadata, created_at, updated_at
            """,
            project_id,
            from_entity_id,
            to_entity_id,
            kind,
            source,
            source_ref,
            meta_json,
        )
