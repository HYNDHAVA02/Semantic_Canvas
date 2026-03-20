"""MCP tool: add_entity — create or upsert an entity."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.mcp.registry import ToolDefinition
from src.repositories.entities import EntitiesRepository

if TYPE_CHECKING:
    from src.embeddings.service import EmbeddingService


class AddEntityParams(BaseModel):
    """Input parameters for the add_entity tool."""

    project_id: UUID = Field(description="Project to add the entity to.")
    name: str = Field(
        description="Fully qualified entity name (e.g. 'PaymentService', 'src.auth.verify_token').",
        min_length=1,
    )
    kind: str = Field(
        description="Entity kind: service, function, class, module, table, endpoint, etc.",
        min_length=1,
    )
    source: str = Field(
        default="agent",
        description="Origin of the entity (agent, manual, axon, github).",
    )
    source_ref: str | None = Field(
        default=None,
        description="Reference to the source (e.g. file path, PR URL).",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary metadata (e.g. tech_stack, file, line).",
    )


async def handle_add_entity(
    params: AddEntityParams,
    repo: EntitiesRepository,
    embedding_service: EmbeddingService,
) -> dict[str, Any]:
    """Create or upsert an entity with embedding for search."""
    embedding = embedding_service.embed_one(f"{params.name} {params.kind}")
    return await repo.create(
        project_id=params.project_id,
        name=params.name,
        kind=params.kind,
        source=params.source,
        source_ref=params.source_ref,
        metadata=params.metadata,
        embedding=embedding,
    )


TOOL = ToolDefinition(
    name="add_entity",
    description=(
        "Create or update an entity (service, function, class, module, table, etc.). "
        "Upserts on (project_id, name, kind) — merges metadata if the entity exists. "
        "Generates an embedding for semantic search."
    ),
    params_model=AddEntityParams,
    handler=handle_add_entity,
)
