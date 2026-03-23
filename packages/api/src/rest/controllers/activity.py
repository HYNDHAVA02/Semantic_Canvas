"""Activity controller — list recent activity log entries."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request

from src.repositories.activity import ActivityRepository
from src.rest.dto.common import PaginatedResponse

router = APIRouter()


@router.get("/")
async def list_activity(
    request: Request,
    project_id: UUID,
    source: str | None = None,
    actor: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> PaginatedResponse:
    """List activity log entries with optional filters and pagination."""
    repo = ActivityRepository(request.app.state.db_pool)
    rows, total = await repo.list_recent(
        project_id=project_id,
        limit=limit,
        offset=offset,
        source=source,
        actor=actor,
    )
    return PaginatedResponse(data=rows, total=total, limit=limit, offset=offset)
