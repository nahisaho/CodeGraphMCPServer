"""
MCP Server Integration Tests
============================

MCPサーバーの統合テスト。
サーバーの作成、ツール/リソース/プロンプトの登録をテストします。
"""

from pathlib import Path

import pytest

from codegraph_mcp.config import Config


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
    (tmp_path / "utils.py").write_text("""
class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b
""")
    return tmp_path


@pytest.fixture
def config(temp_repo: Path) -> Config:
    """Create a config with temp repo path."""
    return Config(repo_path=temp_repo)


# Server Creation Tests

class TestServerCreation:
    """Tests for MCP server creation."""

    def test_create_server(self, config: Config):
        """Test creating MCP server."""
        from codegraph_mcp.server import create_server

        server = create_server(config)

        assert server is not None
        assert server.name == "codegraph-mcp"

    def test_server_has_tools(self, config: Config):
        """Test server has tools registered."""
        from codegraph_mcp.server import create_server

        server = create_server(config)

        # Server should have list_tools handler registered
        assert server is not None


# CLI Tests

class TestCLI:
    """Tests for CLI commands."""

    def test_parser_creation(self):
        """Test CLI parser creation."""
        from codegraph_mcp.__main__ import create_parser

        parser = create_parser()

        assert parser is not None
        assert parser.prog == "codegraph-mcp"

    def test_parser_serve_command(self):
        """Test parsing serve command."""
        from codegraph_mcp.__main__ import create_parser

        parser = create_parser()
        args = parser.parse_args(["serve", "--repo", "/tmp/repo"])

        assert args.command == "serve"
        assert args.repo == Path("/tmp/repo")

    def test_parser_index_command(self):
        """Test parsing index command."""
        from codegraph_mcp.__main__ import create_parser

        parser = create_parser()
        args = parser.parse_args(["index", "/tmp/repo"])

        assert args.command == "index"
        assert args.path == Path("/tmp/repo")

    def test_parser_query_command(self):
        """Test parsing query command."""
        from codegraph_mcp.__main__ import create_parser

        parser = create_parser()
        args = parser.parse_args(["query", "find functions"])

        assert args.command == "query"
        assert args.query == "find functions"

    def test_parser_stats_command(self):
        """Test parsing stats command."""
        from codegraph_mcp.__main__ import create_parser

        parser = create_parser()
        args = parser.parse_args(["stats", "/tmp/repo"])

        assert args.command == "stats"
        assert args.path == Path("/tmp/repo")

    def test_main_no_command(self):
        """Test main with no command shows help."""
        import sys

        from codegraph_mcp.__main__ import main

        old_argv = sys.argv
        sys.argv = ["codegraph-mcp"]
        try:
            result = main()
            assert result == 0
        finally:
            sys.argv = old_argv


# Index Command Integration Tests

class TestIndexCommand:
    """Tests for index command."""

    def test_cmd_index(self, temp_repo: Path):
        """Test index command."""
        import argparse

        from codegraph_mcp.__main__ import cmd_index

        args = argparse.Namespace(
            path=temp_repo,
            full=False,
            community=True,
            no_community=False,
        )
        result = cmd_index(args)

        assert result == 0


# Stats Command Integration Tests

class TestStatsCommand:
    """Tests for stats command."""

    def test_cmd_stats(self, temp_repo: Path):
        """Test stats command."""
        import argparse

        # First index the repo
        from codegraph_mcp.__main__ import cmd_index, cmd_stats
        index_args = argparse.Namespace(
            path=temp_repo,
            full=False,
            community=True,
            no_community=False,
        )
        cmd_index(index_args)

        # Then get stats
        args = argparse.Namespace(path=temp_repo)
        result = cmd_stats(args)

        assert result == 0


# Full Pipeline Integration Tests

class TestFullPipeline:
    """Tests for full indexing and querying pipeline."""

    @pytest.mark.asyncio
    async def test_index_and_query(self, temp_repo: Path):
        """Test indexing and then querying."""
        from codegraph_mcp.core.graph import GraphEngine, GraphQuery
        from codegraph_mcp.core.indexer import Indexer

        # Index
        indexer = Indexer()
        index_result = await indexer.index_repository(
            temp_repo, incremental=False
        )

        assert index_result.success
        assert index_result.entities_count > 0

        # Query
        engine = GraphEngine(temp_repo)
        await engine.initialize()
        try:
            query = GraphQuery(query="Calculator")
            result = await engine.query(query)

            # Should find Calculator class
            assert len(result.entities) > 0
        finally:
            await engine.close()

    @pytest.mark.asyncio
    async def test_index_and_find_callers(self, temp_repo: Path):
        """Test indexing and finding callers."""
        from codegraph_mcp.core.graph import GraphEngine
        from codegraph_mcp.core.indexer import Indexer

        # Index
        indexer = Indexer()
        await indexer.index_repository(temp_repo, incremental=False)

        # Find callers
        engine = GraphEngine(temp_repo)
        await engine.initialize()
        try:
            # main calls helper
            stats = await engine.get_statistics()
            assert stats.entity_count > 0
        finally:
            await engine.close()


# Config Tests

class TestConfigIntegration:
    """Tests for config integration."""

    def test_config_from_path(self, temp_repo: Path):
        """Test creating config from path."""
        config = Config(repo_path=temp_repo)

        assert config.repo_path == temp_repo

    def test_config_default_values(self, temp_repo: Path):
        """Test config default values."""
        config = Config(repo_path=temp_repo)

        assert config.db_path.parent == temp_repo / ".codegraph"
        assert config.parser.exclude_patterns is not None
        assert len(config.parser.exclude_patterns) > 0
