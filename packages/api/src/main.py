"""Semantic Canvas API — FastAPI application factory."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import asyncpg
import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: DB pool, Redis, embedding model."""
    # Startup
    app.state.db_pool = await asyncpg.create_pool(
        settings.database_url,
        min_size=2,
        max_size=10,
    )
    app.state.redis = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    # Pre-warm embedding model (avoids cold-start latency on first request)
    from src.embeddings.service import EmbeddingService
    app.state.embeddings = EmbeddingService(model_name=settings.embedding_model)

    # Initialize MCP server with SSE transport
    from src.mcp.server import init_sse_transport
    init_sse_transport(app.state.db_pool, app.state.embeddings)

    yield

    # Shutdown
    await app.state.db_pool.close()
    await app.state.redis.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Semantic Canvas",
        description="Project memory layer for AI coding agents",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register REST routes
    from src.rest.router import router as rest_router
    app.include_router(rest_router, prefix="/api/v1")

    # Register MCP tools and mount SSE transport
    from src.mcp.registry import register_all_tools
    register_all_tools()

    from src.mcp.server import mcp_mount
    app.routes.append(mcp_mount)

    # Health check
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
