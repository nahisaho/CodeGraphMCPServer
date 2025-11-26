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
    ) -> None:
        """
        Initialize the community detector.
        
        Args:
            algorithm: Detection algorithm ("louvain" or "leiden")
            resolution: Resolution parameter for modularity
            min_size: Minimum community size
        """
        self.algorithm = algorithm
        self.resolution = resolution
        self.min_size = min_size
    
    async def detect(self, engine: Any) -> CommunityResult:
        """
        Detect communities in the code graph.
        
        Args:
            engine: GraphEngine instance
            
        Returns:
            CommunityResult with detected communities
            
        Requirements: REQ-SEM-003
        """
        import networkx as nx
        
        # Build NetworkX graph from entities and relations
        G = await self._build_networkx_graph(engine)
        
        if G.number_of_nodes() == 0:
            return CommunityResult()
        
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
    
    async def _build_networkx_graph(self, engine: Any) -> Any:
        """Build NetworkX graph from database."""
        import networkx as nx
        
        G = nx.DiGraph()
        
        # Add nodes
        cursor = await engine._connection.execute(
            "SELECT id, type, name FROM entities"
        )
        for row in await cursor.fetchall():
            G.add_node(row[0], type=row[1], name=row[2])
        
        # Add edges
        cursor = await engine._connection.execute(
            "SELECT source_id, target_id, type, weight FROM relations"
        )
        for row in await cursor.fetchall():
            G.add_edge(row[0], row[1], type=row[2], weight=row[3])
        
        return G
    
    def _detect_louvain(self, G: Any) -> list[Community]:
        """Apply Louvain algorithm for community detection."""
        import networkx as nx
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
        """Store communities in database."""
        # Clear existing communities
        await engine._connection.execute("DELETE FROM communities")
        
        # Insert new communities
        for community in communities:
            await engine._connection.execute(
                """
                INSERT INTO communities (id, level, name, summary, member_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    community.id,
                    community.level,
                    community.name,
                    community.summary,
                    community.member_count,
                ),
            )
            
            # Update entity community assignments
            for member_id in community.member_ids:
                await engine._connection.execute(
                    "UPDATE entities SET community_id = ? WHERE id = ?",
                    (community.id, member_id),
                )
        
        await engine._connection.commit()
    
    def _compute_modularity(self, G: Any, communities: list[Community]) -> float:
        """Compute modularity score."""
        import networkx as nx
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
