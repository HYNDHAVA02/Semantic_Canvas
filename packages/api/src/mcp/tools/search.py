"""MCP tool: search — cross-table semantic + keyword search."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.mcp.registry import ToolDefinition
from src.repositories.search import SEARCHABLE_TABLES, SearchRepository

if TYPE_CHECKING:
    from src.embeddings.service import EmbeddingService


class SearchParams(BaseModel):
    """Input parameters for the search tool."""

    project_id: UUID = Field(description="Project to search in.")
    query: str = Field(
        description="Natural language search query.",
        min_length=1,
        max_length=500,
    )
    tables: list[str] | None = Field(
        default=None,
        description=(
            "Optional list of tables to search. "
            f"Allowed: {', '.join(SEARCHABLE_TABLES)}. "
            "Defaults to all tables."
        ),
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of results to return.",
    )


async def handle_search(
    params: SearchParams,
    repo: SearchRepository,
    embedding_service: EmbeddingService,
) -> list[dict[str, Any]]:
    """Search across project knowledge using hybrid semantic + keyword matching."""
    query_embedding = embedding_service.embed_one(params.query)

    results = await repo.hybrid_search(
        project_id=params.project_id,
        query_embedding=query_embedding,
        query_text=params.query,
        tables=params.tables,
        limit=params.limit,
    )

    return [r.to_dict() for r in results]


TOOL = ToolDefinition(
    name="search",
    description=(
        "Search across all project knowledge — entities, decisions, conventions, "
        "activity log, and document chunks. Uses hybrid semantic + keyword matching "
        "to find the most relevant results. Optionally filter to specific tables."
    ),
    params_model=SearchParams,
    handler=handle_search,
)
