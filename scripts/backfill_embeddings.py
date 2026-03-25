"""Backfill embeddings for entities that have NULL embedding column.

Prerequisites:
  - Postgres running with semantic_canvas DB
  - fastembed installed (pip install fastembed)

Usage:
  python scripts/backfill_embeddings.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

import asyncpg
from fastembed import TextEmbedding

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://canvas:canvas@localhost:5432/semantic_canvas"
)
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
BATCH_SIZE = 256


def build_embedding_text(name: str, kind: str, metadata: dict[str, object]) -> str:
    """Build the text string used to generate an entity's embedding."""
    file_path = metadata.get("file", "")
    return f"{name} {kind} {file_path}"


async def backfill() -> None:
    """Read all entities with NULL embeddings, generate in batches, update."""
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Fetch all entities missing embeddings
        rows = await conn.fetch(
            """
            SELECT id, name, kind, metadata
            FROM entities
            WHERE embedding IS NULL
            ORDER BY created_at
            """
        )
        total = len(rows)
        if total == 0:
            logger.info("No entities with NULL embeddings found. Nothing to do.")
            return

        logger.info("Found %d entities with NULL embeddings", total)

        # Load embedding model
        logger.info("Loading embedding model: %s", EMBEDDING_MODEL)
        model = TextEmbedding(EMBEDDING_MODEL)
        logger.info("Model loaded")

        # Process in batches
        updated = 0
        for i in range(0, total, BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            texts = []
            for row in batch:
                import json
                meta = json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"]
                texts.append(build_embedding_text(row["name"], row["kind"], meta))

            # Generate embeddings
            embeddings = list(model.embed(texts))

            # Update each entity
            for row, embedding in zip(batch, embeddings):
                embedding_str = "[" + ",".join(str(v) for v in embedding.tolist()) + "]"
                await conn.execute(
                    "UPDATE entities SET embedding = $1::vector, updated_at = now() WHERE id = $2",
                    embedding_str,
                    row["id"],
                )
                updated += 1

            logger.info("Backfilled %d / %d entities", min(i + BATCH_SIZE, total), total)

        logger.info("Done. Updated %d entities with embeddings.", updated)

    finally:
        await conn.close()


def main() -> None:
    """Entry point."""
    asyncio.run(backfill())


if __name__ == "__main__":
    main()
