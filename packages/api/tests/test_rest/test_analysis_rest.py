"""Tests for the analysis REST controller (dead code + blast radius)."""

from __future__ import annotations

from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.repositories.entities import EntitiesRepository
from src.repositories.relationships import RelationshipsRepository


@pytest_asyncio.fixture
async def client(db_pool) -> AsyncClient:
    """Create an async test client."""
    from src.main import create_app

    app = create_app()
    app.state.db_pool = db_pool

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def graph_data(
    db_pool, test_project: dict
) -> tuple[dict, dict[str, Any], dict[str, Any]]:
    """Seed a small graph: A -> B."""
    ent_repo = EntitiesRepository(db_pool)
    a = await ent_repo.create(
        project_id=test_project["id"], name="ServiceA", kind="service"
    )
    b = await ent_repo.create(
        project_id=test_project["id"], name="ServiceB", kind="service"
    )
    rel_repo = RelationshipsRepository(db_pool)
    await rel_repo.create(
        project_id=test_project["id"],
        from_entity_id=a["id"],
        to_entity_id=b["id"],
        kind="calls",
    )
    return test_project, a, b


@pytest.mark.asyncio
class TestAnalysisEndpoints:

    async def test_dead_code_empty(
        self, client: AsyncClient, test_project: dict
    ) -> None:
        """Dead code returns empty list when none flagged."""
        resp = await client.get(
            f"/api/v1/projects/{test_project['id']}/dead-code"
        )
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    async def test_dead_code_with_flagged(
        self, client: AsyncClient, test_project: dict, db_pool
    ) -> None:
        """Dead code returns flagged entities."""
        repo = EntitiesRepository(db_pool)
        await repo.create(
            project_id=test_project["id"],
            name="unusedFn",
            kind="function",
            source="axon",
            metadata={"is_dead_code": True, "file": "src/x.py", "line": 10},
        )

        resp = await client.get(
            f"/api/v1/projects/{test_project['id']}/dead-code"
        )
        data = resp.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "unusedFn"

    async def test_blast_radius_forward(
        self, client: AsyncClient, graph_data: tuple
    ) -> None:
        """Forward blast radius from A includes B."""
        project, a, b = graph_data
        resp = await client.get(
            f"/api/v1/projects/{project['id']}/blast-radius/{a['id']}"
            "?direction=forward&depth=3"
        )
        assert resp.status_code == 200
        data = resp.json()
        names = [e["name"] for e in data["data"]]
        assert "ServiceB" in names

    async def test_blast_radius_both(
        self, client: AsyncClient, graph_data: tuple
    ) -> None:
        """Both direction returns forward and reverse keys."""
        project, a, _ = graph_data
        resp = await client.get(
            f"/api/v1/projects/{project['id']}/blast-radius/{a['id']}"
            "?direction=both"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "forward" in data
        assert "reverse" in data
