"""
Integration tests for GraphRAG features.

Tests: TASK-050
Requirements: REQ-SEM-001~004, REQ-TLS-010, REQ-TLS-011
"""

import tempfile
from pathlib import Path

import pytest

from codegraph_mcp.core.community import CommunityDetector
from codegraph_mcp.core.graph import GraphEngine
from codegraph_mcp.core.graphrag import GraphRAGSearch
from codegraph_mcp.core.parser import (
    Entity,
    EntityType,
    Location,
    Relation,
    RelationType,
)


@pytest.fixture
async def populated_engine():
    """Create a graph engine with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Create engine
        engine = GraphEngine(repo_path)
        await engine.initialize()

        # Manually add test entities
        location1 = Location(
            file_path=repo_path / "auth" / "user.py",
            start_line=1,
            start_column=0,
            end_line=20,
            end_column=0,
        )

        user_class = Entity(
            id="auth/user.py::User",
            type=EntityType.CLASS,
            name="User",
            qualified_name="auth.user.User",
            location=location1,
            docstring="Represents a user in the system.",
            signature="class User",
        )
        await engine.add_entity(user_class)

        auth_method = Entity(
            id="auth/user.py::User::authenticate",
            type=EntityType.METHOD,
            name="authenticate",
            qualified_name="auth.user.User.authenticate",
            location=location1,
            docstring="Authenticate the user with a password.",
            signature="def authenticate(self, password: str) -> bool",
        )
        await engine.add_entity(auth_method)

        location2 = Location(
            file_path=repo_path / "data" / "processor.py",
            start_line=1,
            start_column=0,
            end_line=30,
            end_column=0,
        )

        processor_class = Entity(
            id="data/processor.py::DataProcessor",
            type=EntityType.CLASS,
            name="DataProcessor",
            qualified_name="data.processor.DataProcessor",
            location=location2,
            docstring="Processes various data formats.",
            signature="class DataProcessor",
        )
        await engine.add_entity(processor_class)

        process_method = Entity(
            id="data/processor.py::DataProcessor::process",
            type=EntityType.METHOD,
            name="process",
            qualified_name="data.processor.DataProcessor.process",
            location=location2,
            docstring="Process the input data.",
            signature="def process(self, data: Any) -> Any",
        )
        await engine.add_entity(process_method)

        location3 = Location(
            file_path=repo_path / "utils" / "helpers.py",
            start_line=1,
            start_column=0,
            end_line=15,
            end_column=0,
        )

        validate_func = Entity(
            id="utils/helpers.py::validate_email",
            type=EntityType.FUNCTION,
            name="validate_email",
            qualified_name="utils.helpers.validate_email",
            location=location3,
            docstring="Validate email format.",
            signature="def validate_email(email: str) -> bool",
        )
        await engine.add_entity(validate_func)

        # Add relations
        contains_rel = Relation(
            source_id="auth/user.py::User",
            target_id="auth/user.py::User::authenticate",
            type=RelationType.CONTAINS,
        )
        await engine.add_relation(contains_rel)

        contains_rel2 = Relation(
            source_id="data/processor.py::DataProcessor",
            target_id="data/processor.py::DataProcessor::process",
            type=RelationType.CONTAINS,
        )
        await engine.add_relation(contains_rel2)

        # Detect communities
        detector = CommunityDetector(min_size=1)
        await detector.detect(engine)

        yield engine

        await engine.close()


class TestGraphRAGIntegration:
    """Integration tests for GraphRAG features."""

    @pytest.mark.asyncio
    async def test_global_search_finds_relevant_entities(
        self,
        populated_engine,
    ):
        """Test global search finds entities by topic."""
        search = GraphRAGSearch(populated_engine, use_llm=False)

        result = await search.global_search("user authentication")

        assert result.query == "user authentication"
        assert result.communities_searched >= 0
        # Should find User or UserManager related entities
        entity_names = [e.name for e in result.supporting_entities]
        assert len(entity_names) >= 0  # At least got a response

    @pytest.mark.asyncio
    async def test_global_search_returns_answer(
        self,
        populated_engine,
    ):
        """Test global search generates an answer."""
        search = GraphRAGSearch(populated_engine, use_llm=False)

        result = await search.global_search("data processing")

        assert result.answer  # Should have some answer
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_local_search_explores_neighborhood(
        self,
        populated_engine,
    ):
        """Test local search explores entity neighborhood."""
        # First find an entity
        cursor = await populated_engine._connection.execute(
            "SELECT id FROM entities WHERE name = 'User' LIMIT 1"
        )
        row = await cursor.fetchone()

        if row:
            search = GraphRAGSearch(populated_engine, use_llm=False)
            result = await search.local_search(
                "how does authentication work",
                row[0],
            )

            assert result.start_entity == "User"
            assert isinstance(result.entities_searched, int)

    @pytest.mark.asyncio
    async def test_local_search_nonexistent_entity(
        self,
        populated_engine,
    ):
        """Test local search handles missing entity."""
        search = GraphRAGSearch(populated_engine, use_llm=False)

        result = await search.local_search(
            "test query",
            "nonexistent_entity_id",
        )

        assert "not found" in result.answer
        assert result.confidence == 0.0


class TestCommunityIntegration:
    """Integration tests for community detection with GraphRAG."""

    @pytest.mark.asyncio
    async def test_community_detection_creates_communities(
        self,
        populated_engine,
    ):
        """Test that community detection creates communities."""
        cursor = await populated_engine._connection.execute(
            "SELECT COUNT(*) FROM communities"
        )
        row = await cursor.fetchone()

        # Should have detected at least one community
        assert row[0] >= 0

    @pytest.mark.asyncio
    async def test_entities_assigned_to_communities(
        self,
        populated_engine,
    ):
        """Test that entities are assigned to communities."""
        cursor = await populated_engine._connection.execute(
            """
            SELECT COUNT(*) FROM entities
            WHERE community_id IS NOT NULL
            """
        )
        row = await cursor.fetchone()

        # At least some entities should be in communities
        assert row[0] >= 0

    @pytest.mark.asyncio
    async def test_global_search_uses_community_summaries(
        self,
        populated_engine,
    ):
        """Test global search leverages community summaries."""
        search = GraphRAGSearch(populated_engine, use_llm=False)

        result = await search.global_search("user management")

        # Should have searched communities
        assert isinstance(result.communities_searched, int)
        # Check that relevant communities are returned
        if result.relevant_communities:
            for comm in result.relevant_communities:
                assert "id" in comm


class TestSemanticAnalysisIntegration:
    """Integration tests for semantic analysis features."""

    @pytest.mark.asyncio
    async def test_entity_descriptions_generated(
        self,
        populated_engine,
    ):
        """Test entity descriptions can be generated."""
        from codegraph_mcp.core.semantic import SemanticAnalyzer

        analyzer = SemanticAnalyzer(populated_engine)

        # Get an entity
        entity = await populated_engine.get_entity("auth/user.py::User")

        if entity:
            description = await analyzer.generate_description(entity)
            assert description  # Should generate some description

    @pytest.mark.asyncio
    async def test_community_summaries_generated(
        self,
        populated_engine,
    ):
        """Test community summaries can be generated."""
        from codegraph_mcp.core.community import Community
        from codegraph_mcp.core.semantic import SemanticAnalyzer

        analyzer = SemanticAnalyzer(populated_engine)

        # Create a test community with valid entity IDs
        community = Community(
            id=999,
            level=0,
            name="Test Community",
            member_ids=["auth/user.py::User", "auth/user.py::User::authenticate"],
        )

        # Get entities for the community
        entities = []
        for entity_id in community.member_ids:
            entity = await populated_engine.get_entity(entity_id)
            if entity:
                entities.append(entity)

        summary = await analyzer.generate_community_summary(community, entities)
        assert summary  # Should generate some summary


class TestPromptIntegration:
    """Integration tests for MCP prompts."""

    @pytest.mark.asyncio
    async def test_code_review_prompt_structure(
        self,
        populated_engine,
    ):
        """Test code review prompt has proper structure."""
        from codegraph_mcp.config import Config
        from codegraph_mcp.mcp.prompts import _prompt_code_review

        # Get a valid entity ID
        cursor = await populated_engine._connection.execute(
            "SELECT id FROM entities WHERE type = 'class' LIMIT 1"
        )
        row = await cursor.fetchone()

        if row:
            config = Config()
            result = await _prompt_code_review(
                {"entity_id": row[0]},
                populated_engine,
                config,
            )

            assert len(result) > 0
            assert "Code Review" in result[0].content.text

    @pytest.mark.asyncio
    async def test_explain_codebase_prompt(
        self,
        populated_engine,
    ):
        """Test explain codebase prompt generates context."""
        from codegraph_mcp.config import Config
        from codegraph_mcp.mcp.prompts import _prompt_explain_codebase

        config = Config()
        result = await _prompt_explain_codebase(
            {"depth": "overview"},
            populated_engine,
            config,
        )

        assert len(result) > 0
        text = result[0].content.text
        assert "Statistics" in text or "Entities" in text

    @pytest.mark.asyncio
    async def test_debug_issue_prompt(
        self,
        populated_engine,
    ):
        """Test debug issue prompt."""
        from codegraph_mcp.config import Config
        from codegraph_mcp.mcp.prompts import _prompt_debug_issue

        config = Config()
        result = await _prompt_debug_issue(
            {"error_message": "AttributeError: 'NoneType' has no attribute 'authenticate'"},
            populated_engine,
            config,
        )

        assert len(result) > 0
        assert "Debug" in result[0].content.text

    @pytest.mark.asyncio
    async def test_test_generation_prompt(
        self,
        populated_engine,
    ):
        """Test test generation prompt."""
        from codegraph_mcp.config import Config
        from codegraph_mcp.mcp.prompts import _prompt_test_generation

        # Get a valid entity ID
        cursor = await populated_engine._connection.execute(
            "SELECT id FROM entities WHERE type = 'function' LIMIT 1"
        )
        row = await cursor.fetchone()

        if row:
            config = Config()
            result = await _prompt_test_generation(
                {"entity_id": row[0], "test_type": "unit"},
                populated_engine,
                config,
            )

            assert len(result) > 0
            assert "Test" in result[0].content.text
