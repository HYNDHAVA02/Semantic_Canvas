"""MCP tool: get_entity — retrieve a single entity by name or ID."""

from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from src.mcp.registry import ToolDefinition
from src.repositories.entities import EntitiesRepository


class GetEntityParams(BaseModel):
    """Input parameters for the get_entity tool."""

    entity_id: UUID | None = Field(
        default=None,
        description="Look up entity by its UUID.",
    )
    project_id: UUID | None = Field(
        default=None,
        description="Project the entity belongs to. Required when looking up by name.",
    )
    name: str | None = Field(
        default=None,
        description="Entity name to look up within the project.",
    )

    @model_validator(mode="after")
    def check_lookup_key(self) -> Self:
        """Ensure either entity_id or (project_id + name) is provided."""
        if self.entity_id is None and (self.project_id is None or self.name is None):
            msg = "Provide either entity_id, or both project_id and name."
            raise ValueError(msg)
        return self


async def handle_get_entity(
    params: GetEntityParams,
    repo: EntitiesRepository,
) -> dict[str, Any] | None:
    """Retrieve a single entity by ID or by project + name."""
    if params.entity_id is not None:
        return await repo.get_by_id(params.entity_id)
    # Validator guarantees project_id and name are set here
    assert params.project_id is not None
    assert params.name is not None
    return await repo.get_by_name(params.project_id, params.name)


TOOL = ToolDefinition(
    name="get_entity",
    description=(
        "Get a single entity by its UUID or by project + name. "
        "Returns full entity details including metadata."
    ),
    params_model=GetEntityParams,
    handler=handle_get_entity,
)
