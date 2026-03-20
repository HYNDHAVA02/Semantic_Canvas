"""Tests for the get_dead_code MCP tool."""

from __future__ import annotations

import json
from typing import Any

import asyncpg
import pytest
import pytest_asyncio

from src.mcp.tools.get_dead_code import GetDeadCodeParams, handle_get_dead_code
from src.repositories.entities import EntitiesRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> EntitiesRepository:
    """Create an EntitiesRepository backed by the test pool."""
    return EntitiesRepository(db_pool)


async def _seed_entity(
    db_pool: asyncpg.Pool,
    project_id: Any,
    name: str,
    kind: str = "function",
    is_dead_code: bool = False,
    file: str = "src/main.py",
    line: int | None = None,
) -> None:
    """Insert an entity directly for test setup."""
    metadata = {"is_dead_code": is_dead_code, "file": file}
    if line is not None:
        metadata["line"] = line
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO entities (project_id, name, kind, source, metadata)
            VALUES ($1, $2, $3, 'axon', $4::jsonb)
            """,
            project_id,
            name,
            kind,
            json.dumps(metadata),
        )


@pytest.mark.asyncio
class TestGetDeadCode:
    """Tests for the get_dead_code MCP tool handler."""

    async def test_empty_result(
        self, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """Returns empty list when no dead code exists."""
        params = GetDeadCodeParams(project_id=test_project["id"])
        result = await handle_get_dead_code(params, repo)
        assert result == []

    async def test_returns_dead_code(
        self, db_pool: asyncpg.Pool, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """Returns entities flagged as dead code."""
        await _seed_entity(
            db_pool, test_project["id"], "usedFunc", is_dead_code=False
        )
        await _seed_entity(
            db_pool,
            test_project["id"],
            "unusedHelper",
            is_dead_code=True,
            file="src/utils.py",
            line=42,
        )

        params = GetDeadCodeParams(project_id=test_project["id"])
        result = await handle_get_dead_code(params, repo)

        assert len(result) == 1
        assert result[0]["name"] == "unusedHelper"
        assert result[0]["file"] == "src/utils.py"
        assert result[0]["line"] == 42

    async def test_filter_by_kind(
        self, db_pool: asyncpg.Pool, repo: EntitiesRepository, test_project: dict
    ) -> None:
        """Kind filter returns only matching dead code entities."""
        await _seed_entity(
            db_pool, test_project["id"], "deadFunc", kind="function", is_dead_code=True
        )
        await _seed_entity(
            db_pool, test_project["id"], "DeadClass", kind="class", is_dead_code=True
        )

        params = GetDeadCodeParams(project_id=test_project["id"], kind="function")
        result = await handle_get_dead_code(params, repo)

        assert len(result) == 1
        assert result[0]["name"] == "deadFunc"
