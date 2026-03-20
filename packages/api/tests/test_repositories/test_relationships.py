"""Tests for the relationships repository."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import asyncpg
import pytest
import pytest_asyncio

from src.repositories.entities import EntitiesRepository
from src.repositories.relationships import RelationshipsRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> RelationshipsRepository:
    """Create a RelationshipsRepository backed by the test pool."""
    return RelationshipsRepository(db_pool)


@pytest_asyncio.fixture
async def entities_repo(db_pool: asyncpg.Pool) -> EntitiesRepository:
    """Create an EntitiesRepository for seeding test entities."""
    return EntitiesRepository(db_pool)


@pytest_asyncio.fixture
async def two_entities(
    entities_repo: EntitiesRepository, test_project: dict
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Seed two entities and return them."""
    a = await entities_repo.create(
        project_id=test_project["id"], name="AuthService", kind="service"
    )
    b = await entities_repo.create(
        project_id=test_project["id"], name="UserDB", kind="database"
    )
    return a, b


@pytest.mark.asyncio
class TestRelationshipsRepository:
    """Tests for RelationshipsRepository."""

    async def test_create_relationship(
        self,
        repo: RelationshipsRepository,
        test_project: dict,
        two_entities: tuple[dict[str, Any], dict[str, Any]],
    ) -> None:
        """Create a relationship and verify returned fields."""
        a, b = two_entities
        result = await repo.create(
            project_id=test_project["id"],
            from_entity_id=a["id"],
            to_entity_id=b["id"],
            kind="reads_from",
        )
        assert result["kind"] == "reads_from"
        assert result["from_entity_id"] == a["id"]
        assert result["to_entity_id"] == b["id"]

    async def test_create_upsert(
        self,
        repo: RelationshipsRepository,
        test_project: dict,
        two_entities: tuple[dict[str, Any], dict[str, Any]],
    ) -> None:
        """Upserting merges metadata and updates timestamp."""
        a, b = two_entities
        first = await repo.create(
            project_id=test_project["id"],
            from_entity_id=a["id"],
            to_entity_id=b["id"],
            kind="calls",
            metadata={"weight": 1},
        )
        second = await repo.create(
            project_id=test_project["id"],
            from_entity_id=a["id"],
            to_entity_id=b["id"],
            kind="calls",
            metadata={"latency_ms": 50},
        )
        assert first["id"] == second["id"]
        import json
        meta = json.loads(second["metadata"]) if isinstance(second["metadata"], str) else second["metadata"]
        assert meta["weight"] == 1
        assert meta["latency_ms"] == 50

    async def test_list_by_project(
        self,
        repo: RelationshipsRepository,
        test_project: dict,
        two_entities: tuple[dict[str, Any], dict[str, Any]],
    ) -> None:
        """List returns relationships with joined entity names."""
        a, b = two_entities
        await repo.create(
            project_id=test_project["id"],
            from_entity_id=a["id"],
            to_entity_id=b["id"],
            kind="reads_from",
        )
        results = await repo.list_by_project(project_id=test_project["id"])
        assert len(results) == 1
        assert results[0]["from_entity_name"] == "AuthService"
        assert results[0]["to_entity_name"] == "UserDB"

    async def test_list_by_project_kind_filter(
        self,
        repo: RelationshipsRepository,
        test_project: dict,
        two_entities: tuple[dict[str, Any], dict[str, Any]],
    ) -> None:
        """Kind filter narrows results."""
        a, b = two_entities
        await repo.create(
            project_id=test_project["id"],
            from_entity_id=a["id"],
            to_entity_id=b["id"],
            kind="reads_from",
        )
        await repo.create(
            project_id=test_project["id"],
            from_entity_id=a["id"],
            to_entity_id=b["id"],
            kind="calls",
        )
        results = await repo.list_by_project(
            project_id=test_project["id"], kind="calls"
        )
        assert len(results) == 1
        assert results[0]["kind"] == "calls"

    async def test_list_for_entity_both_directions(
        self,
        repo: RelationshipsRepository,
        entities_repo: EntitiesRepository,
        test_project: dict,
        two_entities: tuple[dict[str, Any], dict[str, Any]],
    ) -> None:
        """list_for_entity with no direction returns from + to."""
        a, b = two_entities
        c = await entities_repo.create(
            project_id=test_project["id"], name="Gateway", kind="service"
        )
        # a -> b
        await repo.create(
            project_id=test_project["id"],
            from_entity_id=a["id"],
            to_entity_id=b["id"],
            kind="reads_from",
        )
        # c -> a
        await repo.create(
            project_id=test_project["id"],
            from_entity_id=c["id"],
            to_entity_id=a["id"],
            kind="calls",
        )
        results = await repo.list_for_entity(entity_id=a["id"])
        assert len(results) == 2

    async def test_list_for_entity_direction_from(
        self,
        repo: RelationshipsRepository,
        entities_repo: EntitiesRepository,
        test_project: dict,
        two_entities: tuple[dict[str, Any], dict[str, Any]],
    ) -> None:
        """Direction='from' returns only outgoing relationships."""
        a, b = two_entities
        c = await entities_repo.create(
            project_id=test_project["id"], name="Gateway", kind="service"
        )
        await repo.create(
            project_id=test_project["id"],
            from_entity_id=a["id"],
            to_entity_id=b["id"],
            kind="reads_from",
        )
        await repo.create(
            project_id=test_project["id"],
            from_entity_id=c["id"],
            to_entity_id=a["id"],
            kind="calls",
        )
        results = await repo.list_for_entity(entity_id=a["id"], direction="from")
        assert len(results) == 1
        assert results[0]["to_entity_name"] == "UserDB"

    async def test_list_for_entity_direction_to(
        self,
        repo: RelationshipsRepository,
        entities_repo: EntitiesRepository,
        test_project: dict,
        two_entities: tuple[dict[str, Any], dict[str, Any]],
    ) -> None:
        """Direction='to' returns only incoming relationships."""
        a, b = two_entities
        c = await entities_repo.create(
            project_id=test_project["id"], name="Gateway", kind="service"
        )
        await repo.create(
            project_id=test_project["id"],
            from_entity_id=a["id"],
            to_entity_id=b["id"],
            kind="reads_from",
        )
        await repo.create(
            project_id=test_project["id"],
            from_entity_id=c["id"],
            to_entity_id=a["id"],
            kind="calls",
        )
        results = await repo.list_for_entity(entity_id=a["id"], direction="to")
        assert len(results) == 1
        assert results[0]["from_entity_name"] == "Gateway"
