"""Search repository — cross-table hybrid search (semantic + keyword).

Searches across entities, decisions, conventions, activity_log, and
document_chunks in parallel. Combines cosine similarity (0.7 weight)
with trigram keyword matching (0.3 weight) for ranked results.
"""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from uuid import UUID

    import asyncpg


# Scoring weights
SEMANTIC_WEIGHT = 0.7
KEYWORD_WEIGHT = 0.3

# Tables that support search and their text columns
SEARCHABLE_TABLES = (
    "entities",
    "decisions",
    "conventions",
    "activity_log",
    "document_chunks",
)


class SearchResult:
    """Unified search result across all tables."""

    __slots__ = ("metadata", "result_id", "score", "snippet", "table_name", "title")

    def __init__(
        self,
        *,
        result_id: UUID,
        table_name: str,
        title: str,
        snippet: str,
        score: float,
        metadata: dict[str, Any],
    ) -> None:
        self.result_id = result_id
        self.table_name = table_name
        self.title = title
        self.snippet = snippet
        self.score = score
        self.metadata = metadata

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for MCP/REST responses."""
        return {
            "id": str(self.result_id),
            "table_name": self.table_name,
            "title": self.title,
            "snippet": self.snippet,
            "score": round(self.score, 4),
            "metadata": self.metadata,
        }


class SearchRepository:
    """Cross-table hybrid search using vector similarity and trigram matching."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def hybrid_search(
        self,
        project_id: UUID,
        query_embedding: list[float],
        query_text: str,
        tables: list[str] | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        """Run hybrid search across multiple tables in parallel.

        Combines cosine similarity (0.7) with trigram keyword matching (0.3).
        Results are merged, deduplicated, and sorted by combined score.
        """
        target_tables = tables or list(SEARCHABLE_TABLES)
        # Validate table names to prevent injection
        for t in target_tables:
            if t not in SEARCHABLE_TABLES:
                msg = f"Unknown searchable table: {t}"
                raise ValueError(msg)

        tasks = [
            self._search_table(project_id, t, query_embedding, query_text, limit)
            for t in target_tables
        ]
        results_per_table = await asyncio.gather(*tasks)

        # Flatten, sort by score descending, take top N
        all_results: list[SearchResult] = []
        for table_results in results_per_table:
            all_results.extend(table_results)

        all_results.sort(key=lambda r: r.score, reverse=True)
        return all_results[:limit]

    async def _search_table(
        self,
        project_id: UUID,
        table_name: str,
        query_embedding: list[float],
        query_text: str,
        limit: int,
    ) -> list[SearchResult]:
        """Search a single table with hybrid scoring."""
        query = _build_query(table_name)
        # asyncpg requires vector as string '[0.1,0.2,...]'
        embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                query,
                project_id,
                embedding_str,
                query_text,
                SEMANTIC_WEIGHT,
                KEYWORD_WEIGHT,
                limit,
            )
        return [
            SearchResult(
                result_id=row["id"],
                table_name=table_name,
                title=row["title"],
                snippet=row["snippet"],
                score=float(row["score"]),
                metadata=_parse_metadata(row["metadata"]),
            )
            for row in rows
        ]


def _parse_metadata(raw: object) -> dict[str, Any]:
    """Parse metadata from asyncpg — may be dict, str, or None."""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        return json.loads(raw)  # type: ignore[no-any-return]
    return {}


def _build_query(table_name: str) -> str:
    """Build a hybrid search query for the given table.

    Each table maps to different title/snippet/metadata columns.
    Keyword score uses COALESCE so tables without trigram indexes
    gracefully return 0 for the keyword component.
    """
    col_map = _COLUMN_MAP[table_name]
    title_col = col_map["title"]
    snippet_col = col_map["snippet"]
    metadata_expr = col_map["metadata"]
    keyword_col = col_map.get("keyword")

    # Cosine similarity: 1 - cosine_distance (pgvector <=> operator)
    # Trigram similarity: similarity() from pg_trgm
    keyword_expr = (
        f"COALESCE(similarity({keyword_col}, $3::text), 0)"
        if keyword_col
        else "0 * LENGTH($3::text)"  # reference $3 so asyncpg can infer its type
    )

    return f"""
        SELECT
            id,
            {title_col} AS title,
            LEFT({snippet_col}, 200) AS snippet,
            {metadata_expr} AS metadata,
            (
                $4::float8 * (1 - (embedding <=> $2::vector))
                + $5::float8 * {keyword_expr}
            ) AS score
        FROM {table_name}
        WHERE project_id = $1
          AND embedding IS NOT NULL
        ORDER BY score DESC
        LIMIT $6
    """


# Column mappings for each searchable table
_COLUMN_MAP: dict[str, dict[str, str]] = {
    "entities": {
        "title": "name",
        "snippet": "COALESCE(metadata->>'description', name)",
        "metadata": "jsonb_build_object('kind', kind, 'source', source, 'is_active', is_active)",
        "keyword": "name",
    },
    "decisions": {
        "title": "title",
        "snippet": "body",
        "metadata": "jsonb_build_object('decided_by', decided_by, 'decided_at', decided_at, 'tags', tags)",
        "keyword": "title",
    },
    "conventions": {
        "title": "title",
        "snippet": "body",
        "metadata": "jsonb_build_object('scope', scope, 'is_active', is_active, 'tags', tags)",
    },
    "activity_log": {
        "title": "summary",
        "snippet": "COALESCE(detail, summary)",
        "metadata": "jsonb_build_object('source', source, 'actor', actor, 'occurred_at', occurred_at)",
    },
    "document_chunks": {
        "title": "CONCAT('Chunk #', chunk_index)",
        "snippet": "content",
        "metadata": "jsonb_build_object('document_id', document_id, 'chunk_index', chunk_index)",
    },
}
