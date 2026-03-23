"""MCP tool: get_recent_activity — list recent activity in a project."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.mcp.registry import ToolDefinition
from src.repositories.activity import ActivityRepository


class GetRecentActivityParams(BaseModel):
    """Input parameters for the get_recent_activity tool."""

    project_id: UUID = Field(description="Project to list activity for.")
    limit: int = Field(
        default=50,
        description="Maximum number of activity entries to return.",
    )
    source: str | None = Field(
        default=None,
        description="Filter by source (github, axon, manual, agent).",
    )
    actor: str | None = Field(
        default=None,
        description="Filter by actor (user or agent name).",
    )


async def handle_get_recent_activity(
    params: GetRecentActivityParams,
    repo: ActivityRepository,
) -> list[dict[str, Any]]:
    """List recent activity in a project, optionally filtered by source and actor."""
    rows, _total = await repo.list_recent(
        project_id=params.project_id,
        limit=params.limit,
        source=params.source,
        actor=params.actor,
    )
    return rows


TOOL = ToolDefinition(
    name="get_recent_activity",
    description=(
        "List recent activity log entries in a project. "
        "Supports filtering by source and actor, with configurable limit."
    ),
    params_model=GetRecentActivityParams,
    handler=handle_get_recent_activity,
)
