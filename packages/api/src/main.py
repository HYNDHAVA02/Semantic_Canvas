"""Semantic Canvas API — FastAPI application factory."""

import asyncio
import json
import logging
import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg
import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.tasks.queue import LocalTaskQueue, create_task_queue

logger = logging.getLogger(__name__)

# Path to ingestion package (sibling of packages/api/)
_INGESTION_PKG_DIR = Path(__file__).resolve().parents[2] / "ingestion"


async def _local_axon_ingest(payload: dict[str, object]) -> None:
    """Run the ingestion pipeline as a subprocess.

    Spawns ``python -m src.main <json_payload>`` inside packages/ingestion/,
    forwarding DATABASE_URL and EMBEDDING_MODEL from the API environment.
    This mirrors production where ingestion runs as a separate Cloud Run service.
    """
    payload_json = json.dumps(payload)
    # Use the same Python interpreter running the API so that the ingestion
    # subprocess inherits the venv. Prepend its directory to PATH so that
    # sibling CLI tools (axon) installed in the same venv are also found.
    python_exe = sys.executable
    venv_bin_dir = str(Path(python_exe).parent)
    env = {
        **os.environ,
        "PATH": venv_bin_dir + os.pathsep + os.environ.get("PATH", ""),
        "DATABASE_URL": settings.database_url,
        "EMBEDDING_MODEL": settings.embedding_model,
    }

    logger.info("Spawning ingestion subprocess for payload: %s", payload_json)
    
    def _run_subprocess():
        import subprocess
        return subprocess.run(
            [python_exe, "-m", "src.main", payload_json],
            cwd=str(_INGESTION_PKG_DIR),
            env=env,
            capture_output=True,
            text=True,
        )

    result = await asyncio.to_thread(_run_subprocess)

    if result.stdout:
        logger.info("Ingestion stdout:\n%s", result.stdout)
    if result.stderr:
        logger.warning("Ingestion stderr:\n%s", result.stderr)
    if result.returncode != 0:
        raise RuntimeError(
            f"Ingestion subprocess exited with code {result.returncode}: "
            f"{result.stderr}"
        )


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
        task_queue.register("axon_ingest", _local_axon_ingest)
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

    # Optional auth — validates tokens if present, allows anonymous otherwise
    from src.auth.middleware import OptionalAuthMiddleware
    app.add_middleware(OptionalAuthMiddleware)

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
