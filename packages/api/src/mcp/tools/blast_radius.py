"""MCP tool: blast_radius — compute forward/reverse impact of an entity."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from src.mcp.registry import ToolDefinition
from src.services.blast_radius import BlastRadiusService


class BlastRadiusParams(BaseModel):
    """Input parameters for the blast_radius tool."""

    project_id: UUID = Field(description="Project containing the entity.")
    entity_id: UUID = Field(description="Entity to compute blast radius for.")
    direction: Literal["forward", "reverse", "both"] = Field(
        default="forward",
        description=(
            "'forward' = what this entity affects, "
            "'reverse' = what affects this entity, "
            "'both' = both directions."
        ),
    )
    max_depth: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum traversal depth (1-10).",
    )


async def handle_blast_radius(
    params: BlastRadiusParams,
    service: BlastRadiusService,
) -> dict[str, list[dict[str, Any]]]:
    """Compute blast radius for an entity."""
    result: dict[str, list[dict[str, Any]]] = {}

    if params.direction in ("forward", "both"):
        result["forward"] = await service.forward_impact(
            project_id=params.project_id,
            entity_id=params.entity_id,
            max_depth=params.max_depth,
        )

    if params.direction in ("reverse", "both"):
        result["reverse"] = await service.reverse_impact(
            project_id=params.project_id,
            entity_id=params.entity_id,
            max_depth=params.max_depth,
        )

    return result


TOOL = ToolDefinition(
    name="blast_radius",
    description=(
        "Compute the blast radius of an entity — what it affects (forward) "
        "or what affects it (reverse). Uses recursive graph traversal over "
        "relationships. Useful for impact analysis before making changes."
    ),
    params_model=BlastRadiusParams,
    handler=handle_blast_radius,
)
