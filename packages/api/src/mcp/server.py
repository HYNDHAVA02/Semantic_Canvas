"""MCP server — exposes project knowledge to AI agents.

Provides both:
- SSE transport (remote agents over HTTP) via /mcp/sse endpoint
- stdio transport (local agents) via separate CLI entry point

This module sets up the MCP Server, dependency injection,
and the Starlette routes for the SSE transport.
"""

from __future__ import annotations

import inspect
import json
import logging
from typing import TYPE_CHECKING, Any

import asyncpg
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route

from mcp.server.lowlevel.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool

from src.mcp.registry import ToolDefinition, registry
from src.repositories.activity import ActivityRepository
from src.repositories.conventions import ConventionsRepository
from src.repositories.decisions import DecisionsRepository
from src.repositories.entities import EntitiesRepository
from src.repositories.relationships import RelationshipsRepository
from src.repositories.search import SearchRepository
from src.services.blast_radius import BlastRadiusService

if TYPE_CHECKING:
    from src.embeddings.service import EmbeddingService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool conversion
# ---------------------------------------------------------------------------


def _tool_to_mcp(tool: ToolDefinition) -> Tool:
    """Convert a ToolDefinition to an MCP Tool."""
    return Tool(
        name=tool.name,
        description=tool.description,
        inputSchema=tool.params_model.model_json_schema(),
    )


# ---------------------------------------------------------------------------
# Dependency injection
# ---------------------------------------------------------------------------


def _build_dependency_map(
    db_pool: asyncpg.Pool,
    embedding_service: object,
) -> dict[str, object]:
    """Build a map from annotation name to instance for dependency injection.

    Uses string keys because handler annotations are strings at runtime
    (due to ``from __future__ import annotations``).
    """
    return {
        "EntitiesRepository": EntitiesRepository(db_pool),
        "RelationshipsRepository": RelationshipsRepository(db_pool),
        "DecisionsRepository": DecisionsRepository(db_pool),
        "ConventionsRepository": ConventionsRepository(db_pool),
        "ActivityRepository": ActivityRepository(db_pool),
        "SearchRepository": SearchRepository(db_pool),
        "BlastRadiusService": BlastRadiusService(db_pool),
        "EmbeddingService": embedding_service,
    }


async def _resolve_and_call(
    tool: ToolDefinition,
    arguments: dict[str, Any],
    dep_map: dict[str, object],
) -> object:
    """Validate arguments, resolve dependencies, and call a tool handler."""
    params = tool.params_model(**arguments)

    sig = inspect.signature(tool.handler)
    kwargs: dict[str, object] = {}

    for i, (name, param) in enumerate(sig.parameters.items()):
        if i == 0:
            # First parameter is always the validated params model
            kwargs[name] = params
        else:
            # Annotation is a string (from __future__ annotations)
            annotation = param.annotation
            if annotation in dep_map:
                kwargs[name] = dep_map[annotation]
            else:
                raise ValueError(
                    f"Unknown dependency type {annotation!r} for tool {tool.name}"
                )

    return await tool.handler(**kwargs)


# ---------------------------------------------------------------------------
# MCP Server factory
# ---------------------------------------------------------------------------


def create_mcp_server(
    db_pool: asyncpg.Pool,
    embedding_service: EmbeddingService,
) -> Server:
    """Create an MCP Server with tool listing and dispatch wired up."""
    server = Server("semantic-canvas")
    dep_map = _build_dependency_map(db_pool, embedding_service)

    @server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
    async def list_tools() -> list[Tool]:
        """Return all registered tools as MCP Tool objects."""
        return [_tool_to_mcp(t) for t in registry.all_tools()]

    @server.call_tool()  # type: ignore[untyped-decorator]
    async def call_tool(
        name: str, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Dispatch a tool call to its handler."""
        tool = registry.get(name)
        if tool is None:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

        try:
            result = await _resolve_and_call(tool, arguments, dep_map)
            return [TextContent(type="text", text=json.dumps(result, default=str))]
        except Exception as exc:
            logger.exception("Tool %s failed", name)
            return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]

    return server


# ---------------------------------------------------------------------------
# SSE transport — Starlette ASGI routes
# ---------------------------------------------------------------------------

# Module-level state, initialized by init_sse_transport() during app lifespan.
_sse_transport: SseServerTransport | None = None
_mcp_server: Server | None = None


def init_sse_transport(
    db_pool: asyncpg.Pool,
    embedding_service: EmbeddingService,
) -> None:
    """Initialize the MCP server and SSE transport.

    Called during FastAPI lifespan startup, after db_pool and
    embedding_service are available.
    """
    global _sse_transport, _mcp_server  # noqa: PLW0603
    _sse_transport = SseServerTransport("/mcp/messages")
    _mcp_server = create_mcp_server(db_pool, embedding_service)
    logger.info("MCP SSE transport initialized")


async def _handle_sse(scope: Any, receive: Any, send: Any) -> None:
    """ASGI handler for SSE connection (GET /sse)."""
    assert _sse_transport is not None, "MCP transport not initialized"
    assert _mcp_server is not None, "MCP server not initialized"
    async with _sse_transport.connect_sse(scope, receive, send) as (read_stream, write_stream):
        await _mcp_server.run(
            read_stream,
            write_stream,
            _mcp_server.create_initialization_options(),
        )


async def _handle_messages(scope: Any, receive: Any, send: Any) -> None:
    """ASGI handler for client messages (POST /messages)."""
    assert _sse_transport is not None, "MCP transport not initialized"
    await _sse_transport.handle_post_message(scope, receive, send)


async def _mcp_health(request: Request) -> Response:
    """MCP server health check."""
    return Response(
        content=json.dumps({"status": "ok", "transport": "sse"}),
        media_type="application/json",
    )


# Starlette Mount to be included in the FastAPI app.
# Routes are defined at module level; the ASGI handlers reference
# module globals that are set by init_sse_transport() before any
# HTTP requests are served (FastAPI lifespan runs first).
mcp_mount = Mount(
    "/mcp",
    routes=[
        Route("/sse", endpoint=_handle_sse),
        Route("/messages", endpoint=_handle_messages, methods=["POST"]),
        Route("/health", endpoint=_mcp_health),
    ],
)
