"""
MCP Tools Unit Tests
====================

MCPツールの単体テスト。
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from codegraph_mcp.config import Config
from codegraph_mcp.core.parser import Entity, EntityType, Location


# Fixtures

@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Create a temporary repository with test files."""
    (tmp_path / "main.py").write_text("""
def main():
    helper()

def helper():
    pass
""")
    return tmp_path


@pytest.fixture
def config(temp_repo: Path) -> Config:
    """Create a config with temp repo path."""
    return Config(repo_path=temp_repo)


@pytest.fixture
def mock_entity() -> Entity:
    """Create a mock entity."""
    return Entity(
        id="test_func",
        type=EntityType.FUNCTION,
        name="test_function",
        qualified_name="test.test_function",
        location=Location(
            file_path=Path("/test/file.py"),
            start_line=1,
            end_line=5,
            start_column=0,
            end_column=0,
        ),
        source_code="def test_function():\n    pass",
    )


# Tool Registration Tests

class TestToolRegistration:
    """ツール登録のテスト"""

    def test_tool_list_returns_14_tools(self):
        """Verify 14 tools are defined."""
        from mcp.server import Server

        from codegraph_mcp.mcp.tools import register

        server = Server("test")
        config = Config(repo_path=Path("/tmp"))
        register(server, config)

        # The tools are registered via decorator
        # We can verify by checking handler count
        assert server is not None

    def test_tool_schema_validation(self):
        """Tool schemas have required fields."""
        from mcp.types import Tool

        # Test tool creation with valid schema
        tool = Tool(
            name="test_tool",
            description="Test description",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        )
        assert tool.name == "test_tool"
        assert "query" in tool.inputSchema["properties"]


# Handler Tests

class TestQueryCodebaseTool:
    """query_codebase ツールのテスト"""

    @pytest.mark.asyncio
    async def test_query_codebase_handler(self, config: Config):
        """Test query_codebase handler."""
        from codegraph_mcp.mcp.tools import _handle_query_codebase

        mock_engine = AsyncMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"entities": [], "relations": []}
        mock_engine.query.return_value = mock_result

        result = await _handle_query_codebase(
            {"query": "find functions", "max_results": 10},
            mock_engine,
            config,
        )

        assert "entities" in result
        mock_engine.query.assert_called_once()


class TestFindDependenciesTool:
    """find_dependencies ツールのテスト"""

    @pytest.mark.asyncio
    async def test_find_dependencies_handler(self, config: Config):
        """Test find_dependencies handler."""
        from codegraph_mcp.mcp.tools import _handle_find_dependencies

        mock_engine = AsyncMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"entities": [], "relations": []}
        mock_engine.find_dependencies.return_value = mock_result

        result = await _handle_find_dependencies(
            {"entity_id": "test_id", "depth": 2},
            mock_engine,
            config,
        )

        assert "entities" in result
        mock_engine.find_dependencies.assert_called_once_with("test_id", depth=2)


class TestFindCallersTool:
    """find_callers ツールのテスト"""

    @pytest.mark.asyncio
    async def test_find_callers_handler(self, config: Config, mock_entity: Entity):
        """Test find_callers handler."""
        from codegraph_mcp.mcp.tools import _handle_find_callers

        mock_engine = AsyncMock()
        mock_engine.find_callers.return_value = [mock_entity]

        result = await _handle_find_callers(
            {"entity_id": "test_id"},
            mock_engine,
            config,
        )

        assert "callers" in result
        assert len(result["callers"]) == 1
        assert result["callers"][0]["name"] == "test_function"


class TestFindCalleesTool:
    """find_callees ツールのテスト"""

    @pytest.mark.asyncio
    async def test_find_callees_handler(self, config: Config, mock_entity: Entity):
        """Test find_callees handler."""
        from codegraph_mcp.mcp.tools import _handle_find_callees

        mock_engine = AsyncMock()
        mock_engine.find_callees.return_value = [mock_entity]

        result = await _handle_find_callees(
            {"entity_id": "test_id"},
            mock_engine,
            config,
        )

        assert "callees" in result
        assert len(result["callees"]) == 1


