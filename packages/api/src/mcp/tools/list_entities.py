"""MCP tool: list_entities — list entities in a project."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.mcp.registry import ToolDefinition
from src.repositories.entities import EntitiesRepository


class ListEntitiesParams(BaseModel):
    """Input parameters for the list_entities tool."""

    project_id: UUID = Field(description="Project to list entities for.")
    kind: str | None = Field(
        default=None,
        description="Filter by entity kind (service, function, class, module, etc.).",
    )
    source: str | None = Field(
        default=None,
        description="Filter by source (axon, github, manual, agent, upload).",
    )
    active_only: bool = Field(
        default=True,
        description="Only return active entities.",
    )


async def handle_list_entities(
    params: ListEntitiesParams,
    repo: EntitiesRepository,
) -> list[dict[str, Any]]:
    """List entities in a project, optionally filtered by kind and source."""
    rows, _total = await repo.list_by_project(
        project_id=params.project_id,
        kind=params.kind,
        source=params.source,
        active_only=params.active_only,
    )
    return rows


TOOL = ToolDefinition(
    name="list_entities",
    description=(
        "List all entities (services, functions, classes, modules, etc.) "
        "in a project. Supports filtering by kind, source, and active status."
    ),
    params_model=ListEntitiesParams,
    handler=handle_list_entities,
)
