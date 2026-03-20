"""Tests for the get_recent_activity MCP tool."""

from __future__ import annotations

from typing import Any

import asyncpg
import pytest
import pytest_asyncio

from src.mcp.tools.get_recent_activity import (
    GetRecentActivityParams,
    handle_get_recent_activity,
)
from src.repositories.activity import ActivityRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> ActivityRepository:
    """Create an ActivityRepository backed by the test pool."""
    return ActivityRepository(db_pool)


async def _seed_activity(
    db_pool: asyncpg.Pool,
    project_id: Any,
    summary: str,
    source: str = "manual",
    actor: str | None = None,
) -> None:
    """Insert an activity log entry directly for test setup."""
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO activity_log (project_id, summary, source, actor)
            VALUES ($1, $2, $3, $4)
            """,
            project_id,
            summary,
            source,
            actor,
        )


@pytest.mark.asyncio
class TestGetRecentActivity:
    """Tests for the get_recent_activity MCP tool handler."""

    async def test_empty_project(
        self, repo: ActivityRepository, test_project: dict
    ) -> None:
        """Returns empty list when project has no activity."""
        params = GetRecentActivityParams(project_id=test_project["id"])
        result = await handle_get_recent_activity(params, repo)
        assert result == []

    async def test_returns_seeded_activity(
        self, db_pool: asyncpg.Pool, repo: ActivityRepository, test_project: dict
    ) -> None:
        """Returns activity entries for a project."""
        await _seed_activity(db_pool, test_project["id"], "Deployed v1.0")
        await _seed_activity(db_pool, test_project["id"], "Fixed auth bug")

        params = GetRecentActivityParams(project_id=test_project["id"])
        result = await handle_get_recent_activity(params, repo)

        summaries = [a["summary"] for a in result]
        assert "Deployed v1.0" in summaries
        assert "Fixed auth bug" in summaries

    async def test_limit(
        self, db_pool: asyncpg.Pool, repo: ActivityRepository, test_project: dict
    ) -> None:
        """Limit restricts number of returned entries."""
        for i in range(5):
            await _seed_activity(db_pool, test_project["id"], f"Activity {i}")

        params = GetRecentActivityParams(project_id=test_project["id"], limit=3)
        result = await handle_get_recent_activity(params, repo)
        assert len(result) == 3

    async def test_filter_by_source(
        self, db_pool: asyncpg.Pool, repo: ActivityRepository, test_project: dict
    ) -> None:
        """Source filter returns only matching entries."""
        await _seed_activity(
            db_pool, test_project["id"], "GitHub push", source="github"
        )
        await _seed_activity(
            db_pool, test_project["id"], "Manual note", source="manual"
        )

        params = GetRecentActivityParams(
            project_id=test_project["id"], source="github"
        )
        result = await handle_get_recent_activity(params, repo)

        assert len(result) == 1
        assert result[0]["summary"] == "GitHub push"

    async def test_filter_by_actor(
        self, db_pool: asyncpg.Pool, repo: ActivityRepository, test_project: dict
    ) -> None:
        """Actor filter returns only matching entries."""
        await _seed_activity(
            db_pool, test_project["id"], "Alice commit", actor="alice"
        )
        await _seed_activity(
            db_pool, test_project["id"], "Bob commit", actor="bob"
        )

        params = GetRecentActivityParams(
            project_id=test_project["id"], actor="alice"
        )
        result = await handle_get_recent_activity(params, repo)

        assert len(result) == 1
        assert result[0]["summary"] == "Alice commit"
