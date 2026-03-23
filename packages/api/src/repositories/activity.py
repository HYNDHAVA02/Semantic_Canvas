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
        offset: int = 0,
        source: str | None = None,
        actor: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """List recent activity with SQL pagination. Returns (rows, total)."""
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

        total_row = await self._fetch_one(
            f"SELECT count(*) AS cnt FROM activity_log WHERE {where}", *params
        )
        total = total_row["cnt"] if total_row else 0

        params.append(limit)
        params.append(offset)
        query = f"""
            SELECT id, summary, detail, entity_ids, source,
                   source_ref, actor, occurred_at, created_at
            FROM activity_log
            WHERE {where}
            ORDER BY occurred_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
        """
        rows = await self._fetch_all(query, *params)
        return rows, total

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
