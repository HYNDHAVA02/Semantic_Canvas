"""MCP server — exposes project knowledge to AI agents.

Provides both:
- SSE transport (remote agents over HTTP) via /mcp/sse endpoint
- stdio transport (local agents) via separate CLI entry point

This module sets up the FastAPI router for the SSE transport.
The stdio transport is handled by a separate script.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def mcp_health() -> dict[str, str]:
    """MCP server health check."""
    return {"status": "ok", "transport": "sse"}


# MCP SSE endpoint will be implemented here using the mcp Python SDK.
# The tool registry in registry.py maps tool names to handlers.
# See .claude/skills/mcp-protocol/SKILL.md for implementation patterns.
