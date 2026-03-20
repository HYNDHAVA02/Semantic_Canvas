"""Tests for the get_conventions MCP tool."""

from __future__ import annotations

from typing import Any

import asyncpg
import pytest
import pytest_asyncio

from src.mcp.tools.get_conventions import (
    GetConventionsParams,
    handle_get_conventions,
)
from src.repositories.conventions import ConventionsRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> ConventionsRepository:
    """Create a ConventionsRepository backed by the test pool."""
    return ConventionsRepository(db_pool)


async def _seed_convention(
    db_pool: asyncpg.Pool,
    project_id: Any,
    title: str,
    body: str = "Convention body.",
    scope: str | None = None,
    is_active: bool = True,
) -> None:
    """Insert a convention directly for test setup."""
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO conventions (project_id, title, body, scope, is_active)
            VALUES ($1, $2, $3, $4, $5)
            """,
            project_id,
            title,
            body,
            scope,
            is_active,
        )


@pytest.mark.asyncio
class TestGetConventions:
    """Tests for the get_conventions MCP tool handler."""

    async def test_empty_project(
        self, repo: ConventionsRepository, test_project: dict
    ) -> None:
        """Returns empty list when project has no conventions."""
        params = GetConventionsParams(project_id=test_project["id"])
        result = await handle_get_conventions(params, repo)
        assert result == []

    async def test_returns_seeded_conventions(
        self, db_pool: asyncpg.Pool, repo: ConventionsRepository, test_project: dict
    ) -> None:
        """Returns all active conventions for a project."""
        await _seed_convention(db_pool, test_project["id"], "Use type hints")
        await _seed_convention(db_pool, test_project["id"], "Kebab-case files")

        params = GetConventionsParams(project_id=test_project["id"])
        result = await handle_get_conventions(params, repo)

        titles = [c["title"] for c in result]
        assert "Use type hints" in titles
        assert "Kebab-case files" in titles

    async def test_filter_by_scope(
        self, db_pool: asyncpg.Pool, repo: ConventionsRepository, test_project: dict
    ) -> None:
        """Filters conventions by scope."""
        await _seed_convention(
            db_pool, test_project["id"], "Backend rule", scope="backend"
        )
        await _seed_convention(
            db_pool, test_project["id"], "Frontend rule", scope="frontend"
        )

        params = GetConventionsParams(project_id=test_project["id"], scope="backend")
        result = await handle_get_conventions(params, repo)

        assert len(result) == 1
        assert result[0]["title"] == "Backend rule"

    async def test_active_only(
        self, db_pool: asyncpg.Pool, repo: ConventionsRepository, test_project: dict
    ) -> None:
        """active_only filter excludes inactive conventions."""
        await _seed_convention(
            db_pool, test_project["id"], "Active rule", is_active=True
        )
        await _seed_convention(
            db_pool, test_project["id"], "Deprecated rule", is_active=False
        )

        # Default: only active
        params = GetConventionsParams(project_id=test_project["id"])
        result = await handle_get_conventions(params, repo)
        assert len(result) == 1
        assert result[0]["title"] == "Active rule"

        # Include inactive
        params = GetConventionsParams(
            project_id=test_project["id"], active_only=False
        )
        result = await handle_get_conventions(params, repo)
        assert len(result) == 2
