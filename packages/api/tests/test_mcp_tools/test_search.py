"""Tests for the search MCP tool."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

if TYPE_CHECKING:
    from uuid import UUID

    import asyncpg

from src.mcp.tools.search import SearchParams, handle_search
from src.repositories.search import SearchRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> SearchRepository:
    """Create a SearchRepository backed by the test pool."""
    return SearchRepository(db_pool)


@pytest.fixture
def embedding_service() -> MagicMock:
    """Mock embedding service that returns a deterministic vector."""
    service = MagicMock()
    service.embed_one.return_value = [0.5] * 384
    return service


def _fake_embedding(seed: float = 0.5) -> list[float]:
    return [seed] * 384


def _embedding_str(embedding: list[float]) -> str:
    """Convert embedding list to pgvector string format."""
    return "[" + ",".join(str(v) for v in embedding) + "]"


async def _seed_entity(
    db_pool: asyncpg.Pool,
    project_id: UUID,
    name: str,
    embedding: list[float] | None = None,
) -> None:
    """Insert an entity with an embedding."""
    emb = _embedding_str(embedding or _fake_embedding())
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO entities (project_id, name, kind, embedding)
            VALUES ($1, $2, 'service', $3::vector)
            """,
            project_id,
            name,
            emb,
        )


async def _seed_decision(
    db_pool: asyncpg.Pool,
    project_id: UUID,
    title: str,
    body: str,
    embedding: list[float] | None = None,
) -> None:
    """Insert a decision with an embedding."""
    emb = _embedding_str(embedding or _fake_embedding())
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO decisions (project_id, title, body, embedding)
            VALUES ($1, $2, $3, $4::vector)
            """,
            project_id,
            title,
            body,
            emb,
        )


@pytest.mark.asyncio
class TestSearchTool:
    """Tests for the search MCP tool handler."""

    async def test_empty_project_returns_empty(
        self,
        repo: SearchRepository,
        embedding_service: MagicMock,
        test_project: dict,
    ) -> None:
        """Returns empty list when project has no data."""
        params = SearchParams(
            project_id=test_project["id"],
            query="authentication",
        )
        result = await handle_search(params, repo, embedding_service)
        assert result == []
        embedding_service.embed_one.assert_called_once_with("authentication")

    async def test_returns_matching_entities(
        self,
        db_pool: asyncpg.Pool,
        repo: SearchRepository,
        embedding_service: MagicMock,
        test_project: dict,
    ) -> None:
        """Returns entities that match the query."""
        await _seed_entity(db_pool, test_project["id"], "AuthService")

        params = SearchParams(
            project_id=test_project["id"],
            query="auth",
            tables=["entities"],
        )
        result = await handle_search(params, repo, embedding_service)

        assert len(result) == 1
        assert result[0]["title"] == "AuthService"
        assert result[0]["table_name"] == "entities"

    async def test_result_shape(
        self,
        db_pool: asyncpg.Pool,
        repo: SearchRepository,
        embedding_service: MagicMock,
        test_project: dict,
    ) -> None:
        """Each result has the expected unified shape."""
        await _seed_entity(db_pool, test_project["id"], "CacheService")

        params = SearchParams(
            project_id=test_project["id"],
            query="cache",
        )
        result = await handle_search(params, repo, embedding_service)

        assert len(result) >= 1
        item = result[0]
        expected_keys = {"id", "table_name", "title", "snippet", "score", "metadata"}
        assert set(item.keys()) == expected_keys

    async def test_table_filter_respected(
        self,
        db_pool: asyncpg.Pool,
        repo: SearchRepository,
        embedding_service: MagicMock,
        test_project: dict,
    ) -> None:
        """Tables filter limits which tables are searched."""
        await _seed_entity(db_pool, test_project["id"], "Svc")
        await _seed_decision(db_pool, test_project["id"], "Dec", "body")

        params = SearchParams(
            project_id=test_project["id"],
            query="test",
            tables=["decisions"],
        )
        result = await handle_search(params, repo, embedding_service)

        table_names = {r["table_name"] for r in result}
        assert "entities" not in table_names

    async def test_limit_applied(
        self,
        db_pool: asyncpg.Pool,
        repo: SearchRepository,
        embedding_service: MagicMock,
        test_project: dict,
    ) -> None:
        """Limit caps results."""
        for i in range(5):
            await _seed_entity(db_pool, test_project["id"], f"Svc{i}")

        params = SearchParams(
            project_id=test_project["id"],
            query="service",
            tables=["entities"],
            limit=2,
        )
        result = await handle_search(params, repo, embedding_service)

        assert len(result) <= 2

    async def test_cross_table_results(
        self,
        db_pool: asyncpg.Pool,
        repo: SearchRepository,
        embedding_service: MagicMock,
        test_project: dict,
    ) -> None:
        """Results span multiple tables by default."""
        await _seed_entity(db_pool, test_project["id"], "AuthService")
        await _seed_decision(db_pool, test_project["id"], "Use JWT", "JWT for auth")

        params = SearchParams(
            project_id=test_project["id"],
            query="authentication",
        )
        result = await handle_search(params, repo, embedding_service)

        table_names = {r["table_name"] for r in result}
        assert len(table_names) >= 2
