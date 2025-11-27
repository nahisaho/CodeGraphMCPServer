"""
GraphRAG Search Module

Implements global and local search using graph-based retrieval augmented generation.

Requirements: REQ-TLS-010, REQ-TLS-011
Design Reference: design-mcp-interface.md §2.1
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from codegraph_mcp.core.graph import GraphEngine
    from codegraph_mcp.core.parser import Entity


@dataclass
class SearchResult:
    """Search result with relevance information."""

    entity_id: str
    name: str
    entity_type: str
    file_path: str | None
    relevance_score: float
    context: str
    community_id: int | None = None
    community_summary: str | None = None


@dataclass
class GlobalSearchResult:
    """Result of global search across communities."""

    query: str
    answer: str
    communities_searched: int
    relevant_communities: list[dict[str, Any]]
    supporting_entities: list[SearchResult]
    confidence: float


@dataclass
class LocalSearchResult:
    """Result of local search within entity neighborhood."""

    query: str
    answer: str
    start_entity: str
    entities_searched: int
    relevant_entities: list[SearchResult]
    relationships: list[dict[str, Any]]
    confidence: float


class GraphRAGSearch:
    """
    GraphRAG-based search implementation.

    Provides global search (across communities) and local search
    (within entity neighborhood) capabilities.

    Requirements: REQ-TLS-010, REQ-TLS-011
    Design Reference: design-mcp-interface.md §2.1

    Usage:
        search = GraphRAGSearch(engine)
        result = await search.global_search("authentication flow")
        result = await search.local_search("UserService", "login process")
    """

    def __init__(
        self,
        engine: GraphEngine,
        use_llm: bool = True,
        max_communities: int = 5,
        max_entities: int = 20,
    ) -> None:
        """
        Initialize GraphRAG search.

        Args:
            engine: Graph engine instance
            use_llm: Whether to use LLM for answer synthesis
            max_communities: Max communities to search in global mode
            max_entities: Max entities to return
        """
        self.engine = engine
        self.use_llm = use_llm
        self.max_communities = max_communities
        self.max_entities = max_entities

    async def global_search(
        self,
        query: str,
        community_level: int = 0,
    ) -> GlobalSearchResult:
        """
        Global search across all communities.

        Uses community summaries to find relevant code regions,
        then retrieves specific entities.

        Args:
            query: Natural language search query
            community_level: Community hierarchy level (0=fine, 1=coarse)

        Returns:
            GlobalSearchResult with answer and supporting evidence

        Requirements: REQ-TLS-010
        """
        # Get community summaries
        communities = await self._get_communities_with_summaries(community_level)

        # Find relevant communities using keyword matching or embeddings
        relevant_communities = await self._find_relevant_communities(
            query, communities
        )

        # Get entities from relevant communities
        supporting_entities: list[SearchResult] = []
        for comm in relevant_communities[: self.max_communities]:
            entities = await self._get_community_entities(
                comm["id"], limit=self.max_entities // self.max_communities
            )
            for entity in entities:
                supporting_entities.append(
                    SearchResult(
                        entity_id=entity.id,
                        name=entity.name,
                        entity_type=entity.type.value,
                        file_path=str(entity.file_path),
                        relevance_score=comm.get("score", 0.5),
                        context=entity.docstring or entity.signature or "",
                        community_id=comm["id"],
                        community_summary=comm.get("summary"),
                    )
                )

        # Generate answer using LLM or rule-based
        answer = await self._generate_global_answer(
            query, relevant_communities, supporting_entities
        )

        return GlobalSearchResult(
            query=query,
            answer=answer,
            communities_searched=len(communities),
            relevant_communities=relevant_communities,
            supporting_entities=supporting_entities[: self.max_entities],
            confidence=self._calculate_confidence(relevant_communities),
        )

    async def local_search(
        self,
        query: str,
        entity_id: str,
        depth: int = 2,
    ) -> LocalSearchResult:
        """
        Local search within entity neighborhood.

        Explores the graph around a starting entity to find
        relevant information.

        Args:
            query: Natural language search query
            entity_id: Starting entity ID
            depth: Search depth in the graph

        Returns:
            LocalSearchResult with answer and related entities

        Requirements: REQ-TLS-011
        """
        # Get the starting entity
        start_entity = await self.engine.get_entity(entity_id)
        if not start_entity:
            return LocalSearchResult(
                query=query,
                answer=f"Entity '{entity_id}' not found.",
                start_entity=entity_id,
                entities_searched=0,
                relevant_entities=[],
                relationships=[],
                confidence=0.0,
            )

        # Get neighborhood entities
        neighbors = await self._get_entity_neighborhood(entity_id, depth)

        # Find relevant entities in neighborhood
        relevant_entities = await self._find_relevant_entities(query, neighbors)

        # Get relationships between entities
        relationships = await self._get_relationships(
            [e.entity_id for e in relevant_entities]
        )

        # Generate answer
        answer = await self._generate_local_answer(
            query, start_entity, relevant_entities, relationships
        )

        return LocalSearchResult(
            query=query,
            answer=answer,
            start_entity=start_entity.name,
            entities_searched=len(neighbors),
            relevant_entities=relevant_entities,
            relationships=relationships,
            confidence=self._calculate_local_confidence(relevant_entities),
        )

    async def _get_communities_with_summaries(
        self,
        level: int,
    ) -> list[dict[str, Any]]:
        """Get all communities with their summaries."""
        cursor = await self.engine._connection.execute(
            """
            SELECT id, level, name, summary, member_count
            FROM communities
            WHERE level = ? OR ? < 0
            ORDER BY member_count DESC
            """,
            (level, level),
        )
        rows = await cursor.fetchall()

        return [
            {
                "id": row[0],
                "level": row[1],
                "name": row[2],
                "summary": row[3],
                "member_count": row[4],
            }
            for row in rows
        ]

    async def _find_relevant_communities(
        self,
        query: str,
        communities: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Find communities relevant to the query."""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored = []
        for comm in communities:
            score = 0.0

            # Match against name
            if comm.get("name"):
                name_lower = comm["name"].lower()
                if any(word in name_lower for word in query_words):
                    score += 0.5

            # Match against summary
            if comm.get("summary"):
                summary_lower = comm["summary"].lower()
                matching_words = sum(
                    1 for word in query_words if word in summary_lower
                )
                score += matching_words * 0.2

            if score > 0:
                comm["score"] = min(score, 1.0)
                scored.append(comm)

        # Sort by score
        scored.sort(key=lambda x: -x.get("score", 0))

        # If no matches, return top communities by size
        if not scored and communities:
            for comm in communities[: self.max_communities]:
                comm["score"] = 0.3
                scored.append(comm)

        return scored[: self.max_communities]

    async def _get_community_entities(
        self,
        community_id: int,
        limit: int = 10,
    ) -> list[Entity]:
        """Get entities in a community."""
        from pathlib import Path

        from codegraph_mcp.core.parser import Entity, EntityType, Location

        cursor = await self.engine._connection.execute(
            """
            SELECT id, type, name, qualified_name, file_path,
                   start_line, end_line, signature, docstring, source_code
            FROM entities
            WHERE community_id = ?
            ORDER BY
                CASE type
                    WHEN 'class' THEN 1
                    WHEN 'function' THEN 2
                    WHEN 'method' THEN 3
                    ELSE 4
                END
            LIMIT ?
            """,
            (community_id, limit),
        )
        rows = await cursor.fetchall()

        entities = []
        for row in rows:
            location = Location(
                file_path=Path(row[4]) if row[4] else Path(),
                start_line=row[5] or 0,
                start_column=0,
                end_line=row[6] or 0,
                end_column=0,
            )
            entity = Entity(
                id=row[0],
                type=EntityType(row[1]),
                name=row[2],
                qualified_name=row[3],
                location=location,
                signature=row[7],
                docstring=row[8],
                source_code=row[9],
            )
            entities.append(entity)

        return entities

    async def _get_entity_neighborhood(
        self,
        entity_id: str,
        depth: int,
    ) -> list[Entity]:
        """Get entities in the neighborhood of a given entity."""
        from pathlib import Path

        from codegraph_mcp.core.parser import Entity, EntityType, Location

        # Get directly connected entities
        cursor = await self.engine._connection.execute(
            """
            SELECT DISTINCT e.id, e.type, e.name, e.qualified_name,
                   e.file_path, e.start_line, e.end_line,
                   e.signature, e.docstring, e.source_code
            FROM entities e
            WHERE e.id IN (
                SELECT target_id FROM relations WHERE source_id = ?
                UNION
                SELECT source_id FROM relations WHERE target_id = ?
            )
            LIMIT ?
            """,
            (entity_id, entity_id, self.max_entities * depth),
        )
        rows = await cursor.fetchall()

        entities = []
        for row in rows:
            location = Location(
                file_path=Path(row[4]) if row[4] else Path(),
                start_line=row[5] or 0,
                start_column=0,
                end_line=row[6] or 0,
                end_column=0,
            )
            entity = Entity(
                id=row[0],
                type=EntityType(row[1]),
                name=row[2],
                qualified_name=row[3],
                location=location,
                signature=row[7],
                docstring=row[8],
                source_code=row[9],
            )
            entities.append(entity)

        return entities

    async def _find_relevant_entities(
        self,
        query: str,
        entities: list[Entity],
    ) -> list[SearchResult]:
        """Find entities relevant to the query."""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        results = []
        for entity in entities:
            score = 0.0

            # Match name
            if any(word in entity.name.lower() for word in query_words):
                score += 0.4

            # Match docstring
            doc = entity.docstring or ""
            if doc and any(word in doc.lower() for word in query_words):
                score += 0.3

            # Match signature
            sig = entity.signature or ""
            if sig and any(word in sig.lower() for word in query_words):
                score += 0.2

            # Match source code
            src = entity.source_code or ""
            if src and any(word in src.lower() for word in query_words):
                score += 0.1

            if score > 0:
                results.append(
                    SearchResult(
                        entity_id=entity.id,
                        name=entity.name,
                        entity_type=entity.type.value,
                        file_path=str(entity.file_path),
                        relevance_score=min(score, 1.0),
                        context=entity.docstring or entity.signature or "",
                    )
                )

        # Sort by relevance
        results.sort(key=lambda x: -x.relevance_score)

        # If no matches, include some entities anyway
        if not results and entities:
            for entity in entities[: self.max_entities]:
                results.append(
                    SearchResult(
                        entity_id=entity.id,
                        name=entity.name,
                        entity_type=entity.type.value,
                        file_path=str(entity.file_path),
                        relevance_score=0.2,
                        context=entity.docstring or entity.signature or "",
                    )
                )

        return results[: self.max_entities]

    async def _get_relationships(
        self,
        entity_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Get relationships between entities."""
        if not entity_ids:
            return []

        placeholders = ",".join("?" * len(entity_ids))
        cursor = await self.engine._connection.execute(
            f"""
            SELECT r.source_id, r.target_id, r.type,
                   e1.name as source_name, e2.name as target_name
            FROM relations r
            JOIN entities e1 ON r.source_id = e1.id
            JOIN entities e2 ON r.target_id = e2.id
            WHERE r.source_id IN ({placeholders})
               OR r.target_id IN ({placeholders})
            LIMIT 50
            """,
            entity_ids + entity_ids,
        )
        rows = await cursor.fetchall()

        return [
            {
                "source_id": row[0],
                "target_id": row[1],
                "type": row[2],
                "source_name": row[3],
                "target_name": row[4],
            }
            for row in rows
        ]

    async def _generate_global_answer(
        self,
        query: str,
        communities: list[dict[str, Any]],
        entities: list[SearchResult],
    ) -> str:
        """Generate answer for global search."""
        if self.use_llm:
            try:
                from codegraph_mcp.core.llm import LLMClient

                client = LLMClient(fallback_to_rules=True)

                context_parts = []
                for comm in communities[:3]:
                    if comm.get("summary"):
                        context_parts.append(
                            f"Module: {comm.get('name', 'Unknown')}\n"
                            f"Summary: {comm['summary']}"
                        )

                for entity in entities[:5]:
                    context_parts.append(
                        f"Entity: {entity.name} ({entity.entity_type})\n"
                        f"Context: {entity.context[:200]}"
                    )

                context = "\n\n".join(context_parts)

                system = """You are a code expert. Answer the question based on
the provided code context. Be specific and reference relevant entities."""

                prompt = f"""Question: {query}

Code Context:
{context}

Provide a concise answer based on the code structure and documentation."""

                return await client.complete(prompt, system=system)

            except Exception:
                pass

        # Fallback: rule-based answer
        if communities:
            comm_names = [
                c.get("name") or f"Community {c['id']}"
                for c in communities
            ]
            entity_names = [e.name for e in entities[:5]]

            return (
                f"Based on the codebase structure, '{query}' is related to "
                f"modules: {', '.join(comm_names)}. "
                f"Key entities: {', '.join(entity_names)}."
            )

        return f"No relevant information found for: {query}"

    async def _generate_local_answer(
        self,
        query: str,
        start_entity: Entity,
        entities: list[SearchResult],
        relationships: list[dict[str, Any]],
    ) -> str:
        """Generate answer for local search."""
        if self.use_llm:
            try:
                from codegraph_mcp.core.llm import LLMClient

                client = LLMClient(fallback_to_rules=True)

                context_parts = [
                    f"Starting entity: {start_entity.name} ({start_entity.type.value})",
                    f"File: {start_entity.file_path}",
                ]

                if start_entity.docstring:
                    context_parts.append(f"Documentation: {start_entity.docstring}")

                context_parts.append("\nRelated entities:")
                for entity in entities[:5]:
                    context_parts.append(f"- {entity.name} ({entity.entity_type})")

                context_parts.append("\nRelationships:")
                for rel in relationships[:10]:
                    context_parts.append(
                        f"- {rel['source_name']} --{rel['type']}--> {rel['target_name']}"
                    )

                context = "\n".join(context_parts)

                system = """You are a code expert. Answer the question based on
the local code context around the given entity."""

                prompt = f"""Question: {query}

Context around '{start_entity.name}':
{context}

Provide a focused answer about this part of the codebase."""

                return await client.complete(prompt, system=system)

            except Exception:
                pass

        # Fallback: rule-based answer
        entity_names = [e.name for e in entities[:5]]
        rel_summary = (
            f"{len(relationships)} relationships" if relationships else "no relationships"
        )

        return (
            f"'{start_entity.name}' is connected to: {', '.join(entity_names)}. "
            f"Found {rel_summary} in the local neighborhood."
        )

    def _calculate_confidence(
        self,
        communities: list[dict[str, Any]],
    ) -> float:
        """Calculate confidence score for global search."""
        if not communities:
            return 0.0

        avg_score = sum(c.get("score", 0) for c in communities) / len(communities)
        return min(avg_score + 0.2, 1.0)

    def _calculate_local_confidence(
        self,
        entities: list[SearchResult],
    ) -> float:
        """Calculate confidence score for local search."""
        if not entities:
            return 0.0

        avg_score = sum(e.relevance_score for e in entities) / len(entities)
        return min(avg_score + 0.3, 1.0)
