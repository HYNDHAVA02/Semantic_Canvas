"""Conventions repository — CRUD for the conventions table."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.repositories.base import BaseRepository, _to_pgvector


class ConventionsRepository(BaseRepository):
    """Data access for the conventions table."""

    async def list_by_project(
        self,
        project_id: UUID,
        scope: str | None = None,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """List conventions with SQL pagination. Returns (rows, total)."""
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2

        if scope:
            conditions.append(f"scope = ${idx}")
            params.append(scope)
            idx += 1

        if active_only:
            conditions.append("is_active = true")

        where = " AND ".join(conditions)

        total_row = await self._fetch_one(
            f"SELECT count(*) AS cnt FROM conventions WHERE {where}", *params
        )
        total = total_row["cnt"] if total_row else 0

        params.append(limit)
        params.append(offset)
        query = f"""
            SELECT id, title, body, scope, source, source_ref,
                   tags, is_active, created_at, updated_at
            FROM conventions
            WHERE {where}
            ORDER BY title
            LIMIT ${idx} OFFSET ${idx + 1}
        """
        rows = await self._fetch_all(query, *params)
        return rows, total

    async def create(
        self,
        project_id: UUID,
        title: str,
        body: str,
        scope: str | None = None,
        source: str = "manual",
        source_ref: str | None = None,
        tags: list[str] | None = None,
        is_active: bool = True,
        embedding: list[float] | None = None,
    ) -> dict[str, Any]:
        """Create a new convention."""
        row = await self._fetch_one(
            """
            INSERT INTO conventions
                (project_id, title, body, scope, source, source_ref, tags, is_active, embedding)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::vector)
            RETURNING id, title, body, scope, source, tags, is_active,
                      created_at, updated_at
            """,
            project_id,
            title,
            body,
            scope,
            source,
            source_ref,
            tags or [],
            is_active,
            _to_pgvector(embedding),
        )
        return row  # type: ignore[return-value]

    async def update(
        self,
        conv_id: UUID,
        **fields: Any,
    ) -> dict[str, Any] | None:
        """Partial update of a convention."""
        allowed = {"title", "body", "scope", "is_active", "tags"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return await self._fetch_one(
                "SELECT id, title, body, scope, source, tags, is_active, "
                "created_at, updated_at FROM conventions WHERE id = $1",
                conv_id,
            )

        set_clauses = []
        params: list[Any] = []
        for i, (col, val) in enumerate(updates.items(), start=1):
            set_clauses.append(f"{col} = ${i}")
            params.append(val)

        params.append(conv_id)
        idx = len(params)

        return await self._fetch_one(
            f"""
            UPDATE conventions SET {', '.join(set_clauses)}, updated_at = now()
            WHERE id = ${idx}
            RETURNING id, title, body, scope, source, tags, is_active,
                      created_at, updated_at
            """,
            *params,
        )
