"""
MCP Resources Unit Tests
========================

MCPリソースの単体テスト。
REQ-RSC-001 ~ REQ-RSC-004
"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from codegraph_mcp.config import Config
from codegraph_mcp.core.graph import GraphStatistics
from codegraph_mcp.core.parser import Entity, EntityType, Location


# Fixtures

@pytest.fixture
def config(tmp_path: Path) -> Config:
    """Create a config with temp repo path."""
    return Config(repo_path=tmp_path)


@pytest.fixture
def mock_entity() -> Entity:
    """Create a mock entity."""
    return Entity(
        id="test_func",
        type=EntityType.FUNCTION,
        name="test_function",
        qualified_name="module.test_function",
        location=Location(
            file_path=Path("/test/file.py"),
            start_line=1,
            end_line=10,
            start_column=0,
            end_column=0,
        ),
        signature="def test_function(a: int) -> str",
        docstring="Test function docstring",
        source_code="def test_function(a: int) -> str:\n    return str(a)",
    )


@pytest.fixture
def mock_stats() -> GraphStatistics:
    """Create mock statistics."""
    return GraphStatistics(
        entity_count=100,
        relation_count=200,
        community_count=5,
        file_count=20,
        entities_by_type={"function": 50, "class": 30, "module": 20},
        relations_by_type={"calls": 100, "imports": 50, "contains": 50},
        languages=["python", "typescript"],
    )


# Dispatch Tests

class TestResourceDispatch:
    """Test resource dispatch logic."""

    @pytest.mark.asyncio
    async def test_dispatch_entity_resource(self, mock_entity: Entity):
        """Test dispatching entity resource."""
        from codegraph_mcp.mcp.resources import _dispatch_resource

        mock_engine = AsyncMock()
        mock_engine.get_entity.return_value = mock_entity
        mock_engine.find_callers.return_value = []
        mock_engine.find_callees.return_value = []

        result = await _dispatch_resource(
            "codegraph://entities/test_func",
            mock_engine,
        )

        assert "entity" in result
        assert result["entity"]["id"] == "test_func"
        mock_engine.get_entity.assert_called_once_with("test_func")

    @pytest.mark.asyncio
    async def test_dispatch_stats_resource(self, mock_stats: GraphStatistics):
        """Test dispatching stats resource."""
        from codegraph_mcp.mcp.resources import _dispatch_resource

        mock_engine = AsyncMock()
        mock_engine.get_statistics.return_value = mock_stats

        result = await _dispatch_resource("codegraph://stats", mock_engine)

        assert "statistics" in result
        assert result["statistics"]["entities"] == 100
        mock_engine.get_statistics.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_unknown_resource(self):
        """Test dispatching unknown resource."""
        from codegraph_mcp.mcp.resources import _dispatch_resource

        mock_engine = AsyncMock()

        result = await _dispatch_resource(
            "codegraph://unknown/resource",
            mock_engine,
        )

        assert "error" in result


# Entity Resource Tests

class TestEntityResource:
    """Tests for entity resource (REQ-RSC-001)."""

    @pytest.mark.asyncio
    async def test_read_entity_found(self, mock_entity: Entity):
        """Test reading existing entity."""
        from codegraph_mcp.mcp.resources import _read_entity

        mock_engine = AsyncMock()
        mock_engine.get_entity.return_value = mock_entity
        mock_engine.find_callers.return_value = []
        mock_engine.find_callees.return_value = []

        result = await _read_entity("test_func", mock_engine)

        assert result["entity"]["id"] == "test_func"
        assert result["entity"]["name"] == "test_function"
        assert result["entity"]["type"] == "function"
        assert "relations" in result

    @pytest.mark.asyncio
    async def test_read_entity_not_found(self):
        """Test reading non-existent entity."""
        from codegraph_mcp.mcp.resources import _read_entity

        mock_engine = AsyncMock()
        mock_engine.get_entity.return_value = None

        result = await _read_entity("nonexistent", mock_engine)

        assert "error" in result
        assert result["entity_id"] == "nonexistent"

    @pytest.mark.asyncio
    async def test_read_entity_with_relations(self, mock_entity: Entity):
        """Test reading entity with relations."""
        from codegraph_mcp.mcp.resources import _read_entity

        caller = Entity(
            id="caller_func",
            type=EntityType.FUNCTION,
            name="caller",
            qualified_name="module.caller",
            location=Location(
                file_path=Path("/test/file.py"),
                start_line=20,
                end_line=25,
                start_column=0,
                end_column=0,
            ),
        )

        mock_engine = AsyncMock()
        mock_engine.get_entity.return_value = mock_entity
        mock_engine.find_callers.return_value = [caller]
        mock_engine.find_callees.return_value = []

        result = await _read_entity("test_func", mock_engine)

        assert len(result["relations"]["callers"]) == 1
        assert result["relations"]["callers"][0]["name"] == "caller"


# File Graph Resource Tests

class TestFileGraphResource:
    """Tests for file graph resource (REQ-RSC-002)."""

    @pytest.mark.asyncio
    async def test_read_file_graph(self):
        """Test reading file graph."""
        from codegraph_mcp.mcp.resources import _read_file_graph

        mock_engine = AsyncMock()

        # Mock cursor for entities
        entity_cursor = AsyncMock()
        entity_cursor.fetchall.return_value = [
            ("func1", "function", "function1", 1, 10, "def function1()"),
            ("func2", "function", "function2", 12, 20, "def function2()"),
        ]

        # Mock cursor for relations
        relation_cursor = AsyncMock()
        relation_cursor.fetchall.return_value = [
            ("func1", "func2", "calls"),
        ]

        mock_engine._connection.execute.side_effect = [
            entity_cursor,
            relation_cursor,
        ]

        result = await _read_file_graph("test/file.py", mock_engine)

        assert result["file_path"] == "test/file.py"
        assert len(result["entities"]) == 2
        assert len(result["relations"]) == 1
        assert result["entity_count"] == 2

    @pytest.mark.asyncio
    async def test_read_file_graph_empty(self):
        """Test reading empty file graph."""
        from codegraph_mcp.mcp.resources import _read_file_graph

        mock_engine = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []
        mock_engine._connection.execute.return_value = mock_cursor

        result = await _read_file_graph("empty.py", mock_engine)

        assert result["entities"] == []
        assert result["relations"] == []
        assert result["entity_count"] == 0


# Statistics Resource Tests

class TestStatsResource:
    """Tests for statistics resource (REQ-RSC-004)."""

    @pytest.mark.asyncio
    async def test_read_stats(self, mock_stats: GraphStatistics):
        """Test reading statistics."""
        from codegraph_mcp.mcp.resources import _read_stats

        mock_engine = AsyncMock()
        mock_engine.get_statistics.return_value = mock_stats

        result = await _read_stats(mock_engine)

        assert result["statistics"]["entities"] == 100
        assert result["statistics"]["relations"] == 200
        assert result["statistics"]["communities"] == 5
        assert result["statistics"]["files"] == 20
        assert "python" in result["statistics"]["languages"]
        assert result["entities_by_type"]["function"] == 50


# Community Resource Tests

class TestCommunityResource:
    """Tests for community resource (REQ-RSC-003)."""

    @pytest.mark.asyncio
    async def test_read_community_found(self):
        """Test reading existing community."""
        from codegraph_mcp.mcp.resources import _read_community

        mock_engine = AsyncMock()

        # Mock community query
        community_cursor = AsyncMock()
        community_cursor.fetchone.return_value = (
            1,
            0,
            "Core Module",
            "Main functionality",
            10,
        )

        # Mock members query
        members_cursor = AsyncMock()
        members_cursor.fetchall.return_value = [
            ("entity1", "function", "func1", "/path/file.py"),
            ("entity2", "class", "MyClass", "/path/file.py"),
        ]

        mock_engine._connection.execute.side_effect = [
            community_cursor,
            members_cursor,
        ]

        result = await _read_community(1, mock_engine)

        assert result["community"]["id"] == 1
        assert result["community"]["name"] == "Core Module"
        assert len(result["members"]) == 2

    @pytest.mark.asyncio
    async def test_read_community_not_found(self):
        """Test reading non-existent community."""
        from codegraph_mcp.mcp.resources import _read_community

        mock_engine = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_engine._connection.execute.return_value = mock_cursor

        result = await _read_community(999, mock_engine)

        assert "error" in result
        assert result["community_id"] == 999


# Registration Tests

class TestResourceRegistration:
    """Tests for resource registration."""

    def test_register_resources(self, config: Config):
        """Test registering resources with server."""
        from mcp.server import Server

        from codegraph_mcp.mcp.resources import register

        server = Server("test")
        register(server, config)

        # Registration should not raise
        assert server is not None
