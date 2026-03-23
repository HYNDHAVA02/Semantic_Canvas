"""Tests for the settings REST controller (PAT + MCP config)."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def client(db_pool) -> AsyncClient:
    """Create an async test client."""
    from src.main import create_app

    app = create_app()
    app.state.db_pool = db_pool

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestSettingsEndpoints:

    async def test_create_token(
        self, client: AsyncClient, test_project: dict
    ) -> None:
        """POST /tokens creates a token and returns plaintext once."""
        pid = test_project["id"]
        resp = await client.post(
            f"/api/v1/projects/{pid}/tokens",
            json={"label": "My Agent Token"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["label"] == "My Agent Token"
        assert "token" in data  # plaintext returned once
        assert len(data["token"]) > 20
        assert "id" in data

    async def test_mcp_config(
        self, client: AsyncClient, test_project: dict
    ) -> None:
        """GET /mcp-config returns valid MCP server config."""
        pid = test_project["id"]
        resp = await client.get(f"/api/v1/projects/{pid}/mcp-config")
        assert resp.status_code == 200
        data = resp.json()
        assert "mcpServers" in data
        sc = data["mcpServers"]["semantic-canvas"]
        assert "/mcp/sse" in sc["url"]
        assert str(pid) in sc["headers"]["X-Project-Id"]
