"""
Unit tests for LLM integration module.

Tests: TASK-036, TASK-037, TASK-038
Requirements: REQ-SEM-001, REQ-SEM-002
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from codegraph_mcp.core.llm import (
    LLMClient,
    LLMConfig,
    LLMResponse,
    RuleBasedProvider,
)
from codegraph_mcp.core.parser import Entity, EntityType, Location


class TestLLMConfig:
    """Tests for LLM configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LLMConfig()
        assert config.provider == "openai"
        assert config.model == "gpt-4o-mini"
        assert config.max_tokens == 1024
        assert config.temperature == 0.3

    def test_from_env_openai(self):
        """Test config from environment (OpenAI)."""
        with patch.dict(
            "os.environ",
            {
                "CODEGRAPH_LLM_PROVIDER": "openai",
                "OPENAI_API_KEY": "test-key",
                "OPENAI_MODEL": "gpt-4",
            },
        ):
            config = LLMConfig.from_env()
            assert config.provider == "openai"
            assert config.api_key == "test-key"
            assert config.model == "gpt-4"

    def test_from_env_anthropic(self):
        """Test config from environment (Anthropic)."""
        with patch.dict(
            "os.environ",
            {
                "CODEGRAPH_LLM_PROVIDER": "anthropic",
                "ANTHROPIC_API_KEY": "test-key",
            },
        ):
            config = LLMConfig.from_env()
            assert config.provider == "anthropic"
            assert config.api_key == "test-key"

    def test_from_env_local(self):
        """Test config from environment (Local)."""
        with patch.dict(
            "os.environ",
            {
                "CODEGRAPH_LLM_PROVIDER": "local",
                "LOCAL_MODEL": "llama3",
                "LOCAL_LLM_URL": "http://localhost:11434",
            },
        ):
            config = LLMConfig.from_env()
            assert config.provider == "local"
            assert config.model == "llama3"


class TestRuleBasedProvider:
    """Tests for rule-based fallback provider."""

    @pytest.mark.asyncio
    async def test_complete(self):
        """Test rule-based completion."""
        config = LLMConfig()
        provider = RuleBasedProvider(config)

        response = await provider.complete([
            {"role": "user", "content": "Describe this function"}
        ])

        assert isinstance(response, LLMResponse)
        assert response.model == "rule-based"
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_complete_stream(self):
        """Test streaming completion."""
        config = LLMConfig()
        provider = RuleBasedProvider(config)

        chunks = []
        async for chunk in provider.complete_stream([
            {"role": "user", "content": "test"}
        ]):
            chunks.append(chunk)

        assert len(chunks) == 1


class TestLLMClient:
    """Tests for LLM client."""

    def test_fallback_to_rules(self):
        """Test fallback to rule-based when no API key."""
        client = LLMClient(fallback_to_rules=True)
        provider = client._get_provider()
        assert isinstance(provider, RuleBasedProvider)

    @pytest.mark.asyncio
    async def test_complete_with_fallback(self):
        """Test completion with rule-based fallback."""
        client = LLMClient(fallback_to_rules=True)

        result = await client.complete("What is this code?")
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_entity_description(self):
        """Test entity description generation."""
        client = LLMClient(fallback_to_rules=True)

        location = Location(
            file_path=Path("src/module.py"),
            start_line=1,
            start_column=0,
            end_line=10,
            end_column=0,
        )
        entity = Entity(
            id="test_func",
            type=EntityType.FUNCTION,
            name="calculate_total",
            qualified_name="module.calculate_total",
            location=location,
            signature="def calculate_total(items: list) -> float",
            docstring="Calculate the total price of items.",
            source_code="def calculate_total(items): return sum(items)",
        )

        description = await client.generate_entity_description(entity)
        assert len(description) > 0

    @pytest.mark.asyncio
    async def test_generate_community_summary(self):
        """Test community summary generation."""
        from codegraph_mcp.core.community import Community

        client = LLMClient(fallback_to_rules=True)

        community = Community(
            id=1,
            level=0,
            name="Data Processing",
            member_ids=["func1", "func2", "class1"],
        )

        location = Location(
            file_path=Path("src/module.py"),
            start_line=1,
            start_column=0,
            end_line=10,
            end_column=0,
        )
        entities = [
            Entity(
                id="func1",
                type=EntityType.FUNCTION,
                name="process_data",
                qualified_name="module.process_data",
                location=location,
            ),
            Entity(
                id="class1",
                type=EntityType.CLASS,
                name="DataProcessor",
                qualified_name="module.DataProcessor",
                location=location,
            ),
        ]

        summary = await client.generate_community_summary(community, entities)
        assert len(summary) > 0

    @pytest.mark.asyncio
    async def test_answer_code_question(self):
        """Test code question answering."""
        client = LLMClient(fallback_to_rules=True)

        location = Location(
            file_path=Path("src/auth.py"),
            start_line=1,
            start_column=0,
            end_line=10,
            end_column=0,
        )
        entity = Entity(
            id="auth_func",
            type=EntityType.FUNCTION,
            name="authenticate",
            qualified_name="auth.authenticate",
            location=location,
            docstring="Authenticate a user with credentials.",
        )

        answer = await client.answer_code_question(
            "How does authentication work?",
            [entity],
        )
        assert len(answer) > 0
