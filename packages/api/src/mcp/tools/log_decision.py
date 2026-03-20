"""MCP tool: log_decision — record an architectural decision."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.mcp.registry import ToolDefinition
from src.repositories.decisions import DecisionsRepository

if TYPE_CHECKING:
    from src.embeddings.service import EmbeddingService


class LogDecisionParams(BaseModel):
    """Input parameters for the log_decision tool."""

    project_id: UUID = Field(description="Project to log the decision for.")
    title: str = Field(
        description="Short title summarising the decision.",
        min_length=1,
    )
    body: str = Field(
        description="Full explanation: context, options considered, rationale.",
        min_length=1,
    )
    decided_by: str | None = Field(
        default=None,
        description="Who made the decision (person, team, or agent name).",
    )
    tags: list[str] | None = Field(
        default=None,
        description="Tags for categorisation (e.g. 'database', 'auth', 'frontend').",
    )
    source: str = Field(
        default="agent",
        description="Origin of the decision (agent, manual, github).",
    )
    source_ref: str | None = Field(
        default=None,
        description="Reference to the source (e.g. PR URL, issue URL).",
    )


async def handle_log_decision(
    params: LogDecisionParams,
    repo: DecisionsRepository,
    embedding_service: EmbeddingService,
) -> dict[str, Any]:
    """Record an architectural decision with embedding for search."""
    embedding = embedding_service.embed_one(f"{params.title} {params.body}")
    return await repo.create(
        project_id=params.project_id,
        title=params.title,
        body=params.body,
        decided_by=params.decided_by,
        source=params.source,
        source_ref=params.source_ref,
        tags=params.tags,
        embedding=embedding,
    )


TOOL = ToolDefinition(
    name="log_decision",
    description=(
        "Record an architectural decision (ADR). Captures the title, rationale, "
        "who decided, and optional tags. Generates an embedding for semantic search."
    ),
    params_model=LogDecisionParams,
    handler=handle_log_decision,
)
