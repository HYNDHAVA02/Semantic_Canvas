"""Batch upsert mapped entities and relationships into PostgreSQL."""

from __future__ import annotations

import json
import logging
from uuid import UUID

import asyncpg

from src.config import settings
from src.mapper import MappedEntity, MappedRelationship

logger = logging.getLogger(__name__)


async def upsert_to_postgres(
    project_id: str,
    entities: list[MappedEntity],
    relationships: list[MappedRelationship],
) -> None:
    """Upsert all entities and relationships into PostgreSQL."""
    conn = await asyncpg.connect(settings.database_url)
    pid = UUID(project_id)

    try:
        # Build axon_id → entity UUID mapping
        axon_id_to_entity_id: dict[str, UUID] = {}

        # Upsert entities
        for entity in entities:
            row = await conn.fetchrow(
                """
                INSERT INTO entities (project_id, name, kind, source, source_ref, metadata, last_seen_at, updated_at)
                VALUES ($1, $2, $3, 'axon', $4, $5::jsonb, now(), now())
                ON CONFLICT (project_id, name, kind)
                DO UPDATE SET
                    source_ref = COALESCE(EXCLUDED.source_ref, entities.source_ref),
                    metadata = entities.metadata || EXCLUDED.metadata,
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
