"""MCP tool: add_relationship — create or upsert a relationship between entities."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.mcp.registry import ToolDefinition
from src.repositories.relationships import RelationshipsRepository


class AddRelationshipParams(BaseModel):
    """Input parameters for the add_relationship tool."""

    project_id: UUID = Field(description="Project the entities belong to.")
    from_entity_id: UUID = Field(
        description="ID of the source entity.",
    )
    to_entity_id: UUID = Field(
        description="ID of the target entity.",
    )
    kind: str = Field(
        description="Relationship kind: calls, imports, extends, implements, uses, owns, etc.",
        min_length=1,
    )
    source: str = Field(
        default="agent",
        description="Origin of the relationship (agent, manual, axon, github).",
    )
    source_ref: str | None = Field(
        default=None,
        description="Reference to the source (e.g. file path, PR URL).",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary metadata about the relationship.",
    )


async def handle_add_relationship(
    params: AddRelationshipParams,
    repo: RelationshipsRepository,
) -> dict[str, Any]:
    """Create or upsert a relationship between two entities."""
    return await repo.create(
        project_id=params.project_id,
        from_entity_id=params.from_entity_id,
        to_entity_id=params.to_entity_id,
        kind=params.kind,
        source=params.source,
        source_ref=params.source_ref,
        metadata=params.metadata,
    )


TOOL = ToolDefinition(
    name="add_relationship",
    description=(
        "Create or update a relationship between two entities. "
        "Upserts on (project_id, from_entity_id, to_entity_id, kind) — "
        "merges metadata if the relationship exists."
    ),
    params_model=AddRelationshipParams,
    handler=handle_add_relationship,
)
