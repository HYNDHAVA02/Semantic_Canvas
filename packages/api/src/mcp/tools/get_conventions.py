"""MCP tool: get_conventions — list conventions in a project."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.mcp.registry import ToolDefinition
from src.repositories.conventions import ConventionsRepository


class GetConventionsParams(BaseModel):
    """Input parameters for the get_conventions tool."""

    project_id: UUID = Field(description="Project to list conventions for.")
    scope: str | None = Field(
        default=None,
        description="Filter by scope (global, backend, frontend, database, or a service name).",
    )
    active_only: bool = Field(
        default=True,
        description="Only return active conventions.",
    )


async def handle_get_conventions(
    params: GetConventionsParams,
    repo: ConventionsRepository,
) -> list[dict[str, Any]]:
    """List conventions in a project, optionally filtered by scope."""
    return await repo.list_by_project(
        project_id=params.project_id,
        scope=params.scope,
        active_only=params.active_only,
    )


TOOL = ToolDefinition(
    name="get_conventions",
    description=(
        "List coding conventions and team rules in a project. "
        "Supports filtering by scope and active status."
    ),
    params_model=GetConventionsParams,
    handler=handle_get_conventions,
)
