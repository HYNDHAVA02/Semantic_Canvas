"""Tests for the log_convention MCP tool."""

from __future__ import annotations

from unittest.mock import MagicMock

import asyncpg
import pytest
import pytest_asyncio

from src.mcp.tools.log_convention import LogConventionParams, handle_log_convention
from src.repositories.conventions import ConventionsRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> ConventionsRepository:
    """Create a ConventionsRepository backed by the test pool."""
    return ConventionsRepository(db_pool)


@pytest.fixture
def mock_embedding_service() -> MagicMock:
    """Mock embedding service returning a zero vector."""
    service = MagicMock()
    service.embed_one.return_value = [0.0] * 384
    return service


@pytest.mark.asyncio
class TestLogConvention:
    """Tests for the log_convention MCP tool handler."""

    async def test_creates_convention(
        self,
        repo: ConventionsRepository,
        test_project: dict,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Creates a convention and returns it with an ID."""
        params = LogConventionParams(
            project_id=test_project["id"],
            title="Always use type hints",
            body="All function signatures must have type annotations.",
        )
        result = await handle_log_convention(params, repo, mock_embedding_service)

        assert result is not None
        assert "id" in result
        assert result["title"] == "Always use type hints"
        mock_embedding_service.embed_one.assert_called_once()

    async def test_scope_field(
        self,
        repo: ConventionsRepository,
        test_project: dict,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Scope field is stored correctly."""
        params = LogConventionParams(
            project_id=test_project["id"],
            title="Use kebab-case for files",
            body="TypeScript files use kebab-case naming.",
            scope="frontend",
            tags=["naming"],
        )
        result = await handle_log_convention(params, repo, mock_embedding_service)

        assert result["title"] == "Use kebab-case for files"
        assert result["scope"] == "frontend"
        assert result["tags"] == ["naming"]

    async def test_embedding_text(
        self,
        repo: ConventionsRepository,
        test_project: dict,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Embedding is generated from title + body."""
        params = LogConventionParams(
            project_id=test_project["id"],
            title="No ORM",
            body="Raw SQL only.",
        )
        await handle_log_convention(params, repo, mock_embedding_service)

        mock_embedding_service.embed_one.assert_called_once_with(
            "No ORM Raw SQL only."
        )