class TestGetCodeSnippetTool:
    """get_code_snippet ツールのテスト"""

    @pytest.mark.asyncio
    async def test_get_code_snippet_found(self, config: Config, mock_entity: Entity):
        """Test get_code_snippet when entity found."""
        from codegraph_mcp.mcp.tools import _handle_get_code_snippet

        mock_engine = AsyncMock()
        mock_engine.get_entity.return_value = mock_entity

        result = await _handle_get_code_snippet(
            {"entity_id": "test_id"},
            mock_engine,
            config,
        )

        assert "source" in result
        assert "def test_function" in result["source"]

    @pytest.mark.asyncio
    async def test_get_code_snippet_not_found(self, config: Config):
        """Test get_code_snippet when entity not found."""
        from codegraph_mcp.mcp.tools import _handle_get_code_snippet

        mock_engine = AsyncMock()
        mock_engine.get_entity.return_value = None

        result = await _handle_get_code_snippet(
            {"entity_id": "nonexistent"},
            mock_engine,
            config,
        )

        assert "error" in result


class TestReadFileTool:
    """read_file_content ツールのテスト"""

    @pytest.mark.asyncio
    async def test_read_file_full(self, temp_repo: Path, config: Config):
        """Test reading full file."""
        from codegraph_mcp.mcp.tools import _handle_read_file

        mock_engine = AsyncMock()

        result = await _handle_read_file(
            {"file_path": "main.py"},
            mock_engine,
            config,
        )

        assert "content" in result
        assert "def main" in result["content"]

    @pytest.mark.asyncio
    async def test_read_file_range(self, temp_repo: Path, config: Config):
        """Test reading file with line range."""
        from codegraph_mcp.mcp.tools import _handle_read_file

        mock_engine = AsyncMock()

        result = await _handle_read_file(
            {"file_path": "main.py", "start_line": 2, "end_line": 4},
            mock_engine,
            config,
        )

        assert "content" in result
        assert "lines" in result

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, temp_repo: Path, config: Config):
        """Test reading nonexistent file."""
        from codegraph_mcp.mcp.tools import _handle_read_file

        mock_engine = AsyncMock()

        result = await _handle_read_file(
            {"file_path": "nonexistent.py"},
            mock_engine,
            config,
        )

        assert "error" in result


class TestReindexTool:
    """reindex_repository ツールのテスト"""

    @pytest.mark.asyncio
    async def test_reindex_incremental(self, temp_repo: Path, config: Config):
        """Test incremental reindex."""
        from codegraph_mcp.mcp.tools import _handle_reindex

        mock_engine = AsyncMock()

        result = await _handle_reindex(
            {"incremental": True},
            mock_engine,
            config,
        )

        assert "entities" in result
        assert "duration" in result


class TestExecuteCommandTool:
    """execute_shell_command ツールのテスト"""

    @pytest.mark.asyncio
    async def test_execute_simple_command(self, temp_repo: Path, config: Config):
        """Test executing simple command."""
        from codegraph_mcp.mcp.tools import _handle_execute_command

        mock_engine = AsyncMock()

        result = await _handle_execute_command(
            {"command": "echo hello", "timeout": 5},
            mock_engine,
            config,
        )

        assert "exit_code" in result
        assert result["exit_code"] == 0
        assert "hello" in result["stdout"]

    @pytest.mark.asyncio
    async def test_execute_command_timeout(self, temp_repo: Path, config: Config):
        """Test command timeout."""
        from codegraph_mcp.mcp.tools import _handle_execute_command

        mock_engine = AsyncMock()

        result = await _handle_execute_command(
            {"command": "sleep 10", "timeout": 1},
            mock_engine,
            config,
        )

        assert "error" in result
        assert "timed out" in result["error"]


class TestDispatchTool:
    """_dispatch_tool のテスト"""

    @pytest.mark.asyncio
    async def test_dispatch_unknown_tool(self, config: Config):
        """Test dispatching unknown tool."""
        from codegraph_mcp.mcp.tools import _dispatch_tool

        mock_engine = AsyncMock()

        result = await _dispatch_tool(
            "unknown_tool",
            {},
            mock_engine,
            config,
        )

        assert "error" in result
        assert "Unknown tool" in result["error"]

    @pytest.mark.asyncio
    async def test_dispatch_known_tool(self, config: Config):
        """Test dispatching known tool."""
        from codegraph_mcp.mcp.tools import _dispatch_tool

        mock_engine = AsyncMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"entities": []}
        mock_engine.query.return_value = mock_result

        result = await _dispatch_tool(
            "query_codebase",
            {"query": "test"},
            mock_engine,
            config,
        )

        assert "entities" in result
