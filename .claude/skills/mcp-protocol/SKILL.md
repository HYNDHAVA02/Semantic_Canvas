---
name: mcp-protocol
description: MCP (Model Context Protocol) implementation patterns. Use when working on MCP tools, the MCP server, tool registration, or agent-facing interfaces. Covers JSON-RPC format, stdio/SSE transport, tool definition patterns, and the mcp Python SDK.
---

# MCP Protocol Patterns

## When to Use
- Creating or modifying MCP tools in `packages/api/src/mcp/tools/`
- Working on the MCP server in `packages/api/src/mcp/server.py`
- Debugging agent connections
- Adding new tool parameters or response shapes

## Tool Definition Pattern

Every MCP tool follows this structure:

```python
from pydantic import BaseModel, Field
from typing import Optional

class ListEntitiesParams(BaseModel):
    """Input parameters — becomes the tool's JSON schema."""
    kind: Optional[str] = Field(None, description="Filter by entity kind: service, database, function, class, module")
    active_only: bool = Field(True, description="Only return active entities")

async def handle_list_entities(params: ListEntitiesParams, ctx: AuthContext, repo: EntitiesRepository) -> list[dict]:
    """Handler — validate, query, return. No business logic here."""
    return await repo.list_entities(
        project_id=ctx.project_id,
        kind=params.kind,
        active_only=params.active_only,
    )

# Tool metadata for registration
TOOL = {
    "name": "list_entities",
    "description": "List all entities in the project. Returns services, databases, functions, classes, etc.",
    "params_model": ListEntitiesParams,
    "handler": handle_list_entities,
}
```

## Key Rules

- Tool descriptions must be clear enough that an AI agent knows when to call it without human guidance
- Parameters use Pydantic models — the JSON schema is auto-generated from this
- Handlers are async, receive parsed params + AuthContext + repository dependencies
- Return plain dicts/lists — the MCP server handles JSON serialization
- Never raise exceptions for expected cases (empty results, not found) — return empty list or None
- Raise `ToolError` only for actual errors (DB failure, auth failure)

## MCP Python SDK Usage

```python
from mcp.server import Server
from mcp.types import Tool

server = Server("semantic-canvas")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [tool.to_mcp_tool() for tool in registry.all_tools()]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    tool = registry.get(name)
    params = tool.params_model(**arguments)
    result = await tool.handler(params, ctx, repo)
    return [TextContent(type="text", text=json.dumps(result))]
```

## Transports

- **stdio**: for local agents (Claude Code, Cursor). Server reads from stdin, writes to stdout.
- **SSE**: for remote agents over HTTP. FastAPI endpoint at `/mcp/sse` handles the SSE stream.

Both transports use the same server instance and tool registry.
