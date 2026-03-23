"""Tests for the entities REST controller."""

from __future__ import annotations

from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.repositories.entities import EntitiesRepository


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
async def seeded_entities(
    db_pool, test_project: dict
) -> tuple[dict, list[dict[str, Any]]]:
    """Seed some entities and return (project, entities)."""
    repo = EntitiesRepository(db_pool)
    entities = []
    for name, kind in [("AuthService", "service"), ("UserDB", "table"), ("cache_get", "function")]:
        e = await repo.create(
            project_id=test_project["id"], name=name, kind=kind
        )
        entities.append(e)
    return test_project, entities


@pytest.mark.asyncio
class TestEntitiesEndpoints:

    async def test_list_entities(
        self, client: AsyncClient, seeded_entities: tuple
    ) -> None:
        """GET lists entities with pagination."""
        project, _ = seeded_entities
        resp = await client.get(
            f"/api/v1/projects/{project['id']}/entities/"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["data"]) == 3

    async def test_list_filter_by_kind(
        self, client: AsyncClient, seeded_entities: tuple
    ) -> None:
        """Kind filter narrows results."""
        project, _ = seeded_entities
        resp = await client.get(
            f"/api/v1/projects/{project['id']}/entities/?kind=service"
        )
        data = resp.json()
        assert data["total"] == 1
        assert data["data"][0]["name"] == "AuthService"

    async def test_get_entity_detail(
        self, client: AsyncClient, seeded_entities: tuple
    ) -> None:
        """GET /:entityId returns entity with relationships and activity."""
        project, entities = seeded_entities
        entity_id = entities[0]["id"]
        resp = await client.get(
            f"/api/v1/projects/{project['id']}/entities/{entity_id}"
        )
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["name"] == "AuthService"
        assert "relationships" in detail
        assert "recent_activity" in detail

    async def test_get_entity_not_found(
        self, client: AsyncClient, test_project: dict
    ) -> None:
        """GET returns 404 for unknown entity."""
        resp = await client.get(
            f"/api/v1/projects/{test_project['id']}/entities/"
            "00000000-0000-0000-0000-000000000099"
        )
        assert resp.status_code == 404
