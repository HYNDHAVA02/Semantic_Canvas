"""MCP tool: log_activity — record an activity log entry."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.mcp.registry import ToolDefinition
from src.repositories.activity import ActivityRepository

if TYPE_CHECKING:
    from src.embeddings.service import EmbeddingService


class LogActivityParams(BaseModel):
    """Input parameters for the log_activity tool."""

    project_id: UUID = Field(description="Project to log the activity for.")
    summary: str = Field(
        description="Short summary of what happened.",
        min_length=1,
    )
    source: str = Field(
        description="Origin of the activity (github, axon, manual, agent).",
    )
    detail: str | None = Field(
        default=None,
        description="Extended detail about the activity.",
    )
    actor: str | None = Field(
        default=None,
        description="Who or what performed the activity (user or agent name).",
    )
    source_ref: str | None = Field(
        default=None,
        description="Reference to the source (e.g. commit SHA, PR URL).",
    )


async def handle_log_activity(
    params: LogActivityParams,
    repo: ActivityRepository,
    embedding_service: EmbeddingService,
) -> dict[str, Any]:
    """Record an activity log entry with embedding for search."""
    embed_text = f"{params.summary} {params.detail or ''}".strip()
    embedding = embedding_service.embed_one(embed_text)
    return await repo.create(
        project_id=params.project_id,
        summary=params.summary,
        source=params.source,
        detail=params.detail,
        actor=params.actor,
        source_ref=params.source_ref,
        embedding=embedding,
    )


TOOL = ToolDefinition(
    name="log_activity",
    description=(
        "Record an activity log entry — what changed, when, and why. "
        "Captures summary, source, actor, and optional detail. "
        "Generates an embedding for semantic search."
    ),
    params_model=LogActivityParams,
    handler=handle_log_activity,
)
