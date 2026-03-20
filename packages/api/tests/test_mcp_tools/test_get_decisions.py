"""Tests for the get_decisions MCP tool."""

from __future__ import annotations

from typing import Any

import asyncpg
import pytest
import pytest_asyncio

from src.mcp.tools.get_decisions import GetDecisionsParams, handle_get_decisions
from src.repositories.decisions import DecisionsRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> DecisionsRepository:
    """Create a DecisionsRepository backed by the test pool."""
    return DecisionsRepository(db_pool)


async def _seed_decision(
    db_pool: asyncpg.Pool,
    project_id: Any,
    title: str,
    body: str = "Decision body.",
    source: str = "manual",
    tags: list[str] | None = None,
) -> None:
    """Insert a decision directly for test setup."""
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO decisions (project_id, title, body, source, tags)
            VALUES ($1, $2, $3, $4, $5)
            """,
            project_id,
            title,
            body,
            source,
            tags or [],
        )


@pytest.mark.asyncio
class TestGetDecisions:
    """Tests for the get_decisions MCP tool handler."""

    async def test_empty_project(
        self, repo: DecisionsRepository, test_project: dict
    ) -> None:
        """Returns empty list when project has no decisions."""
        params = GetDecisionsParams(project_id=test_project["id"])
        result = await handle_get_decisions(params, repo)
        assert result == []

    async def test_returns_seeded_decisions(
        self, db_pool: asyncpg.Pool, repo: DecisionsRepository, test_project: dict
    ) -> None:
        """Returns all decisions for a project."""
        await _seed_decision(db_pool, test_project["id"], "Use PostgreSQL")
        await _seed_decision(db_pool, test_project["id"], "Use FastAPI")

        params = GetDecisionsParams(project_id=test_project["id"])
        result = await handle_get_decisions(params, repo)

        titles = [d["title"] for d in result]
        assert "Use PostgreSQL" in titles
        assert "Use FastAPI" in titles

    async def test_filter_by_tag(
        self, db_pool: asyncpg.Pool, repo: DecisionsRepository, test_project: dict
    ) -> None:
        """Filters decisions by tag."""
        await _seed_decision(
            db_pool, test_project["id"], "Use PostgreSQL", tags=["database"]
        )
        await _seed_decision(
            db_pool, test_project["id"], "Use FastAPI", tags=["backend"]
        )

        params = GetDecisionsParams(project_id=test_project["id"], tag="database")
        result = await handle_get_decisions(params, repo)

        assert len(result) == 1
        assert result[0]["title"] == "Use PostgreSQL"

    async def test_filter_by_source(
        self, db_pool: asyncpg.Pool, repo: DecisionsRepository, test_project: dict
    ) -> None:
        """Filters decisions by source."""
        await _seed_decision(
            db_pool, test_project["id"], "Manual decision", source="manual"
        )
        await _seed_decision(
            db_pool, test_project["id"], "Agent decision", source="agent"
        )

        params = GetDecisionsParams(project_id=test_project["id"], source="agent")
        result = await handle_get_decisions(params, repo)

        assert len(result) == 1
        assert result[0]["title"] == "Agent decision"
