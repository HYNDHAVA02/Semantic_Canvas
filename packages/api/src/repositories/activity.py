"""Activity repository — CRUD for the activity_log table."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.repositories.base import BaseRepository, _to_pgvector


class ActivityRepository(BaseRepository):
    """Data access for the activity_log table."""

    async def list_recent(
        self,
        project_id: UUID,
        limit: int = 50,
        source: str | None = None,
        actor: str | None = None,
    ) -> list[dict[str, Any]]:
        """List recent activity, optionally filtered by source and actor."""
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2

        if source:
            conditions.append(f"source = ${idx}")
            params.append(source)
            idx += 1

        if actor:
            conditions.append(f"actor = ${idx}")
            params.append(actor)
            idx += 1

        where = " AND ".join(conditions)
        query = f"""
            SELECT id, summary, detail, entity_ids, source,
                   source_ref, actor, occurred_at, created_at
            FROM activity_log
            WHERE {where}
            ORDER BY occurred_at DESC
            LIMIT ${idx}
        """
        params.append(limit)
        return await self._fetch_all(query, *params)

    async def create(
        self,
        project_id: UUID,
        summary: str,
        source: str,
        detail: str | None = None,
        actor: str | None = None,
        source_ref: str | None = None,
        embedding: list[float] | None = None,
    ) -> dict[str, Any]:
        """Create a new activity log entry."""
        row = await self._fetch_one(
            """
            INSERT INTO activity_log
                (project_id, summary, detail, source, source_ref, actor, embedding)
            VALUES ($1, $2, $3, $4, $5, $6, $7::vector)
            RETURNING id, summary, detail, source, actor, occurred_at, created_at
            """,
            project_id,
            summary,
            detail,
            source,
            source_ref,
            actor,
            _to_pgvector(embedding),
        )
        return row  # type: ignore[return-value]
