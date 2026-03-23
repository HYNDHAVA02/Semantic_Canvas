"""Decisions controller — list and create endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from src.repositories.decisions import DecisionsRepository
from src.rest.dto.common import PaginatedResponse

router = APIRouter()


class CreateDecisionBody(BaseModel):
    """Request body for creating a decision."""

    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    decided_by: str | None = None
    source: str = "manual"
    source_ref: str | None = None
    tags: list[str] | None = None


@router.get("/")
async def list_decisions(
    request: Request,
    project_id: UUID,
    tag: str | None = None,
    source: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> PaginatedResponse:
    """List decisions in a project with optional filters."""
    repo = DecisionsRepository(request.app.state.db_pool)
    rows, total = await repo.list_by_project(
        project_id=project_id,
        tag=tag,
        source=source,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse(data=rows, total=total, limit=limit, offset=offset)


@router.post("/", status_code=201)
async def create_decision(
    request: Request,
    project_id: UUID,
    body: CreateDecisionBody,
) -> dict[str, Any]:
    """Create a new decision."""
    repo = DecisionsRepository(request.app.state.db_pool)
    embedding = request.app.state.embeddings.embed_one(f"{body.title} {body.body}")
    return await repo.create(
        project_id=project_id,
        title=body.title,
        body=body.body,
        decided_by=body.decided_by,
        source=body.source,
        source_ref=body.source_ref,
        tags=body.tags,
        embedding=embedding,
    )
