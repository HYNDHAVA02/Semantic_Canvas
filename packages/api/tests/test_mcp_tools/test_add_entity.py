"""Tests for the add_entity MCP tool."""

from __future__ import annotations

from unittest.mock import MagicMock

import asyncpg
import pytest
import pytest_asyncio

from src.mcp.tools.add_entity import AddEntityParams, handle_add_entity
from src.repositories.entities import EntitiesRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> EntitiesRepository:
    """Create an EntitiesRepository backed by the test pool."""
    return EntitiesRepository(db_pool)


@pytest.fixture
def mock_embedding_service() -> MagicMock:
    """Mock embedding service returning a zero vector."""
    service = MagicMock()
    service.embed_one.return_value = [0.0] * 384
    return service


@pytest.mark.asyncio
class TestAddEntity:
    """Tests for the add_entity MCP tool handler."""

    async def test_creates_entity(
        self,
        repo: EntitiesRepository,
        test_project: dict,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Creates an entity and returns it with an ID."""
        params = AddEntityParams(
            project_id=test_project["id"],
            name="PaymentService",
            kind="service",
        )
        result = await handle_add_entity(params, repo, mock_embedding_service)

        assert result is not None
        assert "id" in result
        assert result["name"] == "PaymentService"
        assert result["kind"] == "service"
        mock_embedding_service.embed_one.assert_called_once()

    async def test_upsert_merges_metadata(
        self,
        repo: EntitiesRepository,
        test_project: dict,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Upserting an existing entity merges metadata."""
        params1 = AddEntityParams(
            project_id=test_project["id"],
            name="AuthService",
            kind="service",
            metadata={"version": "1.0"},
        )
        first = await handle_add_entity(params1, repo, mock_embedding_service)

        params2 = AddEntityParams(
            project_id=test_project["id"],
            name="AuthService",
            kind="service",
            metadata={"version": "2.0"},
        )
        second = await handle_add_entity(params2, repo, mock_embedding_service)

        assert first["id"] == second["id"]

    async def test_embedding_text(
        self,
        repo: EntitiesRepository,
        test_project: dict,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Embedding is generated from name + kind."""
        params = AddEntityParams(
            project_id=test_project["id"],
            name="verify_token",
            kind="function",
        )
        await handle_add_entity(params, repo, mock_embedding_service)

        mock_embedding_service.embed_one.assert_called_once_with(
            "verify_token function"
        )

    async def test_source_defaults_to_agent(
        self,
        repo: EntitiesRepository,
        test_project: dict,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Source defaults to 'agent' for MCP-created entities."""
        params = AddEntityParams(
            project_id=test_project["id"],
            name="CacheService",
            kind="service",
        )
        result = await handle_add_entity(params, repo, mock_embedding_service)

        assert result["source"] == "agent"
