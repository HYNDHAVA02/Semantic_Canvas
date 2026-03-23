"""Projects controller — CRUD endpoints for projects."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.repositories.projects import ProjectsRepository
from src.rest.dto.common import PaginatedResponse

router = APIRouter()


class CreateProjectBody(BaseModel):
    """Request body for creating a project."""

    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9-]*$")
    description: str | None = None
    repo_url: str | None = None
    default_branch: str = "main"


class UpdateProjectBody(BaseModel):
    """Request body for partial project update."""

    name: str | None = None
    slug: str | None = None
    description: str | None = None
    repo_url: str | None = None
    default_branch: str | None = None


@router.get("/")
async def list_projects(
    request: Request,
    limit: int = 50,
    offset: int = 0,
) -> PaginatedResponse:
    """List all projects with pagination."""
    repo = ProjectsRepository(request.app.state.db_pool)
    rows, total = await repo.list_all(limit=limit, offset=offset)
    return PaginatedResponse(data=rows, total=total, limit=limit, offset=offset)


@router.post("/", status_code=201)
async def create_project(
    request: Request,
    body: CreateProjectBody,
) -> dict[str, Any]:
    """Create a new project."""
    repo = ProjectsRepository(request.app.state.db_pool)
    return await repo.create(
        name=body.name,
        slug=body.slug,
        description=body.description,
        repo_url=body.repo_url,
        default_branch=body.default_branch,
    )


@router.get("/{project_id}")
async def get_project(
    request: Request,
    project_id: UUID,
) -> dict[str, Any]:
    """Get a single project by ID."""
    repo = ProjectsRepository(request.app.state.db_pool)
    project = await repo.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}")
async def update_project(
    request: Request,
    project_id: UUID,
    body: UpdateProjectBody,
) -> dict[str, Any]:
    """Partial update of a project."""
    repo = ProjectsRepository(request.app.state.db_pool)
    updates = body.model_dump(exclude_unset=True)
    result = await repo.update(project_id, **updates)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return result
