"""
MCP Prompts Unit Tests
======================

MCPプロンプトの単体テスト。
REQ-PRM-001 ~ REQ-PRM-006
"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from codegraph_mcp.config import Config
from codegraph_mcp.core.graph import GraphStatistics, QueryResult
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
        languages=["python"],
    )


# Dispatch Tests

class TestPromptDispatch:
    """Test prompt dispatch logic."""

    @pytest.mark.asyncio
    async def test_dispatch_known_prompt(
        self,
        mock_entity: Entity,
        config: Config,
    ):
        """Test dispatching known prompt."""
        from codegraph_mcp.mcp.prompts import _dispatch_prompt

        mock_engine = AsyncMock()
        mock_engine.get_entity.return_value = mock_entity
        mock_engine.find_callers.return_value = []
        mock_engine.find_callees.return_value = []

        result = await _dispatch_prompt(
            "code_review",
            {"entity_id": "test_func"},
            mock_engine,
            config,
        )

        assert len(result) == 1
        assert result[0].role == "user"
        assert "Code Review" in result[0].content.text

    @pytest.mark.asyncio
    async def test_dispatch_unknown_prompt(self, config: Config):
        """Test dispatching unknown prompt."""
        from codegraph_mcp.mcp.prompts import _dispatch_prompt

        mock_engine = AsyncMock()

        result = await _dispatch_prompt(
            "unknown_prompt",
            {},
            mock_engine,
            config,
        )

        assert "Unknown prompt" in result[0].content.text


# Code Review Prompt Tests (REQ-PRM-001)

class TestCodeReviewPrompt:
    """Tests for code_review prompt."""

    @pytest.mark.asyncio
    async def test_code_review_entity_found(
        self,
        mock_entity: Entity,
        config: Config,
    ):
        """Test code review with existing entity."""
        from codegraph_mcp.mcp.prompts import _prompt_code_review

        mock_engine = AsyncMock()
        mock_engine.get_entity.return_value = mock_entity
        mock_engine.find_callers.return_value = []
        mock_engine.find_callees.return_value = []

        result = await _prompt_code_review(
            {"entity_id": "test_func", "focus": "security"},
            mock_engine,
            config,
        )

        content = result[0].content.text
        assert "test_function" in content
        assert "security" in content
        assert "Code Review Request" in content

    @pytest.mark.asyncio
    async def test_code_review_entity_not_found(self, config: Config):
        """Test code review with non-existent entity."""
        from codegraph_mcp.mcp.prompts import _prompt_code_review

        mock_engine = AsyncMock()
        mock_engine.get_entity.return_value = None

        result = await _prompt_code_review(
            {"entity_id": "nonexistent"},
            mock_engine,
            config,
        )

        assert "not found" in result[0].content.text


# Explain Codebase Prompt Tests (REQ-PRM-002)

class TestExplainCodebasePrompt:
    """Tests for explain_codebase prompt."""

    @pytest.mark.asyncio
    async def test_explain_codebase(
        self,
        mock_stats: GraphStatistics,
        config: Config,
    ):
        """Test explain codebase prompt."""
        from codegraph_mcp.mcp.prompts import _prompt_explain_codebase

        mock_engine = AsyncMock()
        mock_engine.get_statistics.return_value = mock_stats

        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [
            ("Core Module", "Main functionality", 10),
        ]
        mock_engine._connection.execute.return_value = mock_cursor

        result = await _prompt_explain_codebase(
            {"depth": "detailed"},
            mock_engine,
            config,
        )

        content = result[0].content.text
        assert "100" in content  # entity count
        assert "detailed" in content


# Implement Feature Prompt Tests (REQ-PRM-003)

class TestImplementFeaturePrompt:
    """Tests for implement_feature prompt."""

    @pytest.mark.asyncio
    async def test_implement_feature(self, config: Config):
        """Test implement feature prompt."""
        from codegraph_mcp.mcp.prompts import _prompt_implement_feature

        mock_engine = AsyncMock()
        mock_result = QueryResult(entities=[], relations=[])
        mock_engine.query.return_value = mock_result

        result = await _prompt_implement_feature(
            {"description": "Add user authentication"},
            mock_engine,
            config,
        )

        content = result[0].content.text
        assert "Feature Implementation" in content
        assert "Add user authentication" in content


# Debug Issue Prompt Tests (REQ-PRM-004)

class TestDebugIssuePrompt:
    """Tests for debug_issue prompt."""

    @pytest.mark.asyncio
    async def test_debug_issue(self, config: Config):
        """Test debug issue prompt."""
        from codegraph_mcp.mcp.prompts import _prompt_debug_issue

        mock_engine = AsyncMock()
        mock_result = QueryResult(entities=[], relations=[])
        mock_engine.query.return_value = mock_result

        result = await _prompt_debug_issue(
            {
                "error_message": "TypeError: cannot read property",
                "context": "Happens on login",
            },
            mock_engine,
            config,
        )

        content = result[0].content.text
        assert "Debug Assistance" in content
        assert "TypeError" in content
        assert "login" in content


# Refactor Guidance Prompt Tests (REQ-PRM-005)

class TestRefactorGuidancePrompt:
    """Tests for refactor_guidance prompt."""

    @pytest.mark.asyncio
    async def test_refactor_guidance(
        self,
        mock_entity: Entity,
        config: Config,
    ):
        """Test refactor guidance prompt."""
        from codegraph_mcp.mcp.prompts import _prompt_refactor_guidance

        mock_engine = AsyncMock()
        mock_engine.get_entity.return_value = mock_entity
        mock_engine.find_callers.return_value = []
        mock_engine.find_callees.return_value = []

        result = await _prompt_refactor_guidance(
            {"entity_id": "test_func", "goal": "reduce complexity"},
            mock_engine,
            config,
        )

        content = result[0].content.text
        assert "Refactoring Guidance" in content
        assert "reduce complexity" in content

    @pytest.mark.asyncio
    async def test_refactor_guidance_entity_not_found(self, config: Config):
        """Test refactor guidance with non-existent entity."""
        from codegraph_mcp.mcp.prompts import _prompt_refactor_guidance

        mock_engine = AsyncMock()
        mock_engine.get_entity.return_value = None

        result = await _prompt_refactor_guidance(
            {"entity_id": "nonexistent"},
            mock_engine,
            config,
        )

        assert "not found" in result[0].content.text


# Test Generation Prompt Tests (REQ-PRM-006)

class TestTestGenerationPrompt:
    """Tests for test_generation prompt."""

    @pytest.mark.asyncio
    async def test_test_generation(
        self,
        mock_entity: Entity,
        config: Config,
    ):
        """Test test generation prompt."""
        from codegraph_mcp.mcp.prompts import _prompt_test_generation

        mock_engine = AsyncMock()
        mock_engine.get_entity.return_value = mock_entity
        mock_result = QueryResult(entities=[], relations=[])
        mock_engine.find_dependencies.return_value = mock_result

        result = await _prompt_test_generation(
            {"entity_id": "test_func", "test_type": "integration"},
            mock_engine,
            config,
        )

        content = result[0].content.text
        assert "Test Generation" in content
        assert "integration" in content

    @pytest.mark.asyncio
    async def test_test_generation_entity_not_found(self, config: Config):
        """Test test generation with non-existent entity."""
        from codegraph_mcp.mcp.prompts import _prompt_test_generation

        mock_engine = AsyncMock()
        mock_engine.get_entity.return_value = None

        result = await _prompt_test_generation(
            {"entity_id": "nonexistent"},
            mock_engine,
            config,
        )

        assert "not found" in result[0].content.text


# Registration Tests

class TestPromptRegistration:
    """Tests for prompt registration."""

    def test_register_prompts(self, config: Config):
        """Test registering prompts with server."""
        from mcp.server import Server

        from codegraph_mcp.mcp.prompts import register

        server = Server("test")
        register(server, config)

        # Registration should not raise
        assert server is not None
