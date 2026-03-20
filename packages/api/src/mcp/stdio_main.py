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

import asyncpg

from mcp.server.stdio import stdio_server

from src.embeddings.service import EmbeddingService
from src.mcp.registry import register_all_tools
from src.mcp.server import create_mcp_server

logger = logging.getLogger(__name__)


async def main() -> None:
    """Run the MCP server over stdio."""
    logging.basicConfig(level=logging.INFO)

    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://canvas:canvas@localhost:5432/semantic_canvas",
    )
    embedding_model = os.environ.get(
        "EMBEDDING_MODEL",
        "BAAI/bge-small-en-v1.5",
    )

    # Create resources
    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5)
    assert pool is not None, "Failed to create database pool"

    embedding_service = EmbeddingService(model_name=embedding_model)

    # Register tools and create server
    register_all_tools()
    server = create_mcp_server(pool, embedding_service)

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
