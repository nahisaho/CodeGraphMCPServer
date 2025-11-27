"""
LLM Integration Module

Provides LLM-based code analysis and summary generation.

Requirements: REQ-SEM-001, REQ-SEM-002
Design Reference: design-core-engine.md §2.3
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from codegraph_mcp.core.community import Community
    from codegraph_mcp.core.parser import Entity


@dataclass
class LLMConfig:
    """LLM configuration."""

    provider: str = "openai"  # openai, anthropic, local
    model: str = "gpt-4o-mini"
    api_key: str = ""
    base_url: str | None = None
    max_tokens: int = 1024
    temperature: float = 0.3
    timeout: float = 60.0

    @classmethod
    def from_env(cls) -> LLMConfig:
        """Create config from environment variables."""
        provider = os.getenv("CODEGRAPH_LLM_PROVIDER", "openai")

        if provider == "openai":
            return cls(
                provider="openai",
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                api_key=os.getenv("OPENAI_API_KEY", ""),
                base_url=os.getenv("OPENAI_BASE_URL"),
            )
        elif provider == "anthropic":
            return cls(
                provider="anthropic",
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
                api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            )
        elif provider == "local":
            return cls(
                provider="local",
                model=os.getenv("LOCAL_MODEL", "llama3"),
                base_url=os.getenv("LOCAL_LLM_URL", "http://localhost:11434"),
            )

        return cls(provider=provider)


@dataclass
class LLMResponse:
    """LLM response."""

    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    raw: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract LLM provider."""

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion."""
        pass

    @abstractmethod
    async def complete_stream(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate streaming completion."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy initialize OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                )
            except ImportError:
                raise ImportError(
                    "openai package not installed. "
                    "Install with: pip install openai"
                )
        return self._client

    async def complete(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion via OpenAI API."""
        client = self._get_client()

        response = await client.chat.completions.create(
            model=kwargs.get("model", self.config.model),
            messages=messages,
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            temperature=kwargs.get("temperature", self.config.temperature),
        )

        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            finish_reason=choice.finish_reason or "stop",
            raw=response.model_dump(),
        )

    async def complete_stream(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate streaming completion."""
        client = self._get_client()

        stream = await client.chat.completions.create(
            model=kwargs.get("model", self.config.model),
            messages=messages,
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            temperature=kwargs.get("temperature", self.config.temperature),
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicProvider(LLMProvider):
    """Anthropic API provider."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy initialize Anthropic client."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.config.api_key)
            except ImportError:
                raise ImportError(
                    "anthropic package not installed. "
                    "Install with: pip install anthropic"
                )
        return self._client

    async def complete(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion via Anthropic API."""
        client = self._get_client()

        # Convert messages format
        system = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                user_messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        response = await client.messages.create(
            model=kwargs.get("model", self.config.model),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            system=system,
            messages=user_messages,
        )

        return LLMResponse(
            content=response.content[0].text if response.content else "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            finish_reason=response.stop_reason or "stop",
            raw={"id": response.id, "model": response.model},
        )

    async def complete_stream(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate streaming completion."""
        client = self._get_client()

        system = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                user_messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        async with client.messages.stream(
            model=kwargs.get("model", self.config.model),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            system=system,
            messages=user_messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text


class LocalProvider(LLMProvider):
    """Local LLM provider (Ollama compatible)."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self.base_url = config.base_url or "http://localhost:11434"

    async def complete(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion via local API."""
        import aiohttp

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": kwargs.get("model", self.config.model),
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                data = await response.json()

        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=data.get("model", self.config.model),
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
            finish_reason="stop",
            raw=data,
        )

    async def complete_stream(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate streaming completion."""
        import aiohttp

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": kwargs.get("model", self.config.model),
            "messages": messages,
            "stream": True,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                async for line in response.content:
                    if line:
                        data = json.loads(line.decode())
                        if "message" in data:
                            yield data["message"].get("content", "")


class RuleBasedProvider(LLMProvider):
    """Rule-based fallback provider (no API required)."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    async def complete(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate rule-based response."""
        # Extract user message
        user_msg = ""
        for msg in messages:
            if msg["role"] == "user":
                user_msg = msg["content"]
                break

        # Generate simple response based on patterns
        content = self._generate_rule_based(user_msg)

        return LLMResponse(
            content=content,
            model="rule-based",
            usage={},
            finish_reason="stop",
        )

    async def complete_stream(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate streaming response."""
        response = await self.complete(messages, **kwargs)
        yield response.content

    def _generate_rule_based(self, prompt: str) -> str:
        """Generate response using rules."""
        # Default summary template
        return "This code module provides functionality as indicated by its structure."


class LLMClient:
    """
    High-level LLM client for code analysis.

    Requirements: REQ-SEM-001, REQ-SEM-002

    Usage:
        client = LLMClient()
        desc = await client.generate_entity_description(entity)
        summary = await client.generate_community_summary(community, entities)
    """

    def __init__(
        self,
        config: LLMConfig | None = None,
        fallback_to_rules: bool = True,
    ) -> None:
        """
        Initialize LLM client.

        Args:
            config: LLM configuration (or loads from env)
            fallback_to_rules: Use rule-based when API unavailable
        """
        self.config = config or LLMConfig.from_env()
        self.fallback_to_rules = fallback_to_rules
        self._provider: LLMProvider | None = None

    def _get_provider(self) -> LLMProvider:
        """Get or create LLM provider."""
        if self._provider is not None:
            return self._provider

        if not self.config.api_key and self.config.provider != "local":
            if self.fallback_to_rules:
                self._provider = RuleBasedProvider(self.config)
                return self._provider
            raise ValueError(f"API key not configured for {self.config.provider}")

        providers = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "local": LocalProvider,
        }

        provider_class = providers.get(self.config.provider)
        if not provider_class:
            if self.fallback_to_rules:
                self._provider = RuleBasedProvider(self.config)
                return self._provider
            raise ValueError(f"Unknown provider: {self.config.provider}")

        try:
            self._provider = provider_class(self.config)
        except ImportError:
            if self.fallback_to_rules:
                self._provider = RuleBasedProvider(self.config)
            else:
                raise

        return self._provider

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate completion.

        Args:
            prompt: User prompt
            system: System prompt
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        provider = self._get_provider()
        response = await provider.complete(messages, **kwargs)
        return response.content

    async def generate_entity_description(
        self,
        entity: Entity,
    ) -> str:
        """
        Generate natural language description for a code entity.

        Args:
            entity: Code entity to describe

        Returns:
            Description text

        Requirements: REQ-SEM-001
        """
        system = """You are a code documentation expert. Generate a clear, concise
description of the given code entity. Focus on:
1. What the code does
2. Key parameters and return values
3. Usage patterns

Keep the description under 100 words."""

        prompt = f"""Describe this {entity.type.value}:

Name: {entity.name}
Qualified Name: {entity.qualified_name}
Signature: {entity.signature or 'N/A'}

Docstring:
{entity.docstring or 'No docstring'}

Source Code:
```
{entity.source_code[:1000] if entity.source_code else 'N/A'}
```"""

        return await self.complete(prompt, system=system)

    async def generate_community_summary(
        self,
        community: Community,
        entities: list[Entity],
    ) -> str:
        """
        Generate summary for a code community.

        Args:
            community: Community metadata
            entities: Entities in the community

        Returns:
            Summary text

        Requirements: REQ-SEM-002
        """
        # Collect entity info
        type_counts: dict[str, int] = {}
        entity_info: list[str] = []

        for entity in entities[:20]:  # Limit for token efficiency
            type_name = entity.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

            info = f"- {entity.name} ({type_name})"
            if entity.docstring:
                first_line = entity.docstring.split("\n")[0][:100]
                info += f": {first_line}"
            entity_info.append(info)

        system = """You are a software architecture expert. Analyze the given code
community and generate a summary that describes:
1. The main purpose/responsibility of this code module
2. Key components and their roles
3. How entities relate to each other

Keep the summary under 150 words."""

        prompt = f"""Summarize this code community:

Community ID: {community.id}
Level: {community.level}
Total Members: {community.member_count}

Entity Composition:
{json.dumps(type_counts, indent=2)}

Key Entities:
{chr(10).join(entity_info)}"""

        return await self.complete(prompt, system=system)

    async def generate_codebase_overview(
        self,
        communities: list[Community],
        stats: dict[str, Any],
    ) -> str:
        """
        Generate high-level codebase overview.

        Args:
            communities: Detected communities
            stats: Codebase statistics

        Returns:
            Overview text
        """
        system = """You are a software architecture expert. Generate a high-level
overview of the codebase based on its structure and communities. Focus on:
1. Overall architecture pattern
2. Main modules and their responsibilities
3. Key relationships and dependencies

Keep the overview under 200 words."""

        community_info = []
        for c in communities[:10]:  # Top communities
            community_info.append(
                f"- Community {c.id} (Level {c.level}): "
                f"{c.member_count} members - {c.summary or 'No summary'}"
            )

        prompt = f"""Generate a codebase overview:

Statistics:
{json.dumps(stats, indent=2)}

Top Communities:
{chr(10).join(community_info)}"""

        return await self.complete(prompt, system=system)

    async def answer_code_question(
        self,
        question: str,
        context: list[Entity],
    ) -> str:
        """
        Answer a question about the code using context.

        Args:
            question: User question
            context: Relevant code entities

        Returns:
            Answer text
        """
        system = """You are a code expert assistant. Answer the user's question
based on the provided code context. Be specific and reference the relevant
code entities when appropriate. If the context doesn't contain enough
information, say so."""

        context_text = []
        for entity in context[:10]:
            info = f"""
### {entity.name} ({entity.type.value})
File: {entity.file_path}:{entity.start_line}
```
{entity.source_code[:500] if entity.source_code else 'N/A'}
```
"""
            context_text.append(info)

        prompt = f"""Question: {question}

Code Context:
{chr(10).join(context_text)}"""

        return await self.complete(prompt, system=system)

