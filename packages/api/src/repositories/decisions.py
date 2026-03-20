"""Decisions repository — CRUD for the decisions table."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.repositories.base import BaseRepository, _to_pgvector


class DecisionsRepository(BaseRepository):
    """Data access for the decisions table."""

    async def list_by_project(
        self,
        project_id: UUID,
        tag: str | None = None,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        """List decisions, optionally filtered by tag and source."""
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2

        if tag:
            conditions.append(f"${idx} = ANY(tags)")
            params.append(tag)
            idx += 1

        if source:
            conditions.append(f"source = ${idx}")
            params.append(source)
            idx += 1

        where = " AND ".join(conditions)
        query = f"""
            SELECT id, title, body, decided_by, decided_at,
                   entity_ids, source, source_ref, tags,
                   created_at, updated_at
            FROM decisions
            WHERE {where}
            ORDER BY decided_at DESC NULLS LAST, created_at DESC
        """
        return await self._fetch_all(query, *params)

    async def create(
        self,
        project_id: UUID,
        title: str,
        body: str,
        decided_by: str | None = None,
        source: str = "manual",
        source_ref: str | None = None,
        tags: list[str] | None = None,
        embedding: list[float] | None = None,
    ) -> dict[str, Any]:
        """Create a new decision."""
        row = await self._fetch_one(
            """
            INSERT INTO decisions
                (project_id, title, body, decided_by, source, source_ref, tags, embedding)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::vector)
            RETURNING id, title, body, decided_by, decided_at, source, tags,
                      created_at, updated_at
            """,
            project_id,
            title,
            body,
            decided_by,
            source,
            source_ref,
            tags or [],
            _to_pgvector(embedding),
        )
        return row  # type: ignore[return-value]
