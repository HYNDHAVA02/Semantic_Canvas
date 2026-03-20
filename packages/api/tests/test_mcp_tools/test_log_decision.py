"""Tests for the log_decision MCP tool."""

from __future__ import annotations

from unittest.mock import MagicMock

import asyncpg
import pytest
import pytest_asyncio

from src.mcp.tools.log_decision import LogDecisionParams, handle_log_decision
from src.repositories.decisions import DecisionsRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> DecisionsRepository:
    """Create a DecisionsRepository backed by the test pool."""
    return DecisionsRepository(db_pool)


@pytest.fixture
def mock_embedding_service() -> MagicMock:
    """Mock embedding service returning a zero vector."""
    service = MagicMock()
    service.embed_one.return_value = [0.0] * 384
    return service


@pytest.mark.asyncio
class TestLogDecision:
    """Tests for the log_decision MCP tool handler."""

    async def test_creates_decision(
        self,
        repo: DecisionsRepository,
        test_project: dict,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Creates a decision and returns it with an ID."""
        params = LogDecisionParams(
            project_id=test_project["id"],
            title="Use PostgreSQL over MongoDB",
            body="We need strong consistency guarantees.",
        )
        result = await handle_log_decision(params, repo, mock_embedding_service)

        assert result is not None
        assert "id" in result
        assert result["title"] == "Use PostgreSQL over MongoDB"
        mock_embedding_service.embed_one.assert_called_once()

    async def test_optional_fields(
        self,
        repo: DecisionsRepository,
        test_project: dict,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Optional fields (decided_by, tags, source_ref) are stored."""
        params = LogDecisionParams(
            project_id=test_project["id"],
            title="Use FastAPI",
            body="Better async support.",
            decided_by="backend-team",
            tags=["backend", "framework"],
            source="manual",
            source_ref="https://github.com/org/repo/pull/42",
        )
        result = await handle_log_decision(params, repo, mock_embedding_service)

        assert result["title"] == "Use FastAPI"
        assert result["decided_by"] == "backend-team"
        assert result["tags"] == ["backend", "framework"]
        assert result["source"] == "manual"

    async def test_embedding_text(
        self,
        repo: DecisionsRepository,
        test_project: dict,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Embedding is generated from title + body."""
        params = LogDecisionParams(
            project_id=test_project["id"],
            title="Use Redis",
            body="For caching.",
        )
        await handle_log_decision(params, repo, mock_embedding_service)

        mock_embedding_service.embed_one.assert_called_once_with(
            "Use Redis For caching."
        )
