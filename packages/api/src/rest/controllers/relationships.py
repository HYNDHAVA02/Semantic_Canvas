"""Relationships controller — list and create endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from src.repositories.relationships import RelationshipsRepository
from src.rest.dto.common import PaginatedResponse

router = APIRouter()


class CreateRelationshipBody(BaseModel):
    """Request body for creating a relationship."""

    from_entity_id: UUID
    to_entity_id: UUID
    kind: str = Field(min_length=1)
    source: str = "manual"
    source_ref: str | None = None
    metadata: dict[str, Any] | None = None


@router.get("/")
async def list_relationships(
    request: Request,
    project_id: UUID,
    kind: str | None = None,
    source: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> PaginatedResponse:
    """List relationships in a project with optional filters."""
    repo = RelationshipsRepository(request.app.state.db_pool)
    rows, total = await repo.list_by_project(
        project_id=project_id,
        kind=kind,
        source=source,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse(data=rows, total=total, limit=limit, offset=offset)


@router.post("/", status_code=201)
async def create_relationship(
    request: Request,
    project_id: UUID,
    body: CreateRelationshipBody,
) -> dict[str, Any]:
    """Create or upsert a relationship."""
    repo = RelationshipsRepository(request.app.state.db_pool)
    return await repo.create(
        project_id=project_id,
        from_entity_id=body.from_entity_id,
        to_entity_id=body.to_entity_id,
        kind=body.kind,
        source=body.source,
        source_ref=body.source_ref,
        metadata=body.metadata,
    )
