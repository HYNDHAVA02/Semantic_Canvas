"""Tests for the conventions REST controller."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def client(db_pool) -> AsyncClient:
    """Create an async test client with mock embeddings."""
    from src.main import create_app

    app = create_app()
    app.state.db_pool = db_pool
    mock_emb = MagicMock()
    mock_emb.embed_one.return_value = [0.0] * 384
    app.state.embeddings = mock_emb

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestConventionsEndpoints:

    async def test_create_and_list(
        self, client: AsyncClient, test_project: dict
    ) -> None:
        """POST creates, GET lists."""
        pid = test_project["id"]

        resp = await client.post(
            f"/api/v1/projects/{pid}/conventions/",
            json={
                "title": "Use type hints",
                "body": "All functions need type hints.",
                "scope": "backend",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "Use type hints"

        resp = await client.get(f"/api/v1/projects/{pid}/conventions/")
        data = resp.json()
        assert data["total"] == 1

    async def test_patch_toggle_active(
        self, client: AsyncClient, test_project: dict
    ) -> None:
        """PATCH can toggle is_active."""
        pid = test_project["id"]
        create_resp = await client.post(
            f"/api/v1/projects/{pid}/conventions/",
            json={"title": "Old rule", "body": "Deprecated."},
        )
        conv_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/api/v1/projects/{pid}/conventions/{conv_id}",
            json={"is_active": False},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_scope_filter(
        self, client: AsyncClient, test_project: dict
    ) -> None:
        """Scope filter works."""
        pid = test_project["id"]
        await client.post(
            f"/api/v1/projects/{pid}/conventions/",
            json={"title": "BE rule", "body": "b", "scope": "backend"},
        )
        await client.post(
            f"/api/v1/projects/{pid}/conventions/",
            json={"title": "FE rule", "body": "f", "scope": "frontend"},
        )

        resp = await client.get(
            f"/api/v1/projects/{pid}/conventions/?scope=frontend"
        )
        data = resp.json()
        assert data["total"] == 1
        assert data["data"][0]["title"] == "FE rule"
