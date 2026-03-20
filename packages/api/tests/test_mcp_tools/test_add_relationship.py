"""Tests for the add_relationship MCP tool."""

from __future__ import annotations

from typing import Any

import asyncpg
import pytest
import pytest_asyncio

from src.mcp.tools.add_relationship import (
    AddRelationshipParams,
    handle_add_relationship,
)
from src.repositories.entities import EntitiesRepository
from src.repositories.relationships import RelationshipsRepository


@pytest_asyncio.fixture
async def entity_repo(db_pool: asyncpg.Pool) -> EntitiesRepository:
    """Create an EntitiesRepository for seeding test entities."""
    return EntitiesRepository(db_pool)


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> RelationshipsRepository:
    """Create a RelationshipsRepository backed by the test pool."""
    return RelationshipsRepository(db_pool)


async def _seed_entity(
    entity_repo: EntitiesRepository,
    project_id: Any,
    name: str,
    kind: str = "service",
) -> dict[str, Any]:
    """Create an entity and return it."""
    return await entity_repo.create(
        project_id=project_id, name=name, kind=kind
    )


@pytest.mark.asyncio
class TestAddRelationship:
    """Tests for the add_relationship MCP tool handler."""

    async def test_creates_relationship(
        self,
        entity_repo: EntitiesRepository,
        repo: RelationshipsRepository,
        test_project: dict,
    ) -> None:
        """Creates a relationship and returns it with an ID."""
        from_entity = await _seed_entity(
            entity_repo, test_project["id"], "AuthService"
        )
        to_entity = await _seed_entity(
            entity_repo, test_project["id"], "UserDB", kind="table"
        )

        params = AddRelationshipParams(
            project_id=test_project["id"],
            from_entity_id=from_entity["id"],
            to_entity_id=to_entity["id"],
            kind="uses",
        )
        result = await handle_add_relationship(params, repo)

        assert result is not None
        assert "id" in result
        assert result["kind"] == "uses"
        assert result["from_entity_id"] == from_entity["id"]
        assert result["to_entity_id"] == to_entity["id"]

    async def test_upsert_merges_metadata(
        self,
        entity_repo: EntitiesRepository,
        repo: RelationshipsRepository,
        test_project: dict,
    ) -> None:
        """Upserting an existing relationship merges metadata."""
        from_entity = await _seed_entity(
            entity_repo, test_project["id"], "ServiceA"
        )
        to_entity = await _seed_entity(
            entity_repo, test_project["id"], "ServiceB"
        )

        params1 = AddRelationshipParams(
            project_id=test_project["id"],
            from_entity_id=from_entity["id"],
            to_entity_id=to_entity["id"],
            kind="calls",
            metadata={"frequency": "high"},
        )
        first = await handle_add_relationship(params1, repo)

        params2 = AddRelationshipParams(
            project_id=test_project["id"],
            from_entity_id=from_entity["id"],
            to_entity_id=to_entity["id"],
            kind="calls",
            metadata={"latency": "low"},
        )
        second = await handle_add_relationship(params2, repo)

        assert first["id"] == second["id"]

    async def test_source_defaults_to_agent(
        self,
        entity_repo: EntitiesRepository,
        repo: RelationshipsRepository,
        test_project: dict,
    ) -> None:
        """Source defaults to 'agent' for MCP-created relationships."""
        from_entity = await _seed_entity(
            entity_repo, test_project["id"], "GatewayService"
        )
        to_entity = await _seed_entity(
            entity_repo, test_project["id"], "PaymentService"
        )

        params = AddRelationshipParams(
            project_id=test_project["id"],
            from_entity_id=from_entity["id"],
            to_entity_id=to_entity["id"],
            kind="calls",
        )
        result = await handle_add_relationship(params, repo)

        assert result["source"] == "agent"
