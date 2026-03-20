"""Embedding service using fastembed.

Wraps the fastembed TextEmbedding model for generating vector(384)
embeddings compatible with Axon's bge-small-en-v1.5 output.
"""

from __future__ import annotations

import logging
from typing import Sequence

from fastembed import TextEmbedding

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate text embeddings using a local model.

    Uses bge-small-en-v1.5 by default (384 dimensions).
    Matches Axon's embedding model so vectors are comparable
    across code entities and human-authored content.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        logger.info("Loading embedding model: %s", model_name)
        self._model = TextEmbedding(model_name)
        self._dimension = 384
        logger.info("Embedding model loaded (%d dimensions)", self._dimension)

    @property
    def dimension(self) -> int:
        """Vector dimension (384 for bge-small-en-v1.5)."""
        return self._dimension

    def embed_one(self, text: str) -> list[float]:
        """Generate embedding for a single text string."""
        results = list(self._model.embed([text]))
        return results[0].tolist()  # type: ignore[no-any-return]  # numpy .tolist() untyped

    def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate embeddings for multiple text strings."""
        if not texts:
            return []
        results = list(self._model.embed(list(texts)))
        return [r.tolist() for r in results]
