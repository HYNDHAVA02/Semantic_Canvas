"""Batch upsert mapped entities and relationships into PostgreSQL."""

from __future__ import annotations

import json
import logging
from uuid import UUID

import asyncpg
from fastembed import TextEmbedding

from src.config import settings
from src.mapper import MappedEntity, MappedRelationship

logger = logging.getLogger(__name__)

# Lazy-loaded singleton so the model is only downloaded/loaded once per process.
_embedding_model: TextEmbedding | None = None


def _get_embedding_model() -> TextEmbedding:
    """Return the shared TextEmbedding model, loading it on first call."""
    global _embedding_model  # noqa: PLW0603
    if _embedding_model is None:
        logger.info("Loading embedding model: %s", settings.embedding_model)
        _embedding_model = TextEmbedding(settings.embedding_model)
        logger.info("Embedding model loaded")
    return _embedding_model


def _build_embedding_text(entity: MappedEntity) -> str:
    """Build the text string used to generate an entity's embedding."""
    file_path = entity.metadata.get("file", "")
    return f"{entity.name} {entity.kind} {file_path}"


def _generate_embeddings(entities: list[MappedEntity]) -> list[list[float]]:
    """Generate embeddings for a batch of entities."""
    model = _get_embedding_model()
    texts = [_build_embedding_text(e) for e in entities]
    results = list(model.embed(texts))
    return [r.tolist() for r in results]


async def upsert_to_postgres(
    project_id: str,
    entities: list[MappedEntity],
    relationships: list[MappedRelationship],
) -> None:
    """Upsert all entities and relationships into PostgreSQL."""
    conn = await asyncpg.connect(settings.database_url)
    pid = UUID(project_id)

    try:
        # Generate embeddings for all entities in one batch
        logger.info("Generating embeddings for %d entities...", len(entities))
        embeddings = _generate_embeddings(entities)
        logger.info("Embeddings generated")

        # Build axon_id → entity UUID mapping
        axon_id_to_entity_id: dict[str, UUID] = {}

        # Upsert entities with embeddings
        for entity, embedding in zip(entities, embeddings):
            # pgvector expects a string like '[0.1, 0.2, ...]'
            embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
            row = await conn.fetchrow(
                """
                INSERT INTO entities (project_id, name, kind, source, source_ref, metadata, embedding, last_seen_at, updated_at)
                VALUES ($1, $2, $3, 'axon', $4, $5::jsonb, $6::vector, now(), now())
                ON CONFLICT (project_id, name, kind)
                DO UPDATE SET
                    source_ref = COALESCE(EXCLUDED.source_ref, entities.source_ref),
                    metadata = entities.metadata || EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding,
                    last_seen_at = now(),
                    updated_at = now(),
                    is_active = true
                RETURNING id
                """,
                pid,
                entity.name,
                entity.kind,
                entity.source_ref,
                json.dumps(entity.metadata),
                embedding_str,
            )
            axon_id_to_entity_id[entity.axon_id] = row["id"]

        logger.info("Upserted %d entities", len(axon_id_to_entity_id))

        # Upsert relationships
        rel_count = 0
        for rel in relationships:
            from_id = axon_id_to_entity_id.get(rel.from_axon_id)
            to_id = axon_id_to_entity_id.get(rel.to_axon_id)
            if not from_id or not to_id:
                continue

            await conn.execute(
                """
                INSERT INTO relationships (project_id, from_entity_id, to_entity_id, kind, source, metadata, updated_at)
                VALUES ($1, $2, $3, $4, 'axon', $5::jsonb, now())
                ON CONFLICT (project_id, from_entity_id, to_entity_id, kind)
                DO UPDATE SET
                    metadata = relationships.metadata || EXCLUDED.metadata,
                    updated_at = now()
                """,
                pid,
                from_id,
                to_id,
                rel.kind,
                json.dumps(rel.metadata),
            )
            rel_count += 1

        logger.info("Upserted %d relationships", rel_count)

        # Mark stale axon entities
        await conn.execute(
            """
            UPDATE entities SET is_active = false, updated_at = now()
            WHERE project_id = $1 AND source = 'axon'
              AND last_seen_at < now() - interval '1 hour'
            """,
            pid,
        )

        # Delete stale axon relationships
        await conn.execute(
            """
            DELETE FROM relationships
            WHERE project_id = $1 AND source = 'axon'
              AND updated_at < now() - interval '1 hour'
            """,
            pid,
        )

        # Log ingestion activity
        await conn.execute(
            """
            INSERT INTO activity_log (project_id, summary, detail, source, actor, occurred_at)
            VALUES ($1, $2, $3, 'axon', 'axon-ci', now())
            """,
            pid,
            f"Axon indexed {len(entities)} symbols, {rel_count} relationships",
            f"Entities: {len(entities)}, Relationships: {rel_count}, "
            f"Dead code: {sum(1 for e in entities if e.metadata.get('is_dead_code'))}",
        )

    finally:
        await conn.close()
