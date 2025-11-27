"""
Semantic Analysis Module

LLM-based semantic analysis for code understanding.

Requirements: REQ-SEM-001, REQ-SEM-002
Design Reference: design-core-engine.md §2.3
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from codegraph_mcp.core.community import Community
    from codegraph_mcp.core.parser import Entity


@dataclass
class SemanticDescription:
    """Semantic description of a code entity."""

    entity_id: str
    description: str
    keywords: list[str]
    complexity: str  # "low", "medium", "high"
    purpose: str


class SemanticAnalyzer:
    """
    Semantic analyzer for code understanding.

    Uses embeddings for similarity search and optionally LLMs
    for natural language descriptions.

    Requirements: REQ-SEM-001, REQ-SEM-002
    Design Reference: design-core-engine.md §2.3

    Usage:
        analyzer = SemanticAnalyzer()
        desc = await analyzer.generate_description(entity)
    """

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_enabled: bool = False,
    ) -> None:
        """
        Initialize the semantic analyzer.

        Args:
            embedding_model: Model for generating embeddings
            llm_enabled: Whether to use LLM for descriptions
        """
        self.embedding_model = embedding_model
        self.llm_enabled = llm_enabled
        self._model: Any = None

    def _ensure_initialized(self) -> None:
        """Lazily initialize the embedding model."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.embedding_model)
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Requirements: REQ-SEM-001
        """
        self._ensure_initialized()
        embedding = self._model.encode(text)
        return embedding.tolist()

    def generate_entity_embedding(self, entity: Entity) -> list[float]:
        """
        Generate embedding for a code entity.

        Combines name, signature, docstring, and source code.

        Args:
            entity: Code entity

        Returns:
            Embedding vector
        """
        parts = [entity.name, entity.qualified_name]

        if entity.signature:
            parts.append(entity.signature)

        if entity.docstring:
            parts.append(entity.docstring)

        if entity.source_code:
            # Truncate source code to reasonable length
            parts.append(entity.source_code[:500])

        text = " ".join(parts)
        return self.generate_embedding(text)

    async def generate_description(self, entity: Entity) -> SemanticDescription:
        """
        Generate natural language description for an entity.

        Args:
            entity: Code entity

        Returns:
            SemanticDescription with natural language description

        Requirements: REQ-SEM-002
        """
        if self.llm_enabled:
            return await self._generate_llm_description(entity)
        else:
            return self._generate_rule_based_description(entity)

    def _generate_rule_based_description(
        self,
        entity: Entity,
    ) -> SemanticDescription:
        """Generate description using rule-based approach."""
        # Extract keywords from name
        keywords = self._extract_keywords(entity.name)

        # Determine complexity based on source code length
        if entity.source_code:
            lines = entity.source_code.count("\n") + 1
            if lines < 10:
                complexity = "low"
            elif lines < 50:
                complexity = "medium"
            else:
                complexity = "high"
        else:
            complexity = "unknown"

        # Generate description
        type_name = entity.type.value.capitalize()
        description = f"{type_name} '{entity.name}'"

        if entity.docstring:
            # Use first line of docstring
            first_line = entity.docstring.split("\n")[0].strip()
            description = f"{description}: {first_line}"

        # Infer purpose from name patterns
        purpose = self._infer_purpose(entity.name)

        return SemanticDescription(
            entity_id=entity.id,
            description=description,
            keywords=keywords,
            complexity=complexity,
            purpose=purpose,
        )

    async def _generate_llm_description(
        self,
        entity: Entity,
    ) -> SemanticDescription:
        """Generate description using LLM."""
        from codegraph_mcp.core.llm import LLMClient

        client = LLMClient(fallback_to_rules=True)
        description = await client.generate_entity_description(entity)

        keywords = self._extract_keywords(entity.name)
        complexity = "medium"
        if entity.source_code:
            lines = entity.source_code.count("\n") + 1
            if lines < 10:
                complexity = "low"
            elif lines > 50:
                complexity = "high"

        purpose = self._infer_purpose(entity.name)

        return SemanticDescription(
            entity_id=entity.id,
            description=description,
            keywords=keywords,
            complexity=complexity,
            purpose=purpose,
        )

    async def generate_community_summary(
        self,
        community: Community,
        entities: list[Entity],
    ) -> str:
        """
        Generate summary for a community of related entities.

        Args:
            community: Community to summarize
            entities: Entities in the community

        Returns:
            Natural language summary

        Requirements: REQ-SEM-004
        """
        if not entities:
            return "Empty community"

        # Try LLM-based summary if enabled
        if self.llm_enabled:
            from codegraph_mcp.core.llm import LLMClient

            client = LLMClient(fallback_to_rules=True)
            try:
                return await client.generate_community_summary(community, entities)
            except Exception:
                pass  # Fall back to rule-based

        # Collect entity names and types
        type_counts: dict[str, int] = {}
        names: list[str] = []

        for entity in entities:
            type_name = entity.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
            names.append(entity.name)

        # Build summary
        parts = []
        for type_name, count in sorted(
            type_counts.items(),
            key=lambda x: -x[1],
        ):
            parts.append(f"{count} {type_name}(s)")

        summary = f"Community with {', '.join(parts)}."

        # Add key entities
        if names:
            key_names = names[:5]
            summary += f" Key entities: {', '.join(key_names)}"
            if len(names) > 5:
                summary += f" and {len(names) - 5} more."

        return summary

    def _extract_keywords(self, name: str) -> list[str]:
        """Extract keywords from a name using common patterns."""
        import re

        # Split camelCase and snake_case
        words = re.split(r"[_\s]|(?<=[a-z])(?=[A-Z])", name)

        # Filter and lowercase
        keywords = [
            w.lower() for w in words
            if w and len(w) > 2
        ]

        return keywords

    def _infer_purpose(self, name: str) -> str:
        """Infer purpose from naming patterns."""
        name_lower = name.lower()

        patterns = {
            "initialization": ["init", "__init__", "setup", "configure"],
            "data retrieval": ["get", "fetch", "load", "read", "find"],
            "data mutation": ["set", "update", "write", "save", "store"],
            "validation": ["validate", "check", "verify", "is_", "has_"],
            "transformation": ["convert", "transform", "parse", "format"],
            "computation": ["calculate", "compute", "process"],
            "event handling": ["on_", "handle", "listener"],
            "testing": ["test_", "_test", "spec"],
        }

        for purpose, keywords in patterns.items():
            if any(kw in name_lower for kw in keywords):
                return purpose

        return "general"
