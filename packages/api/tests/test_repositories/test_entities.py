"""Tests for the entities repository."""

from __future__ import annotations

from uuid import UUID

import asyncpg
import pytest
import pytest_asyncio

from src.repositories.entities import EntitiesRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> EntitiesRepository:
    return EntitiesRepository(db_pool)


@pytest.mark.asyncio
class TestEntitiesRepository:

    async def test_create_entity(
        self, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """Creating an entity returns it with an ID."""
        result = await repo.create(
            project_id=test_project["id"],
            name="PaymentService",
            kind="service",
            source="manual",
            metadata={"tech_stack": "Python"},
        )
        assert result is not None
        assert result["name"] == "PaymentService"
        assert result["kind"] == "service"
        assert "id" in result

    async def test_create_entity_upsert(
        self, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """Creating the same entity twice updates instead of duplicating."""
        first = await repo.create(
            project_id=test_project["id"],
            name="AuthService",
            kind="service",
            metadata={"version": "1.0"},
        )
        second = await repo.create(
            project_id=test_project["id"],
            name="AuthService",
            kind="service",
            metadata={"version": "2.0"},
        )
        assert first["id"] == second["id"]

    async def test_list_by_project(
        self, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """List returns all entities for a project."""
        await repo.create(
            project_id=test_project["id"], name="ServiceA", kind="service"
        )
        await repo.create(
            project_id=test_project["id"], name="ServiceB", kind="service"
        )
        await repo.create(
            project_id=test_project["id"], name="users", kind="table"
        )

        all_entities, total = await repo.list_by_project(test_project["id"])
        assert len(all_entities) == 3
        assert total == 3

        services_only, svc_total = await repo.list_by_project(
            test_project["id"], kind="service"
        )
        assert len(services_only) == 2
        assert svc_total == 2

    async def test_list_empty_project(
        self, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """List on empty project returns empty list, not error."""
        result, total = await repo.list_by_project(test_project["id"])
        assert result == []
        assert total == 0

    async def test_get_by_name(
        self, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """Get by name returns the entity."""
        await repo.create(
            project_id=test_project["id"], name="CacheService", kind="service"
        )
        result = await repo.get_by_name(test_project["id"], "CacheService")
        assert result is not None
        assert result["name"] == "CacheService"

    async def test_get_by_name_not_found(
        self, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """Get by name returns None when not found."""
        result = await repo.get_by_name(test_project["id"], "NonExistent")
        assert result is None

    async def test_get_dead_code(
        self, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """Dead code query returns entities flagged by Axon."""
        await repo.create(
            project_id=test_project["id"],
            name="usedFunction",
            kind="function",
            source="axon",
            metadata={"is_dead_code": False, "file": "src/main.py"},
        )
        await repo.create(
            project_id=test_project["id"],
            name="unusedHelper",
            kind="function",
            source="axon",
            metadata={"is_dead_code": True, "file": "src/utils.py", "line": 42},
        )

        dead = await repo.get_dead_code(test_project["id"])
        assert len(dead) == 1
        assert dead[0]["name"] == "unusedHelper"
