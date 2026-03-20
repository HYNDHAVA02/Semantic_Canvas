"""Tests for the get_entity MCP tool."""

from __future__ import annotations

from uuid import uuid4

import asyncpg
import pytest
import pytest_asyncio
from pydantic import ValidationError

from src.mcp.tools.get_entity import GetEntityParams, handle_get_entity
from src.repositories.entities import EntitiesRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> EntitiesRepository:
    """Create an EntitiesRepository backed by the test pool."""
    return EntitiesRepository(db_pool)


@pytest.mark.asyncio
class TestGetEntity:
    """Tests for the get_entity MCP tool handler."""

    async def test_get_by_name(
        self, db_pool: asyncpg.Pool, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """Lookup by project_id + name returns the correct entity."""
        created = await repo.create(
            project_id=test_project["id"],
            name="AuthService",
            kind="service",
        )

        params = GetEntityParams(
            project_id=test_project["id"], name="AuthService"
        )
        result = await handle_get_entity(params, repo)

        assert result is not None
        assert result["name"] == "AuthService"
        assert result["id"] == created["id"]

    async def test_get_by_id(
        self, db_pool: asyncpg.Pool, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """Lookup by entity_id returns the correct entity."""
        created = await repo.create(
            project_id=test_project["id"],
            name="PaymentService",
            kind="service",
        )

        params = GetEntityParams(entity_id=created["id"])
        result = await handle_get_entity(params, repo)

        assert result is not None
        assert result["name"] == "PaymentService"

    async def test_not_found_returns_none(
        self, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """Returns None when entity does not exist."""
        params = GetEntityParams(entity_id=uuid4())
        result = await handle_get_entity(params, repo)
        assert result is None



class TestGetEntityValidation:
    """Pydantic validation tests (sync — no DB needed)."""

    def test_validation_error_when_no_key(self) -> None:
        """Raises ValidationError when neither entity_id nor name+project_id given."""
        with pytest.raises(ValidationError, match="Provide either entity_id"):
            GetEntityParams()

    def test_validation_error_name_without_project(self) -> None:
        """Raises ValidationError when name given without project_id."""
        with pytest.raises(ValidationError, match="Provide either entity_id"):
            GetEntityParams(name="AuthService")
