"""Tests for the decisions repository."""

from __future__ import annotations

import asyncpg
import pytest
import pytest_asyncio

from src.repositories.decisions import DecisionsRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> DecisionsRepository:
    return DecisionsRepository(db_pool)


@pytest.mark.asyncio
class TestDecisionsRepository:

    async def test_list_returns_seeded_decisions(
        self, repo: DecisionsRepository, test_project: dict
    ) -> None:
        """List returns all decisions for a project."""
        await repo.create(
            project_id=test_project["id"],
            title="Use PostgreSQL over MongoDB",
            body="We need strong consistency guarantees.",
            decided_by="team-lead",
            tags=["database"],
        )
        await repo.create(
            project_id=test_project["id"],
            title="Use FastAPI over Flask",
            body="Better async support and auto-generated docs.",
            decided_by="backend-team",
            tags=["backend", "framework"],
        )

        result, total = await repo.list_by_project(test_project["id"])
        assert len(result) == 2
        assert total == 2
        titles = [d["title"] for d in result]
        assert "Use PostgreSQL over MongoDB" in titles
        assert "Use FastAPI over Flask" in titles

    async def test_filter_by_tag(
        self, repo: DecisionsRepository, test_project: dict
    ) -> None:
        """Tag filter returns only matching decisions."""
        await repo.create(
            project_id=test_project["id"],
            title="Use PostgreSQL",
            body="Strong consistency.",
            tags=["database"],
        )
        await repo.create(
            project_id=test_project["id"],
            title="Use FastAPI",
            body="Async support.",
            tags=["backend"],
        )

        result, total = await repo.list_by_project(test_project["id"], tag="database")
        assert len(result) == 1
        assert total == 1
        assert result[0]["title"] == "Use PostgreSQL"

    async def test_filter_by_source(
        self, repo: DecisionsRepository, test_project: dict
    ) -> None:
        """Source filter returns only matching decisions."""
        await repo.create(
            project_id=test_project["id"],
            title="Manual decision",
            body="Decided manually.",
            source="manual",
        )
        await repo.create(
            project_id=test_project["id"],
            title="Agent decision",
            body="Decided by agent.",
            source="agent",
        )

        result, total = await repo.list_by_project(test_project["id"], source="agent")
        assert len(result) == 1
        assert total == 1
        assert result[0]["title"] == "Agent decision"

    async def test_empty_project(
        self, repo: DecisionsRepository, test_project: dict
    ) -> None:
        """List on empty project returns empty list."""
        result, total = await repo.list_by_project(test_project["id"])
        assert result == []
        assert total == 0
