"""
Unit tests for GraphRAG search module.

Tests: TASK-042, TASK-043
Requirements: REQ-TLS-010, REQ-TLS-011
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from codegraph_mcp.core.graphrag import (
    GlobalSearchResult,
    GraphRAGSearch,
    LocalSearchResult,
    SearchResult,
)
from codegraph_mcp.core.parser import Entity, EntityType, Location


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_create_search_result(self):
        """Test creating a search result."""
        result = SearchResult(
            entity_id="func_1",
            name="process_data",
            entity_type="function",
            file_path="src/module.py",
            relevance_score=0.85,
            context="Process input data.",
        )

        assert result.entity_id == "func_1"
        assert result.name == "process_data"
        assert result.entity_type == "function"
        assert result.relevance_score == 0.85

    def test_search_result_with_community(self):
        """Test search result with community info."""
        result = SearchResult(
            entity_id="class_1",
            name="DataHandler",
            entity_type="class",
            file_path="src/handler.py",
            relevance_score=0.9,
            context="Handles data processing.",
            community_id=5,
            community_summary="Data processing module",
        )

        assert result.community_id == 5
        assert result.community_summary == "Data processing module"


class TestGlobalSearchResult:
    """Tests for GlobalSearchResult dataclass."""

    def test_create_global_result(self):
        """Test creating a global search result."""
        result = GlobalSearchResult(
            query="authentication flow",
            answer="The authentication flow involves...",
            communities_searched=10,
            relevant_communities=[{"id": 1, "name": "Auth"}],
            supporting_entities=[],
            confidence=0.75,
        )

        assert result.query == "authentication flow"
        assert result.communities_searched == 10
        assert result.confidence == 0.75


class TestLocalSearchResult:
    """Tests for LocalSearchResult dataclass."""

    def test_create_local_result(self):
        """Test creating a local search result."""
        result = LocalSearchResult(
            query="how is this used",
            answer="This function is used by...",
            start_entity="process_data",
            entities_searched=15,
            relevant_entities=[],
            relationships=[],
            confidence=0.8,
        )

        assert result.start_entity == "process_data"
        assert result.entities_searched == 15


class TestGraphRAGSearch:
    """Tests for GraphRAGSearch class."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock graph engine."""
        engine = MagicMock()
        engine._connection = MagicMock()
        return engine

    def test_init(self, mock_engine):
        """Test GraphRAGSearch initialization."""
        search = GraphRAGSearch(
            mock_engine,
            use_llm=False,
            max_communities=10,
            max_entities=50,
        )

        assert search.engine == mock_engine
        assert search.use_llm is False
        assert search.max_communities == 10
        assert search.max_entities == 50

    @pytest.mark.asyncio
    async def test_global_search_no_communities(self, mock_engine):
        """Test global search with no communities."""
        # Mock empty communities
        cursor_mock = AsyncMock()
        cursor_mock.fetchall = AsyncMock(return_value=[])
        mock_engine._connection.execute = AsyncMock(return_value=cursor_mock)

        search = GraphRAGSearch(mock_engine, use_llm=False)
        result = await search.global_search("test query")

        assert isinstance(result, GlobalSearchResult)
        assert result.query == "test query"
        assert result.communities_searched == 0

    @pytest.mark.asyncio
    async def test_global_search_with_communities(self, mock_engine):
        """Test global search with communities."""
        # Mock for communities and entities queries
        call_count = [0]

        async def mock_fetchall():
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: _get_communities_with_summaries
                return [
                    (1, 0, "Auth Module", "Authentication and authorization", 10),
                    (2, 0, "Data Module", "Data processing utilities", 8),
                ]
            else:
                # Subsequent calls: _get_community_entities
                return []  # No entities for simplicity

        cursor_mock = AsyncMock()
        cursor_mock.fetchall = mock_fetchall
        mock_engine._connection.execute = AsyncMock(return_value=cursor_mock)

        search = GraphRAGSearch(mock_engine, use_llm=False)
        result = await search.global_search("authentication")

        assert isinstance(result, GlobalSearchResult)
        assert result.communities_searched == 2
        assert len(result.relevant_communities) > 0

    @pytest.mark.asyncio
    async def test_local_search_entity_not_found(self, mock_engine):
        """Test local search when entity not found."""
        mock_engine.get_entity = AsyncMock(return_value=None)

        search = GraphRAGSearch(mock_engine, use_llm=False)
        result = await search.local_search(
            "how is this used",
            "nonexistent_entity",
        )

        assert isinstance(result, LocalSearchResult)
        assert "not found" in result.answer
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_local_search_with_entity(self, mock_engine):
        """Test local search with valid entity."""
        # Mock entity with location
        location = Location(
            file_path=Path("src/module.py"),
            start_line=1,
            start_column=0,
            end_line=10,
            end_column=0,
        )
        mock_entity = Entity(
            id="func_1",
            type=EntityType.FUNCTION,
            name="process_data",
            qualified_name="module.process_data",
            location=location,
            docstring="Process input data.",
        )

        mock_engine.get_entity = AsyncMock(return_value=mock_entity)

        # Mock neighbors
        cursor_mock = AsyncMock()
        cursor_mock.fetchall = AsyncMock(return_value=[])
        mock_engine._connection.execute = AsyncMock(return_value=cursor_mock)

        search = GraphRAGSearch(mock_engine, use_llm=False)
        result = await search.local_search(
            "what does this do",
            "func_1",
        )

        assert isinstance(result, LocalSearchResult)
        assert result.start_entity == "process_data"

    @pytest.mark.asyncio
    async def test_find_relevant_communities(self, mock_engine):
        """Test finding relevant communities."""
        search = GraphRAGSearch(mock_engine, use_llm=False)

        communities = [
            {"id": 1, "name": "Auth", "summary": "User authentication"},
            {"id": 2, "name": "Data", "summary": "Data processing"},
            {"id": 3, "name": "Utils", "summary": "Utility functions"},
        ]

        relevant = await search._find_relevant_communities(
            "authentication",
            communities,
        )

        assert len(relevant) > 0
        assert relevant[0]["id"] == 1  # Auth should be most relevant

    @pytest.mark.asyncio
    async def test_find_relevant_entities(self, mock_engine):
        """Test finding relevant entities."""
        search = GraphRAGSearch(mock_engine, use_llm=False)

        location = Location(
            file_path=Path("src/module.py"),
            start_line=1,
            start_column=0,
            end_line=10,
            end_column=0,
        )
        entities = [
            Entity(
                id="auth_func",
                type=EntityType.FUNCTION,
                name="authenticate_user",
                qualified_name="auth.authenticate_user",
                location=location,
                docstring="Authenticate a user",
            ),
            Entity(
                id="data_func",
                type=EntityType.FUNCTION,
                name="process_data",
                qualified_name="data.process_data",
                location=location,
                docstring="Process data input",
            ),
        ]

        relevant = await search._find_relevant_entities(
            "authenticate",
            entities,
        )

        assert len(relevant) > 0
        assert relevant[0].entity_id == "auth_func"

    def test_calculate_confidence(self, mock_engine):
        """Test confidence calculation."""
        search = GraphRAGSearch(mock_engine, use_llm=False)

        # Empty communities
        assert search._calculate_confidence([]) == 0.0

        # Communities with scores
        communities = [
            {"score": 0.8},
            {"score": 0.6},
        ]
        confidence = search._calculate_confidence(communities)
        assert 0.8 <= confidence <= 1.0

    def test_calculate_local_confidence(self, mock_engine):
        """Test local confidence calculation."""
        search = GraphRAGSearch(mock_engine, use_llm=False)

        # Empty entities
        assert search._calculate_local_confidence([]) == 0.0

        # Entities with scores
        entities = [
            SearchResult(
                entity_id="e1",
                name="func1",
                entity_type="function",
                file_path=None,
                relevance_score=0.9,
                context="",
            ),
            SearchResult(
                entity_id="e2",
                name="func2",
                entity_type="function",
                file_path=None,
                relevance_score=0.7,
                context="",
            ),
        ]
        confidence = search._calculate_local_confidence(entities)
        assert 0.8 <= confidence <= 1.0
