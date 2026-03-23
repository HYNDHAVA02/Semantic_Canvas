"""Conventions controller — list, create, and update endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.repositories.conventions import ConventionsRepository
from src.rest.dto.common import PaginatedResponse

router = APIRouter()


class CreateConventionBody(BaseModel):
    """Request body for creating a convention."""

    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    scope: str | None = None
    source: str = "manual"
    source_ref: str | None = None
    tags: list[str] | None = None
    is_active: bool = True


class UpdateConventionBody(BaseModel):
    """Request body for partial convention update."""

    title: str | None = None
    body: str | None = None
    scope: str | None = None
    is_active: bool | None = None
    tags: list[str] | None = None


@router.get("/")
async def list_conventions(
    request: Request,
    project_id: UUID,
    scope: str | None = None,
    active_only: bool = True,
    limit: int = 50,
    offset: int = 0,
) -> PaginatedResponse:
    """List conventions in a project with optional filters."""
    repo = ConventionsRepository(request.app.state.db_pool)
    rows, total = await repo.list_by_project(
        project_id=project_id,
        scope=scope,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse(data=rows, total=total, limit=limit, offset=offset)


@router.post("/", status_code=201)
async def create_convention(
    request: Request,
    project_id: UUID,
    body: CreateConventionBody,
) -> dict[str, Any]:
    """Create a new convention."""
    repo = ConventionsRepository(request.app.state.db_pool)
    embedding = request.app.state.embeddings.embed_one(f"{body.title} {body.body}")
    return await repo.create(
        project_id=project_id,
        title=body.title,
        body=body.body,
        scope=body.scope,
        source=body.source,
        source_ref=body.source_ref,
        tags=body.tags,
        is_active=body.is_active,
        embedding=embedding,
    )


@router.patch("/{conv_id}")
async def update_convention(
    request: Request,
    project_id: UUID,
    conv_id: UUID,
    body: UpdateConventionBody,
) -> dict[str, Any]:
    """Partial update of a convention (e.g. toggle active)."""
    repo = ConventionsRepository(request.app.state.db_pool)
    updates = body.model_dump(exclude_unset=True)
    result = await repo.update(conv_id, **updates)
    if result is None:
        raise HTTPException(status_code=404, detail="Convention not found")
    return result
