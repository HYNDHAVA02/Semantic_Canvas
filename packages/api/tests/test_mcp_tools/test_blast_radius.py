"""Tests for the blast_radius MCP tool."""

from __future__ import annotations

from typing import Any

import asyncpg
import pytest
import pytest_asyncio

from src.mcp.tools.blast_radius import BlastRadiusParams, handle_blast_radius
from src.repositories.entities import EntitiesRepository
from src.repositories.relationships import RelationshipsRepository
from src.services.blast_radius import BlastRadiusService


@pytest_asyncio.fixture
async def service(db_pool: asyncpg.Pool) -> BlastRadiusService:
    """Create a BlastRadiusService backed by the test pool."""
    return BlastRadiusService(db_pool)


@pytest_asyncio.fixture
async def seeded(
    db_pool: asyncpg.Pool, test_project: dict
) -> dict[str, Any]:
    """Seed A → B → C chain."""
    ent = EntitiesRepository(db_pool)
    rel = RelationshipsRepository(db_pool)
    pid = test_project["id"]

    a = await ent.create(project_id=pid, name="API", kind="service")
    b = await ent.create(project_id=pid, name="Cache", kind="service")
    c = await ent.create(project_id=pid, name="DB", kind="database")

    await rel.create(project_id=pid, from_entity_id=a["id"], to_entity_id=b["id"], kind="calls")
    await rel.create(project_id=pid, from_entity_id=b["id"], to_entity_id=c["id"], kind="reads_from")

    return {"project_id": pid, "a": a["id"], "b": b["id"], "c": c["id"]}


@pytest.mark.asyncio
class TestBlastRadius:
    """Tests for the blast_radius MCP tool handler."""

    async def test_forward(
        self, service: BlastRadiusService, seeded: dict[str, Any]
    ) -> None:
        """Forward blast radius returns impacted entities."""
        params = BlastRadiusParams(
            project_id=seeded["project_id"],
            entity_id=seeded["a"],
            direction="forward",
        )
        result = await handle_blast_radius(params, service)
        assert "forward" in result
        names = [e["name"] for e in result["forward"]]
        assert names == ["Cache", "DB"]

    async def test_both_directions(
        self, service: BlastRadiusService, seeded: dict[str, Any]
    ) -> None:
        """Both directions returns forward and reverse."""
        params = BlastRadiusParams(
            project_id=seeded["project_id"],
            entity_id=seeded["b"],
            direction="both",
        )
        result = await handle_blast_radius(params, service)
        assert "forward" in result
        assert "reverse" in result
        forward_names = [e["name"] for e in result["forward"]]
        reverse_names = [e["name"] for e in result["reverse"]]
        assert "DB" in forward_names
        assert "API" in reverse_names

    async def test_max_depth_limits(
        self, service: BlastRadiusService, seeded: dict[str, Any]
    ) -> None:
        """max_depth=1 limits traversal to direct neighbors."""
        params = BlastRadiusParams(
            project_id=seeded["project_id"],
            entity_id=seeded["a"],
            direction="forward",
            max_depth=1,
        )
        result = await handle_blast_radius(params, service)
        assert len(result["forward"]) == 1
        assert result["forward"][0]["name"] == "Cache"

    async def test_empty_graph(
        self, service: BlastRadiusService, test_project: dict, db_pool: asyncpg.Pool
    ) -> None:
        """Entity with no relationships returns empty result."""
        ent = EntitiesRepository(db_pool)
        solo = await ent.create(
            project_id=test_project["id"], name="Solo", kind="service"
        )
        params = BlastRadiusParams(
            project_id=test_project["id"],
            entity_id=solo["id"],
        )
        result = await handle_blast_radius(params, service)
        assert result["forward"] == []
