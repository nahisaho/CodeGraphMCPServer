"""
Community Detection Module

Graph-based community detection for code clustering.

Requirements: REQ-SEM-003, REQ-SEM-004
Design Reference: design-core-engine.md §2.5
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Community:
    """
    Represents a code community (cluster of related entities).

    Requirements: REQ-SEM-003
    """

    id: int
    level: int
    name: str | None = None
    summary: str | None = None
    member_ids: list[str] = field(default_factory=list)
    parent_id: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def member_count(self) -> int:
        return len(self.member_ids)


@dataclass
class CommunityResult:
    """Result of community detection."""

    communities: list[Community] = field(default_factory=list)
    levels: int = 0
    modularity: float = 0.0


class CommunityDetector:
    """
    Community detection using Louvain algorithm.

    Requirements: REQ-SEM-003, REQ-SEM-004
    Design Reference: design-core-engine.md §2.5

    Usage:
        detector = CommunityDetector()
        result = detector.detect(graph_engine)
    """

    def __init__(
        self,
        algorithm: str = "louvain",
        resolution: float = 1.0,
        min_size: int = 3,
        max_nodes: int = 50000,  # Sample if larger
    ) -> None:
        """
        Initialize the community detector.

        Args:
            algorithm: Detection algorithm ("louvain" or "leiden")
            resolution: Resolution parameter for modularity
            min_size: Minimum community size
            max_nodes: Max nodes before sampling (for large graphs)
        """
        self.algorithm = algorithm
        self.resolution = resolution
        self.min_size = min_size
        self.max_nodes = max_nodes

    async def detect(self, engine: Any) -> CommunityResult:
        """
        Detect communities in the code graph.

        Args:
            engine: GraphEngine instance

        Returns:
            CommunityResult with detected communities

        Requirements: REQ-SEM-003
        """

        # Check graph size first
        cursor = await engine._connection.execute(
            "SELECT COUNT(*) FROM entities"
        )
        node_count = (await cursor.fetchone())[0]

        # Build NetworkX graph from entities and relations
        G = await self._build_networkx_graph(engine)

        if G.number_of_nodes() == 0:
            return CommunityResult()

        # Sample large graphs for performance
        if node_count > self.max_nodes:
            G = self._sample_graph(G, self.max_nodes)

        # Apply community detection
        if self.algorithm == "louvain":
            communities = self._detect_louvain(G)
        else:
            communities = self._detect_louvain(G)  # Fallback

        # Store communities in database
        await self._store_communities(engine, communities)

        return CommunityResult(
            communities=communities,
            levels=max((c.level for c in communities), default=0) + 1,
            modularity=self._compute_modularity(G, communities),
        )

    def _sample_graph(self, G: Any, max_nodes: int) -> Any:
        """Sample graph for large-scale community detection."""
        import random

        if G.number_of_nodes() <= max_nodes:
            return G

        # Sample nodes by degree (keep high-degree nodes)
        degrees = dict(G.degree())
        sorted_nodes = sorted(
            degrees.keys(),
            key=lambda x: degrees[x],
            reverse=True
        )

        # Keep top nodes by degree + random sample
        top_count = max_nodes // 2
        top_nodes = set(sorted_nodes[:top_count])

        remaining = list(sorted_nodes[top_count:])
        random.seed(42)
        random_sample = set(random.sample(
            remaining,
            min(max_nodes - top_count, len(remaining))
        ))

        sampled_nodes = top_nodes | random_sample
        return G.subgraph(sampled_nodes).copy()

    async def _build_networkx_graph(self, engine: Any) -> Any:
        """Build NetworkX graph from database (optimized for large graphs)."""
        import networkx as nx

        G = nx.DiGraph()

        # Batch fetch nodes - use fetchall() for speed
        cursor = await engine._connection.execute(
            "SELECT id, type, name FROM entities"
        )
        rows = await cursor.fetchall()

        # Add nodes in bulk
        G.add_nodes_from(
            (row[0], {"type": row[1], "name": row[2]})
            for row in rows
        )

        # Batch fetch edges
        cursor = await engine._connection.execute(
            "SELECT source_id, target_id, type, weight FROM relations"
        )
        rows = await cursor.fetchall()

        # Add edges in bulk
        G.add_edges_from(
            (row[0], row[1], {"type": row[2], "weight": row[3]})
            for row in rows
        )

        return G

    def _detect_louvain(self, G: Any) -> list[Community]:
        """Apply Louvain algorithm for community detection."""
        from networkx.algorithms.community import louvain_communities

        # Convert to undirected for Louvain
        G_undirected = G.to_undirected()

        # Detect communities
        partition = louvain_communities(
            G_undirected,
            resolution=self.resolution,
            seed=42,
        )

        communities = []
        for idx, members in enumerate(partition):
            if len(members) >= self.min_size:
                communities.append(Community(
                    id=idx,
                    level=0,
                    member_ids=list(members),
                ))

        return communities

    async def _store_communities(
        self,
        engine: Any,
        communities: list[Community],
    ) -> None:
        """Store communities in database (batch optimized)."""
        # Clear existing communities
        await engine._connection.execute("DELETE FROM communities")

        # Batch insert communities
        community_data = [
            (c.id, c.level, c.name, c.summary, c.member_count)
            for c in communities
        ]
        await engine._connection.executemany(
            """
            INSERT INTO communities (id, level, name, summary, member_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            community_data,
        )

        # Batch update entity community assignments
        # Build (community_id, entity_id) pairs
        assignments = []
        for community in communities:
            for member_id in community.member_ids:
                assignments.append((community.id, member_id))

        # Execute batch update
        await engine._connection.executemany(
            "UPDATE entities SET community_id = ? WHERE id = ?",
            assignments,
        )

        await engine._connection.commit()

    async def update_incremental(
        self,
        engine: Any,
        changed_entity_ids: list[str],
    ) -> CommunityResult:
        """
        Incrementally update communities for changed entities.

        This method reassigns changed entities to their best-fit existing
        communities based on their relationships. If significant changes
        are detected, it triggers a full re-detection.

        Args:
            engine: GraphEngine instance
            changed_entity_ids: List of entity IDs that changed

        Returns:
            CommunityResult with updated community assignments
        """
        if not changed_entity_ids:
            return CommunityResult()

        # Check if we have existing communities
        cursor = await engine._connection.execute(
            "SELECT COUNT(*) FROM communities"
        )
        community_count = (await cursor.fetchone())[0]

        # If no communities exist or many entities changed, do full detection
        cursor = await engine._connection.execute(
            "SELECT COUNT(*) FROM entities"
        )
        total_entities = (await cursor.fetchone())[0]

        # Threshold: if >20% of entities changed, do full re-detection
        change_ratio = len(changed_entity_ids) / max(total_entities, 1)
        if community_count == 0 or change_ratio > 0.2:
            return await self.detect(engine)

        # Incremental update: assign changed entities to best-fit communities
        await self._assign_to_best_communities(
            engine, changed_entity_ids
        )

        # Get updated statistics
        cursor = await engine._connection.execute(
            "SELECT COUNT(DISTINCT community_id) FROM entities "
            "WHERE community_id IS NOT NULL"
        )
        _ = (await cursor.fetchone())[0]  # active_communities

        return CommunityResult(
            communities=[],  # Not re-detecting all communities
            levels=1,
            modularity=0.0,  # Skip modularity computation for speed
        )

    async def _assign_to_best_communities(
        self,
        engine: Any,
        entity_ids: list[str],
    ) -> None:
        """Assign entities to their best-fit communities."""
        for entity_id in entity_ids:
            # Find most common community among connected entities
            cursor = await engine._connection.execute(
                """
                SELECT e.community_id, COUNT(*) as cnt
                FROM entities e
                JOIN relations r ON (
                    (r.source_id = ? AND r.target_id = e.id) OR
                    (r.target_id = ? AND r.source_id = e.id)
                )
                WHERE e.community_id IS NOT NULL
                GROUP BY e.community_id
                ORDER BY cnt DESC
                LIMIT 1
                """,
                (entity_id, entity_id),
            )
            row = await cursor.fetchone()

            if row and row[0] is not None:
                # Assign to most connected community
                await engine._connection.execute(
                    "UPDATE entities SET community_id = ? WHERE id = ?",
                    (row[0], entity_id),
                )
            else:
                # No connected communities, leave unassigned or create new
                await engine._connection.execute(
                    "UPDATE entities SET community_id = NULL WHERE id = ?",
                    (entity_id,),
                )

        await engine._connection.commit()

    def _compute_modularity(self, G: Any, communities: list[Community]) -> float:
        """Compute modularity score."""
        from networkx.algorithms.community import modularity

        G_undirected = G.to_undirected()

        # Convert to list of sets for networkx
        partition = [set(c.member_ids) for c in communities]

        if not partition:
            return 0.0

        try:
            return modularity(G_undirected, partition)
        except Exception:
            return 0.0
