"""Tests for the log_activity MCP tool."""

from __future__ import annotations

from unittest.mock import MagicMock

import asyncpg
import pytest
import pytest_asyncio

from src.mcp.tools.log_activity import LogActivityParams, handle_log_activity
from src.repositories.activity import ActivityRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> ActivityRepository:
    """Create an ActivityRepository backed by the test pool."""
    return ActivityRepository(db_pool)


@pytest.fixture
def mock_embedding_service() -> MagicMock:
    """Mock embedding service returning a zero vector."""
    service = MagicMock()
    service.embed_one.return_value = [0.0] * 384
    return service


@pytest.mark.asyncio
class TestLogActivity:
    """Tests for the log_activity MCP tool handler."""

    async def test_creates_activity(
        self,
        repo: ActivityRepository,
        test_project: dict,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Creates an activity entry and returns it with an ID."""
        params = LogActivityParams(
            project_id=test_project["id"],
            summary="Deployed v2.0 to production",
            source="github",
        )
        result = await handle_log_activity(params, repo, mock_embedding_service)

        assert result is not None
        assert "id" in result
        assert result["summary"] == "Deployed v2.0 to production"
        assert result["source"] == "github"
        mock_embedding_service.embed_one.assert_called_once()

    async def test_optional_fields(
        self,
        repo: ActivityRepository,
        test_project: dict,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Optional fields (detail, actor, source_ref) are stored."""
        params = LogActivityParams(
            project_id=test_project["id"],
            summary="Refactored auth module",
            source="agent",
            detail="Extracted JWT verification into a separate service class.",
            actor="claude",
            source_ref="https://github.com/org/repo/commit/abc123",
        )
        result = await handle_log_activity(params, repo, mock_embedding_service)

        assert result["summary"] == "Refactored auth module"
        assert result["detail"] == "Extracted JWT verification into a separate service class."
        assert result["actor"] == "claude"

    async def test_embedding_text_with_detail(
        self,
        repo: ActivityRepository,
        test_project: dict,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Embedding includes both summary and detail."""
        params = LogActivityParams(
            project_id=test_project["id"],
            summary="Fixed bug",
            source="manual",
            detail="Null pointer in auth flow.",
        )
        await handle_log_activity(params, repo, mock_embedding_service)

        mock_embedding_service.embed_one.assert_called_once_with(
            "Fixed bug Null pointer in auth flow."
        )

    async def test_embedding_text_without_detail(
        self,
        repo: ActivityRepository,
        test_project: dict,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Embedding uses only summary when detail is None."""
        params = LogActivityParams(
            project_id=test_project["id"],
            summary="Quick fix",
            source="manual",
        )
        await handle_log_activity(params, repo, mock_embedding_service)

        mock_embedding_service.embed_one.assert_called_once_with("Quick fix")
