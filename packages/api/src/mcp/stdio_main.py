"""Standalone MCP server entry point for stdio transport.

Used by local AI agents (e.g. Claude Code) that communicate
over stdin/stdout. Creates its own database pool and embedding
service — no FastAPI needed.

Usage:
    python -m src.mcp.stdio_main
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Sequence

import asyncpg

from mcp.server.stdio import stdio_server

from src.embeddings.service import EmbeddingService
from src.mcp.registry import register_all_tools
from src.mcp.server import create_mcp_server

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    """Send all logging to stderr so stdout stays clean for JSON-RPC."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s - %(name)s - %(message)s"))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    # Suppress noisy third-party loggers that pollute output
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

    # Suppress fastembed/onnxruntime download progress bars
    logging.getLogger("fastembed").setLevel(logging.WARNING)
    logging.getLogger("onnxruntime").setLevel(logging.WARNING)


# Configure logging before any imports that might log to stdout
_configure_logging()

# Redirect tqdm progress bars (used by huggingface_hub downloads) to stderr
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TQDM_DISABLE", "1")


class _LazyEmbeddingService:
    """Proxy that loads the real EmbeddingService on first use.

    Defers the heavy ONNX model load so the MCP server can accept
    the initialize handshake immediately.
    """

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._inner: EmbeddingService | None = None

    def _ensure_loaded(self) -> EmbeddingService:
        if self._inner is None:
            self._inner = EmbeddingService(model_name=self._model_name)
        return self._inner

    @property
    def dimension(self) -> int:
        return self._ensure_loaded().dimension

    def embed_one(self, text: str) -> list[float]:
        return self._ensure_loaded().embed_one(text)

    def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        return self._ensure_loaded().embed_many(texts)


class _LazyPool:
    """Proxy that creates the asyncpg connection pool on first use.

    Defers the database connection until a tool actually needs it,
    so the MCP stdio handshake completes instantly.
    """

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._pool: asyncpg.Pool | None = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self._database_url, min_size=1, max_size=5
            )
            assert self._pool is not None, "Failed to create database pool"
            logger.info("Database pool created")
        return self._pool

    @asynccontextmanager
    async def acquire(self, *args, **kwargs):  # noqa: ANN002, ANN003
        pool = await self._ensure_pool()
        async with pool.acquire(*args, **kwargs) as conn:
            yield conn

    async def fetchrow(self, *args, **kwargs):  # noqa: ANN002, ANN003
        pool = await self._ensure_pool()
        return await pool.fetchrow(*args, **kwargs)

    async def fetch(self, *args, **kwargs):  # noqa: ANN002, ANN003
        pool = await self._ensure_pool()
        return await pool.fetch(*args, **kwargs)

    async def execute(self, *args, **kwargs):  # noqa: ANN002, ANN003
        pool = await self._ensure_pool()
        return await pool.execute(*args, **kwargs)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()


async def main() -> None:
    """Run the MCP server over stdio."""

    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://canvas:canvas@localhost:5432/semantic_canvas",
    )
    embedding_model = os.environ.get(
        "EMBEDDING_MODEL",
        "BAAI/bge-small-en-v1.5",
    )

    # Use lazy proxies so the MCP server starts instantly —
    # no blocking DB/model initialization before the stdio handshake.
    pool = _LazyPool(database_url)
    embedding_service = _LazyEmbeddingService(embedding_model)

    # Register tools and create server
    register_all_tools()
    server = create_mcp_server(pool, embedding_service)  # type: ignore[arg-type]

    logger.info("Starting MCP stdio server")

    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
