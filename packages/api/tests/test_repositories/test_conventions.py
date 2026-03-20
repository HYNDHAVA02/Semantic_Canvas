"""Tests for the conventions repository."""

from __future__ import annotations

import asyncpg
import pytest
import pytest_asyncio

from src.repositories.conventions import ConventionsRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> ConventionsRepository:
    return ConventionsRepository(db_pool)


@pytest.mark.asyncio
class TestConventionsRepository:

    async def test_list_returns_seeded_conventions(
        self, repo: ConventionsRepository, test_project: dict
    ) -> None:
        """List returns all active conventions for a project."""
        await repo.create(
            project_id=test_project["id"],
            title="Always use type hints",
            body="All function signatures must have type hints.",
            scope="backend",
        )
        await repo.create(
            project_id=test_project["id"],
            title="Kebab-case for TypeScript files",
            body="Use kebab-case naming for all .ts and .tsx files.",
            scope="frontend",
        )

        result = await repo.list_by_project(test_project["id"])
        assert len(result) == 2
        titles = [c["title"] for c in result]
        assert "Always use type hints" in titles

    async def test_filter_by_scope(
        self, repo: ConventionsRepository, test_project: dict
    ) -> None:
        """Scope filter returns only matching conventions."""
        await repo.create(
            project_id=test_project["id"],
            title="Backend convention",
            body="Backend only.",
            scope="backend",
        )
        await repo.create(
            project_id=test_project["id"],
            title="Frontend convention",
            body="Frontend only.",
            scope="frontend",
        )

        result = await repo.list_by_project(test_project["id"], scope="backend")
        assert len(result) == 1
        assert result[0]["title"] == "Backend convention"

    async def test_active_only_filter(
        self, repo: ConventionsRepository, test_project: dict
    ) -> None:
        """active_only filter excludes inactive conventions."""
        await repo.create(
            project_id=test_project["id"],
            title="Active rule",
            body="Still applies.",
            is_active=True,
        )
        await repo.create(
            project_id=test_project["id"],
            title="Deprecated rule",
            body="No longer applies.",
            is_active=False,
        )

        # Default: only active
        result = await repo.list_by_project(test_project["id"])
        assert len(result) == 1
        assert result[0]["title"] == "Active rule"

        # Include inactive
        result = await repo.list_by_project(test_project["id"], active_only=False)
        assert len(result) == 2

    async def test_empty_project(
        self, repo: ConventionsRepository, test_project: dict
    ) -> None:
        """List on empty project returns empty list."""
        result = await repo.list_by_project(test_project["id"])
        assert result == []
