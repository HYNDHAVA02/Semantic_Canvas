"""Entities controller — list and detail endpoints for entities."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from src.repositories.activity import ActivityRepository
from src.repositories.entities import EntitiesRepository
from src.repositories.relationships import RelationshipsRepository
from src.rest.dto.common import PaginatedResponse

router = APIRouter()


@router.get("/")
async def list_entities(
    request: Request,
    project_id: UUID,
    kind: str | None = None,
    source: str | None = None,
    active_only: bool = True,
    limit: int = 50,
    offset: int = 0,
) -> PaginatedResponse:
    """List entities in a project with optional filters and pagination."""
    repo = EntitiesRepository(request.app.state.db_pool)
    rows, total = await repo.list_by_project(
        project_id=project_id,
        kind=kind,
        source=source,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse(data=rows, total=total, limit=limit, offset=offset)


@router.get("/{entity_id}")
async def get_entity_detail(
    request: Request,
    project_id: UUID,
    entity_id: UUID,
) -> dict[str, Any]:
    """Get entity detail including relationships and recent activity."""
    pool = request.app.state.db_pool
    ent_repo = EntitiesRepository(pool)

    entity = await ent_repo.get_by_id(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")

    rel_repo = RelationshipsRepository(pool)
    relationships = await rel_repo.list_for_entity(entity_id=entity_id)

    act_repo = ActivityRepository(pool)
    # Activity log doesn't filter by entity_id directly, so we return
    # recent activity for the project (the dashboard can filter client-side).
    activity, _total = await act_repo.list_recent(
        project_id=project_id, limit=10,
    )

    return {
        **entity,
        "relationships": relationships,
        "recent_activity": activity,
    }
