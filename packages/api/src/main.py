"""Semantic Canvas API — FastAPI application factory."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import asyncpg
import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.tasks.queue import create_task_queue, LocalTaskQueue


async def _noop_axon_ingest(payload: dict) -> None:  # type: ignore[type-arg]
    """Stub handler for axon_ingest tasks in local dev."""
    import logging
    logging.getLogger(__name__).info("axon_ingest stub called: %s", payload)


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

    # Task queue
    task_queue = create_task_queue(
        backend=settings.task_queue_backend,
        gcp_project_id=settings.gcp_project_id,
        cloud_tasks_location=settings.cloud_tasks_location,
        cloud_tasks_queue=settings.cloud_tasks_queue,
        ingestion_service_url=settings.ingestion_service_url,
    )
    if isinstance(task_queue, LocalTaskQueue):
        task_queue.register("axon_ingest", _noop_axon_ingest)
    app.state.task_queue = task_queue

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
