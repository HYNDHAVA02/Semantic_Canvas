"""Analysis controller — dead code detection and blast radius."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Request

from src.repositories.entities import EntitiesRepository
from src.services.blast_radius import BlastRadiusService

router = APIRouter()


@router.get("/dead-code")
async def list_dead_code(
    request: Request,
    project_id: UUID,
    kind: str | None = None,
) -> dict[str, Any]:
    """List entities flagged as dead code."""
    repo = EntitiesRepository(request.app.state.db_pool)
    rows = await repo.get_dead_code(project_id=project_id, kind=kind)
    return {"data": rows, "total": len(rows)}


@router.get("/blast-radius/{entity_id}")
async def blast_radius(
    request: Request,
    project_id: UUID,
    entity_id: UUID,
    direction: str = "forward",
    depth: int = 3,
) -> dict[str, Any]:
    """Compute blast radius for an entity."""
    service = BlastRadiusService(request.app.state.db_pool)

    if direction == "both":
        forward = await service.forward_impact(project_id, entity_id, depth)
        reverse = await service.reverse_impact(project_id, entity_id, depth)
        return {"forward": forward, "reverse": reverse}

    if direction == "reverse":
        affected = await service.reverse_impact(project_id, entity_id, depth)
    else:
        affected = await service.forward_impact(project_id, entity_id, depth)

    return {"data": affected, "direction": direction, "depth": depth}
