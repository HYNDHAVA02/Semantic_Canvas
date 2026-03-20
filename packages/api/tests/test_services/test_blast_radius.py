"""Tests for the blast radius service."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import asyncpg
import pytest
import pytest_asyncio

from src.repositories.entities import EntitiesRepository
from src.repositories.relationships import RelationshipsRepository
from src.services.blast_radius import BlastRadiusService


@pytest_asyncio.fixture
async def service(db_pool: asyncpg.Pool) -> BlastRadiusService:
    """Create a BlastRadiusService backed by the test pool."""
    return BlastRadiusService(db_pool)


@pytest_asyncio.fixture
async def chain(
    db_pool: asyncpg.Pool, test_project: dict
) -> dict[str, Any]:
    """Seed a linear chain: A → B → C → D (all 'calls' relationships)."""
    ent = EntitiesRepository(db_pool)
    rel = RelationshipsRepository(db_pool)
    pid = test_project["id"]

    a = await ent.create(project_id=pid, name="A", kind="service")
    b = await ent.create(project_id=pid, name="B", kind="service")
    c = await ent.create(project_id=pid, name="C", kind="service")
    d = await ent.create(project_id=pid, name="D", kind="service")

    await rel.create(project_id=pid, from_entity_id=a["id"], to_entity_id=b["id"], kind="calls")
    await rel.create(project_id=pid, from_entity_id=b["id"], to_entity_id=c["id"], kind="calls")
    await rel.create(project_id=pid, from_entity_id=c["id"], to_entity_id=d["id"], kind="calls")

    return {
        "project_id": pid,
        "a": a["id"],
        "b": b["id"],
        "c": c["id"],
        "d": d["id"],
    }


@pytest.mark.asyncio
class TestBlastRadiusService:
    """Tests for BlastRadiusService."""

    async def test_forward_full_depth(
        self, service: BlastRadiusService, chain: dict[str, Any]
    ) -> None:
        """Forward from A at depth 3 returns B(1), C(2), D(3)."""
        result = await service.forward_impact(
            project_id=chain["project_id"],
            entity_id=chain["a"],
            max_depth=3,
        )
        names = [(r["name"], r["depth"]) for r in result]
        assert names == [("B", 1), ("C", 2), ("D", 3)]

    async def test_forward_limited_depth(
        self, service: BlastRadiusService, chain: dict[str, Any]
    ) -> None:
        """Forward from A at depth 1 returns only B."""
        result = await service.forward_impact(
            project_id=chain["project_id"],
            entity_id=chain["a"],
            max_depth=1,
        )
        assert len(result) == 1
        assert result[0]["name"] == "B"

    async def test_reverse_impact(
        self, service: BlastRadiusService, chain: dict[str, Any]
    ) -> None:
        """Reverse from D returns C(1), B(2), A(3)."""
        result = await service.reverse_impact(
            project_id=chain["project_id"],
            entity_id=chain["d"],
            max_depth=3,
        )
        names = [(r["name"], r["depth"]) for r in result]
        assert names == [("C", 1), ("B", 2), ("A", 3)]

    async def test_no_relationships(
        self, service: BlastRadiusService, test_project: dict, db_pool: asyncpg.Pool
    ) -> None:
        """Entity with no relationships returns empty list."""
        ent = EntitiesRepository(db_pool)
        lonely = await ent.create(
            project_id=test_project["id"], name="Lonely", kind="service"
        )
        result = await service.forward_impact(
            project_id=test_project["id"],
            entity_id=lonely["id"],
        )
        assert result == []

    async def test_cycle_does_not_loop(
        self, service: BlastRadiusService, db_pool: asyncpg.Pool, test_project: dict
    ) -> None:
        """Cycles are handled by UNION deduplication — no infinite recursion."""
        ent = EntitiesRepository(db_pool)
        rel = RelationshipsRepository(db_pool)
        pid = test_project["id"]

        x = await ent.create(project_id=pid, name="X", kind="service")
        y = await ent.create(project_id=pid, name="Y", kind="service")

        # X → Y → X (cycle)
        await rel.create(project_id=pid, from_entity_id=x["id"], to_entity_id=y["id"], kind="calls")
        await rel.create(project_id=pid, from_entity_id=y["id"], to_entity_id=x["id"], kind="calls")

        result = await service.forward_impact(
            project_id=pid, entity_id=x["id"], max_depth=5
        )
        # Should find Y (and X back via cycle), but no infinite loop
        names = {r["name"] for r in result}
        assert "Y" in names
        assert len(result) <= 2  # at most X and Y
