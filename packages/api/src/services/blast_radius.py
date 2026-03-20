"""Blast radius service — recursive graph traversal over relationships.

Answers: "if I change entity X, what else is affected?" (forward)
and "what affects entity X?" (reverse).

Used by both MCP tools and REST endpoints.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import asyncpg


class BlastRadiusService:
    """Compute forward and reverse impact for an entity."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def forward_impact(
        self,
        project_id: UUID,
        entity_id: UUID,
        max_depth: int = 3,
    ) -> list[dict[str, Any]]:
        """What does this entity affect? Traverse from_entity → to_entity."""
        return await self._traverse(
            project_id, entity_id, max_depth, direction="forward"
        )

    async def reverse_impact(
        self,
        project_id: UUID,
        entity_id: UUID,
        max_depth: int = 3,
    ) -> list[dict[str, Any]]:
        """What affects this entity? Traverse to_entity → from_entity."""
        return await self._traverse(
            project_id, entity_id, max_depth, direction="reverse"
        )

    async def _traverse(
        self,
        project_id: UUID,
        entity_id: UUID,
        max_depth: int,
        direction: str,
    ) -> list[dict[str, Any]]:
        """Run the recursive CTE in the specified direction."""
        if direction == "forward":
            seed_col = "from_entity_id"
            next_col = "to_entity_id"
            join_col = "from_entity_id"
        else:
            seed_col = "to_entity_id"
            next_col = "from_entity_id"
            join_col = "to_entity_id"

        query = f"""
            WITH RECURSIVE blast AS (
                SELECT {next_col} AS entity_id, 1 AS depth,
                       ARRAY[{seed_col}, {next_col}] AS path
                FROM relationships
                WHERE {seed_col} = $1 AND project_id = $2

                UNION ALL

                SELECT r.{next_col}, b.depth + 1,
                       b.path || r.{next_col}
                FROM relationships r
                JOIN blast b ON r.{join_col} = b.entity_id
                WHERE r.project_id = $2
                  AND b.depth < $3
                  AND NOT r.{next_col} = ANY(b.path)
            ),
            nearest AS (
                SELECT DISTINCT ON (entity_id) entity_id, depth
                FROM blast
                ORDER BY entity_id, depth
            )
            SELECT e.id, e.name, e.kind, n.depth
            FROM nearest n
            JOIN entities e ON e.id = n.entity_id
            ORDER BY n.depth, e.name
        """

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, entity_id, project_id, max_depth)
            return [dict(row) for row in rows]
