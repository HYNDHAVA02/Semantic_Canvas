"""Tests for the list_entities MCP tool."""

from __future__ import annotations

from typing import Any

import asyncpg
import pytest
import pytest_asyncio

from src.mcp.tools.list_entities import ListEntitiesParams, handle_list_entities
from src.repositories.entities import EntitiesRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> EntitiesRepository:
    """Create an EntitiesRepository backed by the test pool."""
    return EntitiesRepository(db_pool)


async def _seed_entity(
    db_pool: asyncpg.Pool,
    project_id: Any,
    name: str,
    kind: str = "service",
    source: str = "manual",
    is_active: bool = True,
) -> None:
    """Insert an entity directly for test setup."""
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO entities (project_id, name, kind, source, is_active)
            VALUES ($1, $2, $3, $4, $5)
            """,
            project_id,
            name,
            kind,
            source,
            is_active,
        )


@pytest.mark.asyncio
class TestListEntities:
    """Tests for the list_entities MCP tool handler."""

    async def test_empty_project(
        self, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """Returns empty list when project has no entities."""
        params = ListEntitiesParams(project_id=test_project["id"])
        result = await handle_list_entities(params, repo)
        assert result == []

    async def test_returns_seeded_entities(
        self, db_pool: asyncpg.Pool, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """Returns all active entities for a project."""
        await _seed_entity(db_pool, test_project["id"], "AuthService")
        await _seed_entity(db_pool, test_project["id"], "PaymentService")

        params = ListEntitiesParams(project_id=test_project["id"])
        result = await handle_list_entities(params, repo)

        names = [e["name"] for e in result]
        assert sorted(names) == ["AuthService", "PaymentService"]

    async def test_filter_by_kind(
        self, db_pool: asyncpg.Pool, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """Filters entities by kind."""
        await _seed_entity(db_pool, test_project["id"], "AuthService", kind="service")
        await _seed_entity(db_pool, test_project["id"], "parse_token", kind="function")

        params = ListEntitiesParams(project_id=test_project["id"], kind="function")
        result = await handle_list_entities(params, repo)

        assert len(result) == 1
        assert result[0]["name"] == "parse_token"

    async def test_filter_by_source(
        self, db_pool: asyncpg.Pool, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """Filters entities by source."""
        await _seed_entity(db_pool, test_project["id"], "AuthService", source="axon")
        await _seed_entity(db_pool, test_project["id"], "PaymentService", source="manual")

        params = ListEntitiesParams(project_id=test_project["id"], source="axon")
        result = await handle_list_entities(params, repo)

        assert len(result) == 1
        assert result[0]["name"] == "AuthService"

    async def test_active_only_false_includes_inactive(
        self, db_pool: asyncpg.Pool, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """Setting active_only=False includes inactive entities."""
        await _seed_entity(db_pool, test_project["id"], "ActiveService", is_active=True)
        await _seed_entity(db_pool, test_project["id"], "DeprecatedService", is_active=False)

        # Default: only active
        params = ListEntitiesParams(project_id=test_project["id"])
        result = await handle_list_entities(params, repo)
        assert len(result) == 1
        assert result[0]["name"] == "ActiveService"

        # Include inactive
        params = ListEntitiesParams(project_id=test_project["id"], active_only=False)
        result = await handle_list_entities(params, repo)
        assert len(result) == 2
