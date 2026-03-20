"""MCP tool: get_dead_code — list dead code entities in a project."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.mcp.registry import ToolDefinition
from src.repositories.entities import EntitiesRepository


class GetDeadCodeParams(BaseModel):
    """Input parameters for the get_dead_code tool."""

    project_id: UUID = Field(description="Project to list dead code for.")
    kind: str | None = Field(
        default=None,
        description="Filter by entity kind (function, class, module, etc.).",
    )


async def handle_get_dead_code(
    params: GetDeadCodeParams,
    repo: EntitiesRepository,
) -> list[dict[str, Any]]:
    """List entities flagged as dead code by Axon."""
    return await repo.get_dead_code(
        project_id=params.project_id,
        kind=params.kind,
    )


TOOL = ToolDefinition(
    name="get_dead_code",
    description=(
        "List entities flagged as dead (unreachable) code by static analysis. "
        "Supports filtering by entity kind."
    ),
    params_model=GetDeadCodeParams,
    handler=handle_get_dead_code,
)
