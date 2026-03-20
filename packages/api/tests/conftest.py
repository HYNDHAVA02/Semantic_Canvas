"""Shared test fixtures for the API package."""

from __future__ import annotations

import asyncio
import os
from typing import AsyncGenerator
from uuid import UUID, uuid4

import asyncpg
import pytest
import pytest_asyncio

# Use test database
TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://canvas:canvas@localhost:5432/semantic_canvas_test",
)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    """Create a connection pool for the test database."""
    pool = await asyncpg.create_pool(TEST_DATABASE_URL, min_size=1, max_size=5)
    yield pool
    await pool.close()


@pytest_asyncio.fixture(autouse=True)
async def clean_db(db_pool: asyncpg.Pool) -> AsyncGenerator[None, None]:
    """Clean all tables before each test."""
    yield
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM document_chunks")
        await conn.execute("DELETE FROM documents")
        await conn.execute("DELETE FROM activity_log")
        await conn.execute("DELETE FROM conventions")
        await conn.execute("DELETE FROM decisions")
        await conn.execute("DELETE FROM relationships")
        await conn.execute("DELETE FROM entities")
        await conn.execute("DELETE FROM projects")


@pytest_asyncio.fixture
async def test_project(db_pool: asyncpg.Pool) -> dict:
    """Create a test project and return its data."""
    project_id = uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO projects (id, name, slug, description)
            VALUES ($1, $2, $3, $4)
            """,
            project_id,
            "Test Project",
            "test-project",
            "A test project for unit tests",
        )
    return {"id": project_id, "name": "Test Project", "slug": "test-project"}
