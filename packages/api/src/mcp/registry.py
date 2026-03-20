"""MCP tool registry — maps tool names to handlers.

All MCP tools are registered here. The MCP server uses this
registry to list available tools and dispatch calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel


@dataclass
class ToolDefinition:
    """A registered MCP tool."""

    name: str
    description: str
    params_model: type[BaseModel]
    handler: Callable[..., Any]


class ToolRegistry:
    """Registry of all available MCP tools."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool definition."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def all_tools(self) -> list[ToolDefinition]:
        """List all registered tools."""
        return list(self._tools.values())


# Global registry instance
registry = ToolRegistry()


def register_all_tools() -> None:
    """Register all MCP tools. Called at startup to avoid circular imports."""
    from src.mcp.tools.add_entity import TOOL as add_entity_tool
    from src.mcp.tools.add_relationship import TOOL as add_relationship_tool
    from src.mcp.tools.blast_radius import TOOL as blast_radius_tool
    from src.mcp.tools.get_conventions import TOOL as get_conventions_tool
    from src.mcp.tools.get_dead_code import TOOL as get_dead_code_tool
    from src.mcp.tools.get_decisions import TOOL as get_decisions_tool
    from src.mcp.tools.get_entity import TOOL as get_entity_tool
    from src.mcp.tools.get_recent_activity import TOOL as get_recent_activity_tool
    from src.mcp.tools.get_relationships import TOOL as get_relationships_tool
    from src.mcp.tools.list_entities import TOOL as list_entities_tool
    from src.mcp.tools.log_activity import TOOL as log_activity_tool
    from src.mcp.tools.log_convention import TOOL as log_convention_tool
    from src.mcp.tools.log_decision import TOOL as log_decision_tool
    from src.mcp.tools.search import TOOL as search_tool

    # Read tools
    registry.register(list_entities_tool)
    registry.register(get_entity_tool)
    registry.register(get_relationships_tool)
    registry.register(blast_radius_tool)
    registry.register(search_tool)
    registry.register(get_decisions_tool)
    registry.register(get_conventions_tool)
    registry.register(get_recent_activity_tool)
    registry.register(get_dead_code_tool)

    # Write tools
    registry.register(log_decision_tool)
    registry.register(log_convention_tool)
    registry.register(log_activity_tool)
    registry.register(add_entity_tool)
    registry.register(add_relationship_tool)
