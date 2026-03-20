"""MCP tool: log_convention — record a coding convention or team rule."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.mcp.registry import ToolDefinition
from src.repositories.conventions import ConventionsRepository

if TYPE_CHECKING:
    from src.embeddings.service import EmbeddingService


class LogConventionParams(BaseModel):
    """Input parameters for the log_convention tool."""

    project_id: UUID = Field(description="Project to log the convention for.")
    title: str = Field(
        description="Short title for the convention.",
        min_length=1,
    )
    body: str = Field(
        description="Full description of the convention and when it applies.",
        min_length=1,
    )
    scope: str | None = Field(
        default=None,
        description="Scope: global, backend, frontend, database, or a service name.",
    )
    tags: list[str] | None = Field(
        default=None,
        description="Tags for categorisation (e.g. 'naming', 'testing', 'imports').",
    )
    source: str = Field(
        default="agent",
        description="Origin of the convention (agent, manual, github).",
    )
    source_ref: str | None = Field(
        default=None,
        description="Reference to the source (e.g. PR URL, style guide URL).",
    )


async def handle_log_convention(
    params: LogConventionParams,
    repo: ConventionsRepository,
    embedding_service: EmbeddingService,
) -> dict[str, Any]:
    """Record a coding convention with embedding for search."""
    embedding = embedding_service.embed_one(f"{params.title} {params.body}")
    return await repo.create(
        project_id=params.project_id,
        title=params.title,
        body=params.body,
        scope=params.scope,
        source=params.source,
        source_ref=params.source_ref,
        tags=params.tags,
        embedding=embedding,
    )


TOOL = ToolDefinition(
    name="log_convention",
    description=(
        "Record a coding convention or team rule. Captures the title, description, "
        "scope, and optional tags. Generates an embedding for semantic search."
    ),
    params_model=LogConventionParams,
    handler=handle_log_convention,
)
