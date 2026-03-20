"""Tests for the get_relationships MCP tool."""

from __future__ import annotations

from typing import Any

import asyncpg
import pytest
import pytest_asyncio

from src.mcp.tools.get_relationships import (
    GetRelationshipsParams,
    handle_get_relationships,
)
from src.repositories.entities import EntitiesRepository
from src.repositories.relationships import RelationshipsRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> RelationshipsRepository:
    """Create a RelationshipsRepository backed by the test pool."""
    return RelationshipsRepository(db_pool)


@pytest_asyncio.fixture
async def seeded_project(
    db_pool: asyncpg.Pool, test_project: dict
) -> dict[str, Any]:
    """Seed entities and a relationship, return IDs."""
    ent_repo = EntitiesRepository(db_pool)
    rel_repo = RelationshipsRepository(db_pool)

    a = await ent_repo.create(
        project_id=test_project["id"], name="OrderService", kind="service"
    )
    b = await ent_repo.create(
        project_id=test_project["id"], name="PaymentService", kind="service"
    )
    rel = await rel_repo.create(
        project_id=test_project["id"],
        from_entity_id=a["id"],
        to_entity_id=b["id"],
        kind="calls",
    )
    return {
        "project_id": test_project["id"],
        "entity_a": a,
        "entity_b": b,
        "relationship": rel,
    }


@pytest.mark.asyncio
class TestGetRelationships:
    """Tests for the get_relationships MCP tool handler."""

    async def test_empty_project(
        self, repo: RelationshipsRepository, test_project: dict
    ) -> None:
        """Returns empty list for project with no relationships."""
        params = GetRelationshipsParams(project_id=test_project["id"])
        result = await handle_get_relationships(params, repo)
        assert result == []

    async def test_returns_project_relationships(
        self, repo: RelationshipsRepository, seeded_project: dict[str, Any]
    ) -> None:
        """Returns all relationships in a project."""
        params = GetRelationshipsParams(project_id=seeded_project["project_id"])
        result = await handle_get_relationships(params, repo)
        assert len(result) == 1
        assert result[0]["from_entity_name"] == "OrderService"
        assert result[0]["to_entity_name"] == "PaymentService"

    async def test_entity_id_filter(
        self, repo: RelationshipsRepository, seeded_project: dict[str, Any]
    ) -> None:
        """Filtering by entity_id returns only relevant relationships."""
        params = GetRelationshipsParams(
            project_id=seeded_project["project_id"],
            entity_id=seeded_project["entity_a"]["id"],
        )
        result = await handle_get_relationships(params, repo)
        assert len(result) == 1

    async def test_kind_filter(
        self, repo: RelationshipsRepository, seeded_project: dict[str, Any]
    ) -> None:
        """Kind filter returns only matching relationships."""
        params = GetRelationshipsParams(
            project_id=seeded_project["project_id"], kind="depends_on"
        )
        result = await handle_get_relationships(params, repo)
        assert result == []

        params = GetRelationshipsParams(
            project_id=seeded_project["project_id"], kind="calls"
        )
        result = await handle_get_relationships(params, repo)
        assert len(result) == 1
