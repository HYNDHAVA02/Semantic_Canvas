"""Search controller — hybrid semantic + keyword search."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from src.repositories.search import SearchRepository

router = APIRouter()


@router.get("/")
async def search(
    request: Request,
    project_id: UUID,
    q: str = "",
    tables: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Hybrid search across all project knowledge.

    Args:
        q: Search query string.
        tables: Comma-separated list of tables to search (optional).
        limit: Max results to return.
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    table_list = [t.strip() for t in tables.split(",")] if tables else None

    embedding_service = request.app.state.embeddings
    query_embedding = embedding_service.embed_one(q)

    repo = SearchRepository(request.app.state.db_pool)
    results = await repo.hybrid_search(
        project_id=project_id,
        query_embedding=query_embedding,
        query_text=q,
        tables=table_list,
        limit=limit,
    )

    return {
        "data": [r.to_dict() for r in results],
        "query": q,
        "total": len(results),
    }
