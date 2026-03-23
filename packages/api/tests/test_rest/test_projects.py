"""Tests for the projects REST controller."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def client(db_pool) -> AsyncClient:
    """Create an async test client with db pool wired up."""
    from src.main import create_app

    app = create_app()
    app.state.db_pool = db_pool

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestProjectsEndpoints:

    async def test_list_empty(self, client: AsyncClient) -> None:
        """GET /projects returns empty paginated list."""
        resp = await client.get("/api/v1/projects/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []
        assert data["total"] == 0
        assert "limit" in data
        assert "offset" in data

    async def test_create_and_get(self, client: AsyncClient) -> None:
        """POST then GET returns the created project."""
        resp = await client.post(
            "/api/v1/projects/",
            json={
                "name": "Test Project",
                "slug": "test-proj",
                "description": "A test",
            },
        )
        assert resp.status_code == 201
        project = resp.json()
        assert project["name"] == "Test Project"
        assert project["slug"] == "test-proj"
        project_id = project["id"]

        resp = await client.get(f"/api/v1/projects/{project_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == project_id

    async def test_get_not_found(self, client: AsyncClient) -> None:
        """GET /projects/:id returns 404 for unknown project."""
        resp = await client.get(
            "/api/v1/projects/00000000-0000-0000-0000-000000000099"
        )
        assert resp.status_code == 404

    async def test_update(self, client: AsyncClient) -> None:
        """PATCH /projects/:id updates specified fields."""
        create_resp = await client.post(
            "/api/v1/projects/",
            json={"name": "Original", "slug": "original"},
        )
        project_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/api/v1/projects/{project_id}",
            json={"name": "Updated"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"
        assert resp.json()["slug"] == "original"  # unchanged

    async def test_list_pagination(self, client: AsyncClient) -> None:
        """List respects limit and offset."""
        for i in range(3):
            await client.post(
                "/api/v1/projects/",
                json={"name": f"Proj {i}", "slug": f"proj-{i}"},
            )

        resp = await client.get("/api/v1/projects/?limit=2&offset=0")
        data = resp.json()
        assert len(data["data"]) == 2
        assert data["total"] == 3

        resp = await client.get("/api/v1/projects/?limit=2&offset=2")
        data = resp.json()
        assert len(data["data"]) == 1
        assert data["total"] == 3
