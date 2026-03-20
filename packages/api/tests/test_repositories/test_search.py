"""Tests for the search repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

if TYPE_CHECKING:
    from uuid import UUID

    import asyncpg

from src.repositories.search import SEARCHABLE_TABLES, SearchRepository


@pytest_asyncio.fixture
async def repo(db_pool: asyncpg.Pool) -> SearchRepository:
    return SearchRepository(db_pool)


def _fake_embedding(seed: float = 0.1) -> list[float]:
    """Generate a deterministic 384-dim embedding for testing."""
    return [seed] * 384


def _embedding_str(embedding: list[float]) -> str:
    """Convert embedding list to pgvector string format."""
    return "[" + ",".join(str(v) for v in embedding) + "]"


async def _seed_entity(
    db_pool: asyncpg.Pool,
    project_id: UUID,
    name: str,
    kind: str = "service",
    embedding: list[float] | None = None,
) -> UUID:
    """Insert an entity with an embedding and return its ID."""
    emb = _embedding_str(embedding or _fake_embedding())
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO entities (project_id, name, kind, embedding)
            VALUES ($1, $2, $3, $4::vector)
            RETURNING id
            """,
            project_id,
            name,
            kind,
            emb,
        )
        return row["id"]  # type: ignore[index,return-value]


async def _seed_decision(
    db_pool: asyncpg.Pool,
    project_id: UUID,
    title: str,
    body: str,
    embedding: list[float] | None = None,
) -> UUID:
    """Insert a decision with an embedding and return its ID."""
    emb = _embedding_str(embedding or _fake_embedding())
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO decisions (project_id, title, body, embedding)
            VALUES ($1, $2, $3, $4::vector)
            RETURNING id
            """,
            project_id,
            title,
            body,
            emb,
        )
        return row["id"]  # type: ignore[index,return-value]


async def _seed_convention(
    db_pool: asyncpg.Pool,
    project_id: UUID,
    title: str,
    body: str,
    embedding: list[float] | None = None,
) -> UUID:
    """Insert a convention with an embedding and return its ID."""
    emb = _embedding_str(embedding or _fake_embedding())
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO conventions (project_id, title, body, embedding)
            VALUES ($1, $2, $3, $4::vector)
            RETURNING id
            """,
            project_id,
            title,
            body,
            emb,
        )
        return row["id"]  # type: ignore[index,return-value]


