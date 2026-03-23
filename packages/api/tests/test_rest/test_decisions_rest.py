"""Tests for the decisions REST controller."""

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
    # Mock embeddings to avoid loading the model
    mock_emb = MagicMock()
    mock_emb.embed_one.return_value = [0.0] * 384
    app.state.embeddings = mock_emb

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestDecisionsEndpoints:

    async def test_create_and_list(
        self, client: AsyncClient, test_project: dict
    ) -> None:
        """POST creates, GET lists with pagination."""
        pid = test_project["id"]

        resp = await client.post(
            f"/api/v1/projects/{pid}/decisions/",
            json={
                "title": "Use PostgreSQL",
                "body": "Strong consistency.",
                "tags": ["database"],
            },
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "Use PostgreSQL"

        resp = await client.get(f"/api/v1/projects/{pid}/decisions/")
        data = resp.json()
        assert data["total"] == 1
        assert data["data"][0]["title"] == "Use PostgreSQL"

    async def test_filter_by_tag(
        self, client: AsyncClient, test_project: dict
    ) -> None:
        """Tag filter works on list endpoint."""
        pid = test_project["id"]
        await client.post(
            f"/api/v1/projects/{pid}/decisions/",
            json={"title": "DB choice", "body": "pg", "tags": ["database"]},
        )
        await client.post(
            f"/api/v1/projects/{pid}/decisions/",
            json={"title": "Framework", "body": "fastapi", "tags": ["backend"]},
        )

        resp = await client.get(
            f"/api/v1/projects/{pid}/decisions/?tag=database"
        )
        data = resp.json()
        assert data["total"] == 1
        assert data["data"][0]["title"] == "DB choice"

    async def test_pagination(
        self, client: AsyncClient, test_project: dict
    ) -> None:
        """Pagination returns correct counts."""
        pid = test_project["id"]
        for i in range(3):
            await client.post(
                f"/api/v1/projects/{pid}/decisions/",
                json={"title": f"Decision {i}", "body": f"Body {i}"},
            )

        resp = await client.get(
            f"/api/v1/projects/{pid}/decisions/?limit=2&offset=0"
        )
        data = resp.json()
        assert len(data["data"]) == 2
        assert data["total"] == 3
