"""Base repository — shared DB pool access for all repositories."""

from __future__ import annotations

from typing import Any

import asyncpg


def _to_pgvector(embedding: list[float] | None) -> str | None:
    """Convert a float list to pgvector string format, or None."""
    if embedding is None:
        return None
    return "[" + ",".join(str(v) for v in embedding) + "]"


class BaseRepository:
    """Base class for all repositories.

    Provides access to the asyncpg connection pool
    and common query helpers.
    """

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def _fetch_all(self, query: str, *args: Any) -> list[dict[str, Any]]:
        """Execute a query and return all rows as dicts."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def _fetch_one(self, query: str, *args: Any) -> dict[str, Any] | None:
        """Execute a query and return one row as a dict, or None."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def _execute(self, query: str, *args: Any) -> str:
        """Execute a query and return the status string."""
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)
