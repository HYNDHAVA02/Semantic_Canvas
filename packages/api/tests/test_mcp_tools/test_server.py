"""Tests for the MCP server wiring: tool conversion, DI, dispatch."""

from __future__ import annotations

from unittest.mock import MagicMock

import asyncpg
import pytest

from src.mcp.registry import register_all_tools, registry
from src.mcp.server import (
    _build_dependency_map,
    _resolve_and_call,
    _tool_to_mcp,
    create_mcp_server,
)
from src.repositories.entities import EntitiesRepository


def _mock_embedding_service() -> MagicMock:
    """Create a mock EmbeddingService that avoids importing fastembed."""
    mock = MagicMock()
    mock.embed_one.return_value = [0.0] * 384
    return mock


class TestToolToMcp:
    """Tests for converting ToolDefinition -> MCP Tool."""

    def test_converts_name_and_description(self) -> None:
        """Tool name and description are carried through."""
        register_all_tools()
        tool_def = registry.get("list_entities")
        assert tool_def is not None

        mcp_tool = _tool_to_mcp(tool_def)

        assert mcp_tool.name == "list_entities"
        assert mcp_tool.description is not None
        assert len(mcp_tool.description) > 0

    def test_input_schema_has_properties(self) -> None:
        """inputSchema is a valid JSON Schema with properties."""
        register_all_tools()
        tool_def = registry.get("list_entities")
        assert tool_def is not None

        mcp_tool = _tool_to_mcp(tool_def)

        assert "properties" in mcp_tool.inputSchema
        assert "project_id" in mcp_tool.inputSchema["properties"]


class TestBuildDependencyMap:
    """Tests for the dependency map builder."""

    def test_all_types_present(self, db_pool: asyncpg.Pool) -> None:
        """All 8 dependency types are in the map."""
        mock_emb = _mock_embedding_service()
        dep_map = _build_dependency_map(db_pool, mock_emb)

        expected_keys = [
            "EntitiesRepository",
            "RelationshipsRepository",
            "DecisionsRepository",
            "ConventionsRepository",
            "ActivityRepository",
            "SearchRepository",
            "BlastRadiusService",
            "EmbeddingService",
        ]
        for key in expected_keys:
            assert key in dep_map, f"Missing dependency: {key}"
        assert len(dep_map) == 8


@pytest.mark.asyncio
class TestResolveAndCall:
    """Tests for the resolve-and-call dispatch."""

    async def test_dispatches_repo_tool(
        self, db_pool: asyncpg.Pool, test_project: dict
    ) -> None:
        """Dispatches list_entities and gets back a list."""
        register_all_tools()
        tool = registry.get("list_entities")
        assert tool is not None

        mock_emb = _mock_embedding_service()
        dep_map = _build_dependency_map(db_pool, mock_emb)

        result = await _resolve_and_call(
            tool,
            {"project_id": str(test_project["id"])},
            dep_map,
        )

        assert isinstance(result, list)

    async def test_dispatches_tool_with_embedding_service(
        self, db_pool: asyncpg.Pool, test_project: dict
    ) -> None:
        """Dispatches add_entity with embedding service injected."""
        register_all_tools()
        tool = registry.get("add_entity")
        assert tool is not None

        mock_emb = _mock_embedding_service()
        dep_map = _build_dependency_map(db_pool, mock_emb)

        result = await _resolve_and_call(
            tool,
            {
                "project_id": str(test_project["id"]),
                "name": "TestService",
                "kind": "service",
            },
            dep_map,
        )

        assert isinstance(result, dict)
        assert result["name"] == "TestService"
        mock_emb.embed_one.assert_called_once()

    async def test_dispatches_blast_radius(
        self, db_pool: asyncpg.Pool, test_project: dict
    ) -> None:
        """Dispatches blast_radius with BlastRadiusService."""
        register_all_tools()
        tool = registry.get("blast_radius")
        assert tool is not None

        # Create an entity to query
        repo = EntitiesRepository(db_pool)
        created = await repo.create(
            project_id=test_project["id"],
            name="BlastTarget",
            kind="service",
        )

        mock_emb = _mock_embedding_service()
        dep_map = _build_dependency_map(db_pool, mock_emb)

        result = await _resolve_and_call(
            tool,
            {
                "project_id": str(test_project["id"]),
                "entity_id": str(created["id"]),
            },
            dep_map,
        )

        assert isinstance(result, dict)


@pytest.mark.asyncio
class TestCreateMcpServer:
    """Tests for the full MCP server."""

    async def test_list_tools_count(self, db_pool: asyncpg.Pool) -> None:
        """list_tools returns all 14 registered tools."""
        register_all_tools()
        mock_emb = _mock_embedding_service()
        _server = create_mcp_server(db_pool, mock_emb)

        tools = [_tool_to_mcp(t) for t in registry.all_tools()]
        assert len(tools) == 14

    async def test_tool_names(self, db_pool: asyncpg.Pool) -> None:
        """All expected tool names are registered."""
        register_all_tools()
        tool_names = {t.name for t in registry.all_tools()}

        expected = {
            "list_entities",
            "get_entity",
            "get_relationships",
            "blast_radius",
            "search",
            "get_decisions",
            "get_conventions",
            "get_recent_activity",
            "get_dead_code",
            "log_decision",
            "log_convention",
            "log_activity",
            "add_entity",
            "add_relationship",
        }
        assert tool_names == expected
