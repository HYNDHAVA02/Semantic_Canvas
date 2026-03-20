"""MCP tool: get_relationships — query relationships between entities."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from src.mcp.registry import ToolDefinition
from src.repositories.relationships import RelationshipsRepository


class GetRelationshipsParams(BaseModel):
    """Input parameters for the get_relationships tool."""

    project_id: UUID = Field(description="Project to query relationships in.")
    entity_id: UUID | None = Field(
        default=None,
        description="Filter to relationships involving this entity.",
    )
    kind: str | None = Field(
        default=None,
        description="Filter by relationship kind (calls, depends_on, imports, etc.).",
    )
    direction: Literal["from", "to"] | None = Field(
        default=None,
        description="Direction filter: 'from' (outgoing), 'to' (incoming). Only used with entity_id.",
    )


async def handle_get_relationships(
    params: GetRelationshipsParams,
    repo: RelationshipsRepository,
) -> list[dict[str, Any]]:
    """Query relationships, optionally filtered by entity, kind, and direction."""
    if params.entity_id is not None:
        return await repo.list_for_entity(
            entity_id=params.entity_id,
            kind=params.kind,
            direction=params.direction,
        )
    return await repo.list_by_project(
        project_id=params.project_id,
        kind=params.kind,
    )


TOOL = ToolDefinition(
    name="get_relationships",
    description=(
        "Query relationships between entities in a project. "
        "Returns connections like calls, depends_on, imports, inherits, etc. "
        "Filter by entity, kind, and direction (from/to)."
    ),
    params_model=GetRelationshipsParams,
    handler=handle_get_relationships,
)
