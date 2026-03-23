"""MCP tool: get_decisions — list decisions in a project."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.mcp.registry import ToolDefinition
from src.repositories.decisions import DecisionsRepository


class GetDecisionsParams(BaseModel):
    """Input parameters for the get_decisions tool."""

    project_id: UUID = Field(description="Project to list decisions for.")
    tag: str | None = Field(
        default=None,
        description="Filter by tag (e.g. 'database', 'auth').",
    )
    source: str | None = Field(
        default=None,
        description="Filter by source (manual, agent, github).",
    )


async def handle_get_decisions(
    params: GetDecisionsParams,
    repo: DecisionsRepository,
) -> list[dict[str, Any]]:
    """List decisions in a project, optionally filtered by tag and source."""
    rows, _total = await repo.list_by_project(
        project_id=params.project_id,
        tag=params.tag,
        source=params.source,
    )
    return rows


TOOL = ToolDefinition(
    name="get_decisions",
    description=(
        "List architectural decisions (ADRs) in a project. "
        "Supports filtering by tag and source."
    ),
    params_model=GetDecisionsParams,
    handler=handle_get_decisions,
)