async def _seed_activity(
    db_pool: asyncpg.Pool,
    project_id: UUID,
    summary: str,
    source: str = "manual",
    embedding: list[float] | None = None,
) -> UUID:
    """Insert an activity log entry with an embedding and return its ID."""
    emb = _embedding_str(embedding or _fake_embedding())
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO activity_log (project_id, summary, source, embedding)
            VALUES ($1, $2, $3, $4::vector)
            RETURNING id
            """,
            project_id,
            summary,
            source,
            emb,
        )
        return row["id"]  # type: ignore[index,return-value]


async def _seed_document_chunk(
    db_pool: asyncpg.Pool,
    project_id: UUID,
    content: str,
    chunk_index: int = 0,
    embedding: list[float] | None = None,
) -> UUID:
    """Insert a document chunk with an embedding and return its ID."""
    async with db_pool.acquire() as conn:
        doc_row = await conn.fetchrow(
            """
            INSERT INTO documents (project_id, title)
            VALUES ($1, 'Test Doc')
            RETURNING id
            """,
            project_id,
        )
        doc_id = doc_row["id"]  # type: ignore[index]
        emb = _embedding_str(embedding or _fake_embedding())
        row = await conn.fetchrow(
            """
            INSERT INTO document_chunks
                (document_id, project_id, content, chunk_index, embedding)
            VALUES ($1, $2, $3, $4, $5::vector)
            RETURNING id
            """,
            doc_id,
            project_id,
            content,
            chunk_index,
            emb,
        )
        return row["id"]  # type: ignore[index,return-value]


@pytest.mark.asyncio
class TestSearchRepository:
    """Tests for the SearchRepository."""

    async def test_empty_project_returns_no_results(
        self, repo: SearchRepository, test_project: dict
    ) -> None:
        """Search on an empty project returns empty list."""
        results = await repo.hybrid_search(
            project_id=test_project["id"],
            query_embedding=_fake_embedding(),
            query_text="anything",
        )
        assert results == []

    async def test_finds_entity_by_semantic_similarity(
        self,
        db_pool: asyncpg.Pool,
        repo: SearchRepository,
        test_project: dict,
    ) -> None:
        """Entities with matching embeddings appear in results."""
        emb = _fake_embedding(0.5)
        await _seed_entity(db_pool, test_project["id"], "PaymentService", embedding=emb)

        results = await repo.hybrid_search(
            project_id=test_project["id"],
            query_embedding=emb,
            query_text="payment",
            tables=["entities"],
        )

        assert len(results) == 1
        assert results[0].title == "PaymentService"
        assert results[0].table_name == "entities"
        assert results[0].score > 0

    async def test_searches_across_multiple_tables(
        self,
        db_pool: asyncpg.Pool,
        repo: SearchRepository,
        test_project: dict,
    ) -> None:
        """Results come from multiple tables when no filter is applied."""
        emb = _fake_embedding(0.5)
        await _seed_entity(
            db_pool, test_project["id"], "AuthService", embedding=emb
        )
        await _seed_decision(
            db_pool, test_project["id"], "Use JWT", "We chose JWT for auth.", embedding=emb
        )

        results = await repo.hybrid_search(
            project_id=test_project["id"],
            query_embedding=emb,
            query_text="auth",
        )

        table_names = {r.table_name for r in results}
        assert "entities" in table_names
        assert "decisions" in table_names

    async def test_table_filter_limits_search(
        self,
        db_pool: asyncpg.Pool,
        repo: SearchRepository,
        test_project: dict,
    ) -> None:
        """When tables filter is set, only those tables are searched."""
        emb = _fake_embedding(0.5)
        await _seed_entity(db_pool, test_project["id"], "CacheService", embedding=emb)
        await _seed_decision(
            db_pool, test_project["id"], "Use Redis", "Redis for caching.", embedding=emb
        )

        results = await repo.hybrid_search(
            project_id=test_project["id"],
            query_embedding=emb,
            query_text="cache",
            tables=["decisions"],
        )

        table_names = {r.table_name for r in results}
        assert "decisions" in table_names
        assert "entities" not in table_names

    async def test_invalid_table_raises_error(
        self, repo: SearchRepository, test_project: dict
    ) -> None:
        """Passing an unknown table name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown searchable table"):
            await repo.hybrid_search(
                project_id=test_project["id"],
                query_embedding=_fake_embedding(),
                query_text="test",
                tables=["nonexistent"],
            )

    async def test_limit_caps_results(
        self,
        db_pool: asyncpg.Pool,
        repo: SearchRepository,
        test_project: dict,
    ) -> None:
        """Limit parameter caps the number of results returned."""
        emb = _fake_embedding(0.5)
        for i in range(5):
            await _seed_entity(
                db_pool, test_project["id"], f"Service{i}", embedding=emb
            )

        results = await repo.hybrid_search(
            project_id=test_project["id"],
            query_embedding=emb,
            query_text="service",
            tables=["entities"],
            limit=3,
        )

        assert len(results) <= 3

    async def test_results_sorted_by_score_descending(
        self,
        db_pool: asyncpg.Pool,
        repo: SearchRepository,
        test_project: dict,
    ) -> None:
        """Results are ordered by score, highest first."""
        # Different embeddings → different similarity scores
        await _seed_entity(
            db_pool, test_project["id"], "Close",
            embedding=_fake_embedding(0.9),
        )
        await _seed_entity(
            db_pool, test_project["id"], "Far",
            embedding=_fake_embedding(0.1),
        )

        results = await repo.hybrid_search(
            project_id=test_project["id"],
            query_embedding=_fake_embedding(0.9),
            query_text="close",
            tables=["entities"],
        )

        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    async def test_result_shape(
        self,
        db_pool: asyncpg.Pool,
        repo: SearchRepository,
        test_project: dict,
    ) -> None:
        """Result dict has the expected keys."""
        emb = _fake_embedding(0.5)
        await _seed_entity(db_pool, test_project["id"], "TestEntity", embedding=emb)

        results = await repo.hybrid_search(
            project_id=test_project["id"],
            query_embedding=emb,
            query_text="test",
            tables=["entities"],
        )

        d = results[0].to_dict()
        assert set(d.keys()) == {"id", "table_name", "title", "snippet", "score", "metadata"}
        assert d["table_name"] == "entities"

    async def test_all_five_tables_searchable(
        self,
        db_pool: asyncpg.Pool,
        repo: SearchRepository,
        test_project: dict,
    ) -> None:
        """All five searchable tables return results when seeded."""
        emb = _fake_embedding(0.5)
        await _seed_entity(db_pool, test_project["id"], "Svc", embedding=emb)
        await _seed_decision(db_pool, test_project["id"], "Dec", "body", embedding=emb)
        await _seed_convention(db_pool, test_project["id"], "Conv", "body", embedding=emb)
        await _seed_activity(db_pool, test_project["id"], "Act", embedding=emb)
        await _seed_document_chunk(db_pool, test_project["id"], "Chunk", embedding=emb)

        results = await repo.hybrid_search(
            project_id=test_project["id"],
            query_embedding=emb,
            query_text="test",
        )

        table_names = {r.table_name for r in results}
        assert table_names == set(SEARCHABLE_TABLES)
