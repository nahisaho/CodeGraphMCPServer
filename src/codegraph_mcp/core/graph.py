"""
Graph Engine Module

SQLite-based graph storage and query engine for code entities and relations.
Uses NetworkX for in-memory graph operations and path finding.

Requirements: REQ-GRF-001 ~ REQ-GRF-006
Design Reference: design-core-engine.md §2.2, design-storage.md
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx

from codegraph_mcp.core.parser import Entity, EntityType, Relation, RelationType


@dataclass
class GraphQuery:
    """
    Query specification for graph searches.

    Requirements: REQ-TLS-001
    """

    # Natural language query
    query: str

    # Optional filters
    entity_types: list[EntityType] | None = None
    relation_types: list[RelationType] | None = None
    file_patterns: list[str] | None = None

    # Search options
    max_depth: int = 3
    max_results: int = 100
    include_source: bool = False

    # Enhanced query options
    include_related: bool = True  # Include related entities
    include_community: bool = True  # Include community info


@dataclass
class QueryResult:
    """
    Result of a graph query.

    Requirements: REQ-TLS-001
    """

    entities: list[Entity] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)
    paths: list[list[str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    # Enhanced: scores for relevance ranking
    scores: dict[str, float] = field(default_factory=dict)
    # Enhanced: community info for entities
    communities: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        entities_list = []
        for e in self.entities:
            entity_dict = {
                "id": e.id,
                "type": e.type.value,
                "name": e.name,
                "qualified_name": e.qualified_name,
                "file_path": str(e.file_path),
                "start_line": e.start_line,
                "end_line": e.end_line,
            }
            # Add score if available
            if e.id in self.scores:
                entity_dict["score"] = self.scores[e.id]
            # Add community if available
            if e.id in self.communities:
                entity_dict["community_id"] = self.communities[e.id]
            entities_list.append(entity_dict)

        return {
            "entities": entities_list,
            "relations": [
                {
                    "source_id": r.source_id,
                    "target_id": r.target_id,
                    "type": r.type.value,
                }
                for r in self.relations
            ],
            "paths": self.paths,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        lines = [f"Found {len(self.entities)} entities:"]
        for e in self.entities[:10]:
            score_str = ""
            if e.id in self.scores:
                score_str = f" (score: {self.scores[e.id]:.2f})"
            lines.append(f"  - {e.type.value}: {e.qualified_name}{score_str}")
        if len(self.entities) > 10:
            lines.append(f"  ... and {len(self.entities) - 10} more")
        return "\n".join(lines)


@dataclass
class GraphStatistics:
    """Statistics about the graph."""

    entity_count: int = 0
    relation_count: int = 0
    community_count: int = 0
    file_count: int = 0
    languages: list[str] = field(default_factory=list)

    # Per-type counts
    entities_by_type: dict[str, int] = field(default_factory=dict)
    relations_by_type: dict[str, int] = field(default_factory=dict)


class GraphEngine:
    """
    SQLite-based graph engine for code analysis.

    Requirements: REQ-GRF-001 ~ REQ-GRF-006
    Design Reference: design-core-engine.md §2.2

    Usage:
        engine = GraphEngine(Path("/repo"))
        engine.add_entity(entity)
        result = engine.query(GraphQuery("find all functions"))
    """

    def __init__(self, repo_path: Path, db_path: Path | None = None) -> None:
        """
        Initialize the graph engine.

        Args:
            repo_path: Path to the repository
            db_path: Path to SQLite database (default: .codegraph/graph.db)
        """
        self.repo_path = repo_path
        self.db_path = db_path or (repo_path / ".codegraph" / "graph.db")
        self._connection: Any = None

    async def initialize(self) -> None:
        """
        Initialize database connection and schema.

        Requirements: REQ-GRF-005
        """
        import aiosqlite

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = await aiosqlite.connect(self.db_path)
        await self._create_schema()

    async def _create_schema(self) -> None:
        """Create database schema if not exists."""
        schema = """
        -- Entity table (REQ-GRF-003)
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            qualified_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            start_line INTEGER NOT NULL,
            end_line INTEGER NOT NULL,
            start_column INTEGER DEFAULT 0,
            end_column INTEGER DEFAULT 0,
            signature TEXT,
            docstring TEXT,
            source_code TEXT,
            embedding BLOB,
            community_id INTEGER,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Relations table (REQ-GRF-004)
        CREATE TABLE IF NOT EXISTS relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            type TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            metadata TEXT,
            FOREIGN KEY (source_id) REFERENCES entities(id) ON DELETE CASCADE,
            FOREIGN KEY (target_id) REFERENCES entities(id) ON DELETE CASCADE
        );

        -- Communities table (REQ-SEM-003)
        CREATE TABLE IF NOT EXISTS communities (
            id INTEGER PRIMARY KEY,
            level INTEGER NOT NULL,
            name TEXT,
            summary TEXT,
            member_count INTEGER DEFAULT 0,
            parent_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES communities(id)
        );

        -- File tracking table
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            language TEXT,
            hash TEXT NOT NULL,
            size INTEGER,
            entity_count INTEGER DEFAULT 0,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Indexes (REQ-GRF-006)
        CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
        CREATE INDEX IF NOT EXISTS idx_entities_file ON entities(file_path);
        CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
        CREATE INDEX IF NOT EXISTS idx_entities_qualified ON entities(qualified_name);
        CREATE INDEX IF NOT EXISTS idx_entities_community ON entities(community_id);
        CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id);
        CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id);
        CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(type);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_relations_unique
            ON relations(source_id, target_id, type);
        """

        for statement in schema.split(";"):
            statement = statement.strip()
            if statement:
                await self._connection.execute(statement)
        await self._connection.commit()

    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def add_entity(self, entity: Entity) -> str:
        """
        Add an entity to the graph.

        Args:
            entity: Entity to add

        Returns:
            Entity ID

        Requirements: REQ-GRF-003
        """
        import json

        await self._connection.execute(
            """
            INSERT OR REPLACE INTO entities
            (id, type, name, qualified_name, file_path, start_line, end_line,
             start_column, end_column, signature, docstring, source_code, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entity.id,
                entity.type.value,
                entity.name,
                entity.qualified_name,
                str(entity.file_path),
                entity.start_line,
                entity.end_line,
                entity.location.start_column,
                entity.location.end_column,
                entity.signature,
                entity.docstring,
                entity.source_code,
                json.dumps(entity.metadata),
            ),
        )
        await self._connection.commit()
        return entity.id

    async def add_relation(self, relation: Relation) -> int:
        """
        Add a relation to the graph.

        Args:
            relation: Relation to add

        Returns:
            Relation ID

        Requirements: REQ-GRF-004
        """
        import json

        cursor = await self._connection.execute(
            """
            INSERT OR IGNORE INTO relations
            (source_id, target_id, type, weight, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                relation.source_id,
                relation.target_id,
                relation.type.value,
                relation.weight,
                json.dumps(relation.metadata),
            ),
        )
        await self._connection.commit()
        return cursor.lastrowid

    async def add_entities_batch(self, entities: list[Entity]) -> int:
        """
        Add multiple entities in a single batch operation.

        This is significantly faster than adding entities one by one
        because it uses executemany and commits once at the end.

        Args:
            entities: List of entities to add.

        Returns:
            Number of entities added.
        """
        if not entities:
            return 0

        data = [
            (
                entity.id,
                entity.type.value,
                entity.name,
                entity.qualified_name,
                str(entity.file_path),
                entity.start_line,
                entity.end_line,
                entity.signature or "",
                entity.docstring or "",
                json.dumps(entity.metadata),
            )
            for entity in entities
        ]

        await self._connection.executemany(
            """
            INSERT OR REPLACE INTO entities
            (id, type, name, qualified_name, file_path,
             start_line, end_line, signature, docstring, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            data,
        )
        await self._connection.commit()
        return len(entities)

    async def add_relations_batch(self, relations: list[Relation]) -> int:
        """
        Add multiple relations in a single batch operation.

        This is significantly faster than adding relations one by one
        because it uses executemany and commits once at the end.

        Args:
            relations: List of relations to add.

        Returns:
            Number of relations added.
        """
        if not relations:
            return 0

        data = [
            (
                relation.source_id,
                relation.target_id,
                relation.type.value,
                relation.weight,
                json.dumps(relation.metadata),
            )
            for relation in relations
        ]

        await self._connection.executemany(
            """
            INSERT OR IGNORE INTO relations
            (source_id, target_id, type, weight, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            data,
        )
        await self._connection.commit()
        return len(relations)

    async def resolve_entity_id(
        self,
        entity_id: str,
        entity_type: EntityType | None = None,
    ) -> str | None:
        """
        Resolve a partial entity ID to a full entity ID.

        Supports:
        - Exact match: Returns if entity_id matches exactly
        - Name match: Searches by entity name
        - Qualified name suffix: Searches by qualified_name ending
        - File + name: "filename::name" pattern

        Args:
            entity_id: Full or partial entity identifier
            entity_type: Optional type filter

        Returns:
            Full entity ID or None if not found/ambiguous
        """
        # First try exact match
        cursor = await self._connection.execute(
            "SELECT id FROM entities WHERE id = ?",
            (entity_id,),
        )
        row = await cursor.fetchone()
        if row:
            return row[0]

        # Build query for partial matches
        type_filter = ""
        params: list[Any] = []

        if entity_type:
            type_filter = " AND type = ?"
            params.append(entity_type.value)

        # Try name exact match (may return multiple)
        cursor = await self._connection.execute(
            f"""
            SELECT id, qualified_name FROM entities
            WHERE name = ?{type_filter}
            ORDER BY LENGTH(id) ASC
            LIMIT 10
            """,
            [entity_id, *params],
        )
        rows = await cursor.fetchall()
        if len(rows) == 1:
            return rows[0][0]
        elif len(rows) > 1:
            # Multiple matches - ambiguous, return None
            return None

        # Try qualified_name suffix match
        cursor = await self._connection.execute(
            f"""
            SELECT id FROM entities
            WHERE qualified_name LIKE ?{type_filter}
            ORDER BY LENGTH(id) ASC
            LIMIT 10
            """,
            [f"%{entity_id}", *params],
        )
        rows = await cursor.fetchall()
        if len(rows) == 1:
            return rows[0][0]
        elif len(rows) > 1:
            # Multiple matches - ambiguous, return None
            return None

        # Try file::name pattern
        if "::" in entity_id:
            parts = entity_id.rsplit("::", 1)
            file_part, name_part = parts[0], parts[1]
            cursor = await self._connection.execute(
                f"""
                SELECT id FROM entities
                WHERE name = ? AND file_path LIKE ?{type_filter}
                ORDER BY LENGTH(id) ASC
                LIMIT 10
                """,
                [name_part, f"%{file_part}%", *params],
            )
            rows = await cursor.fetchall()
            if rows:
                return rows[0][0]

        return None

    async def search_entities(
        self,
        pattern: str,
        entity_type: EntityType | None = None,
        limit: int = 20,
    ) -> list[Entity]:
        """
        Search entities by name pattern.

        Args:
            pattern: Search pattern (supports SQL LIKE wildcards)
            entity_type: Optional type filter
            limit: Maximum results

        Returns:
            List of matching entities
        """
        type_filter = ""
        params: list[Any] = [f"%{pattern}%", f"%{pattern}%"]

        if entity_type:
            type_filter = " AND type = ?"
            params.append(entity_type.value)

        params.append(limit)

        cursor = await self._connection.execute(
            f"""
            SELECT * FROM entities
            WHERE (name LIKE ? OR qualified_name LIKE ?){type_filter}
            ORDER BY
                CASE WHEN name = ? THEN 0 ELSE 1 END,
                LENGTH(name) ASC
            LIMIT ?
            """,
            [*params[:2], pattern, *params[2:]],
        )
        rows = await cursor.fetchall()
        return [self._row_to_entity(row) for row in rows]

    async def get_entity(self, entity_id: str) -> Entity | None:
        """Get an entity by ID (supports partial matching)."""
        # Try to resolve partial ID
        resolved_id = await self.resolve_entity_id(entity_id)
        if not resolved_id:
            return None

        cursor = await self._connection.execute(
            "SELECT * FROM entities WHERE id = ?",
            (resolved_id,),
        )
        row = await cursor.fetchone()
        if row:
            return self._row_to_entity(row)
        return None

    async def find_callers(self, entity_id: str) -> list[Entity]:
        """
        Find all entities that call the given entity.

        Supports partial entity_id matching.

        Requirements: REQ-TLS-003
        """
        # Resolve partial entity_id
        resolved_id = await self.resolve_entity_id(entity_id)
        if not resolved_id:
            return []

        cursor = await self._connection.execute(
            """
            SELECT e.* FROM entities e
            JOIN relations r ON e.id = r.source_id
            WHERE r.target_id = ? AND r.type = 'calls'
            """,
            (resolved_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_entity(row) for row in rows]

    async def find_callees(self, entity_id: str) -> list[Entity]:
        """
        Find all entities called by the given entity.

        Supports partial entity_id matching.

        Requirements: REQ-TLS-004
        """
        # Resolve partial entity_id
        resolved_id = await self.resolve_entity_id(entity_id)
        if not resolved_id:
            return []

        cursor = await self._connection.execute(
            """
            SELECT e.* FROM entities e
            JOIN relations r ON e.id = r.target_id
            WHERE r.source_id = ? AND r.type = 'calls'
            """,
            (resolved_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_entity(row) for row in rows]

    async def find_dependencies(
        self, entity_id: str, depth: int = 1
    ) -> QueryResult:
        """
        Find dependencies of an entity up to given depth.

        Supports partial entity_id matching.

        Requirements: REQ-TLS-002
        """
        # Resolve partial entity_id
        resolved_id = await self.resolve_entity_id(entity_id)
        if not resolved_id:
            return QueryResult(entities=[], relations=[])

        visited: set[str] = set()
        entities: list[Entity] = []
        relations: list[Relation] = []

        async def traverse(eid: str, current_depth: int) -> None:
            if eid in visited or current_depth > depth:
                return
            visited.add(eid)

            entity = await self.get_entity(eid)
            if entity:
                entities.append(entity)

            cursor = await self._connection.execute(
                """
                SELECT target_id, type, weight FROM relations
                WHERE source_id = ? AND type IN ('imports', 'calls', 'uses')
                """,
                (eid,),
            )
            for row in await cursor.fetchall():
                rel = Relation(
                    source_id=eid,
                    target_id=row[0],
                    type=RelationType(row[1]),
                    weight=row[2],
                )
                relations.append(rel)
                await traverse(row[0], current_depth + 1)

        await traverse(resolved_id, 0)
        return QueryResult(entities=entities, relations=relations)

    async def query(self, query: str | GraphQuery) -> QueryResult:
        """
        Execute a graph query with relevance scoring.

        Args:
            query: Query string or GraphQuery object

        Returns:
            QueryResult with matching entities, scores, and community info

        Requirements: REQ-TLS-001
        """
        if isinstance(query, str):
            query = GraphQuery(query=query)

        search_term = query.query.lower()
        scores: dict[str, float] = {}
        communities: dict[str, int] = {}
        all_entities: list[Entity] = []
        all_relations: list[Relation] = []

        # Phase 1: Direct matches with scoring
        base_sql = """
            SELECT *, community_id FROM entities WHERE 1=1
        """
        params: list[Any] = []

        if query.entity_types:
            placeholders = ",".join("?" * len(query.entity_types))
            base_sql += f" AND type IN ({placeholders})"
            params.extend(t.value for t in query.entity_types)

        if query.file_patterns:
            pattern_conditions = []
            for pattern in query.file_patterns:
                pattern_conditions.append("file_path LIKE ?")
                params.append(f"%{pattern}%")
            base_sql += f" AND ({' OR '.join(pattern_conditions)})"

        # Text search with different matching strategies
        if query.query:
            base_sql += " AND (name LIKE ? OR qualified_name LIKE ?)"
            params.extend([f"%{query.query}%", f"%{query.query}%"])

        base_sql += f" LIMIT {query.max_results * 2}"  # Get more for scoring

        cursor = await self._connection.execute(base_sql, params)
        rows = await cursor.fetchall()

        seen_ids: set[str] = set()
        for row in rows:
            entity = self._row_to_entity(row)
            if entity.id not in seen_ids:
                seen_ids.add(entity.id)
                all_entities.append(entity)

                # Calculate relevance score
                score = self._calculate_relevance_score(
                    entity, search_term
                )
                scores[entity.id] = score

                # Track community
                if len(row) > 10 and row[10] is not None:
                    communities[entity.id] = row[10]

        # Phase 2: Include related entities if enabled
        if query.include_related and all_entities:
            direct_ids = list(seen_ids)
            related_entities, related_relations = await self._get_related(
                direct_ids[:20],  # Limit for performance
                query.max_results // 2,
            )

            for entity in related_entities:
                if entity.id not in seen_ids:
                    seen_ids.add(entity.id)
                    all_entities.append(entity)
                    # Related entities get lower base score
                    scores[entity.id] = 0.3

            all_relations.extend(related_relations)

        # Phase 3: Add community info if enabled
        if query.include_community:
            for entity in all_entities:
                if entity.id not in communities:
                    cursor = await self._connection.execute(
                        "SELECT community_id FROM entities WHERE id = ?",
                        (entity.id,),
                    )
                    row = await cursor.fetchone()
                    if row and row[0] is not None:
                        communities[entity.id] = row[0]

        # Sort by score and limit results
        all_entities.sort(key=lambda e: scores.get(e.id, 0), reverse=True)
        all_entities = all_entities[:query.max_results]

        return QueryResult(
            entities=all_entities,
            relations=all_relations,
            scores=scores,
            communities=communities,
            metadata={
                "query": query.query,
                "count": len(all_entities),
                "include_related": query.include_related,
            },
        )

    def _calculate_relevance_score(
        self, entity: Entity, search_term: str
    ) -> float:
        """Calculate relevance score for an entity."""
        score = 0.0
        name_lower = entity.name.lower()
        qualified_lower = entity.qualified_name.lower()

        # Exact name match: highest score
        if name_lower == search_term:
            score += 1.0
        # Name starts with search term
        elif name_lower.startswith(search_term):
            score += 0.8
        # Name contains search term
        elif search_term in name_lower:
            score += 0.6

        # Qualified name bonus
        if search_term in qualified_lower:
            score += 0.2

        # Entity type bonus (functions/classes are often more relevant)
        if entity.type in (EntityType.FUNCTION, EntityType.CLASS):
            score += 0.1

        return min(score, 1.0)

    async def _get_related(
        self, entity_ids: list[str], limit: int
    ) -> tuple[list[Entity], list[Relation]]:
        """Get entities related to the given entities."""
        if not entity_ids:
            return [], []

        entities: list[Entity] = []
        relations: list[Relation] = []

        placeholders = ",".join("?" * len(entity_ids))

        # Get direct relations
        cursor = await self._connection.execute(
            f"""
            SELECT DISTINCT target_id, type, weight FROM relations
            WHERE source_id IN ({placeholders})
            UNION
            SELECT DISTINCT source_id, type, weight FROM relations
            WHERE target_id IN ({placeholders})
            LIMIT ?
            """,
            entity_ids + entity_ids + [limit * 2],
        )
        related_rows = await cursor.fetchall()

        related_ids: set[str] = set()
        for row in related_rows:
            related_ids.add(row[0])

        # Filter out already known IDs
        related_ids -= set(entity_ids)

        if related_ids:
            id_placeholders = ",".join("?" * len(related_ids))
            cursor = await self._connection.execute(
                f"SELECT * FROM entities WHERE id IN ({id_placeholders})",
                list(related_ids),
            )
            for row in await cursor.fetchall():
                entities.append(self._row_to_entity(row))

        return entities[:limit], relations

    async def get_statistics(self) -> GraphStatistics:
        """
        Get graph statistics.

        Requirements: REQ-RSC-004
        """
        stats = GraphStatistics()

        # Total counts
        cursor = await self._connection.execute(
            "SELECT COUNT(*) FROM entities"
        )
        stats.entity_count = (await cursor.fetchone())[0]

        cursor = await self._connection.execute(
            "SELECT COUNT(*) FROM relations"
        )
        stats.relation_count = (await cursor.fetchone())[0]

        cursor = await self._connection.execute(
            "SELECT COUNT(*) FROM communities"
        )
        stats.community_count = (await cursor.fetchone())[0]

        cursor = await self._connection.execute(
            "SELECT COUNT(DISTINCT file_path) FROM entities"
        )
        stats.file_count = (await cursor.fetchone())[0]

        # Counts by type
        cursor = await self._connection.execute(
            "SELECT type, COUNT(*) FROM entities GROUP BY type"
        )
        for row in await cursor.fetchall():
            stats.entities_by_type[row[0]] = row[1]

        cursor = await self._connection.execute(
            "SELECT type, COUNT(*) FROM relations GROUP BY type"
        )
        for row in await cursor.fetchall():
            stats.relations_by_type[row[0]] = row[1]

        return stats

    def _row_to_entity(self, row: tuple) -> Entity:
        """Convert database row to Entity object."""
        from codegraph_mcp.core.parser import Location

        return Entity(
            id=row[0],
            type=EntityType(row[1]),
            name=row[2],
            qualified_name=row[3],
            location=Location(
                file_path=Path(row[4]),
                start_line=row[5],
                end_line=row[6],
                start_column=row[7] or 0,
                end_column=row[8] or 0,
            ),
            signature=row[9],
            docstring=row[10],
            source_code=row[11],
            metadata=json.loads(row[14]) if row[14] else {},
        )

    async def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> list[list[str]]:
        """
        Find all paths between two entities.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            max_depth: Maximum path length

        Returns:
            List of paths (each path is a list of entity IDs)

        Requirements: REQ-TLS-005
        """
        # Build NetworkX graph from relations
        G = await self._build_networkx_graph()

        if source_id not in G or target_id not in G:
            return []

        try:
            # Find all simple paths up to max_depth
            paths = list(nx.all_simple_paths(
                G, source_id, target_id, cutoff=max_depth
            ))
            return paths[:10]  # Limit to 10 paths
        except nx.NetworkXNoPath:
            return []

    async def _build_networkx_graph(self) -> nx.DiGraph:
        """Build NetworkX graph from database."""
        G = nx.DiGraph()

        # Add all entities as nodes
        cursor = await self._connection.execute(
            "SELECT id, type, name FROM entities"
        )
        for row in await cursor.fetchall():
            G.add_node(row[0], type=row[1], name=row[2])

        # Add all relations as edges
        cursor = await self._connection.execute(
            "SELECT source_id, target_id, type, weight FROM relations"
        )
        for row in await cursor.fetchall():
            G.add_edge(row[0], row[1], type=row[2], weight=row[3])

        return G

    async def get_neighbors(
        self,
        entity_id: str,
        direction: str = "both",
        relation_types: list[RelationType] | None = None,
    ) -> list[Entity]:
        """
        Get neighboring entities.

        Args:
            entity_id: Entity ID
            direction: "in", "out", or "both"
            relation_types: Filter by relation types

        Returns:
            List of neighboring entities
        """
        entities = []

        type_filter = ""
        params: list[Any] = [entity_id]
        if relation_types:
            placeholders = ",".join("?" * len(relation_types))
            type_filter = f" AND r.type IN ({placeholders})"
            params.extend(t.value for t in relation_types)

        if direction in ("out", "both"):
            cursor = await self._connection.execute(
                f"""
                SELECT DISTINCT e.* FROM entities e
                JOIN relations r ON e.id = r.target_id
                WHERE r.source_id = ?{type_filter}
                """,
                params,
            )
            for row in await cursor.fetchall():
                entities.append(self._row_to_entity(row))

        if direction in ("in", "both"):
            cursor = await self._connection.execute(
                f"""
                SELECT DISTINCT e.* FROM entities e
                JOIN relations r ON e.id = r.source_id
                WHERE r.target_id = ?{type_filter}
                """,
                params,
            )
            for row in await cursor.fetchall():
                entities.append(self._row_to_entity(row))

        # Deduplicate
        seen = set()
        unique = []
        for e in entities:
            if e.id not in seen:
                seen.add(e.id)
                unique.append(e)

        return unique

    async def get_subgraph(
        self,
        entity_id: str,
        depth: int = 2,
    ) -> QueryResult:
        """
        Get a subgraph centered on an entity.

        Args:
            entity_id: Center entity ID
            depth: Radius of the subgraph

        Returns:
            QueryResult with entities and relations in the subgraph
        """
        visited: set[str] = set()
        entities: list[Entity] = []
        relations: list[Relation] = []

        async def traverse(eid: str, current_depth: int) -> None:
            if eid in visited or current_depth > depth:
                return
            visited.add(eid)

            entity = await self.get_entity(eid)
            if entity:
                entities.append(entity)

            # Get outgoing relations
            cursor = await self._connection.execute(
                "SELECT target_id, type, weight FROM relations WHERE source_id = ?",
                (eid,),
            )
            for row in await cursor.fetchall():
                rel = Relation(
                    source_id=eid,
                    target_id=row[0],
                    type=RelationType(row[1]) if row[1] in [r.value for r in RelationType] else RelationType.REFERENCES,
                    weight=row[2],
                )
                relations.append(rel)
                await traverse(row[0], current_depth + 1)

            # Get incoming relations
            cursor = await self._connection.execute(
                "SELECT source_id, type, weight FROM relations WHERE target_id = ?",
                (eid,),
            )
            for row in await cursor.fetchall():
                rel = Relation(
                    source_id=row[0],
                    target_id=eid,
                    type=RelationType(row[1]) if row[1] in [r.value for r in RelationType] else RelationType.REFERENCES,
                    weight=row[2],
                )
                relations.append(rel)
                await traverse(row[0], current_depth + 1)

        await traverse(entity_id, 0)

        return QueryResult(
            entities=entities,
            relations=relations,
            metadata={"center": entity_id, "depth": depth},
        )

    async def search_by_name(
        self,
        name_pattern: str,
        entity_types: list[EntityType] | None = None,
        limit: int = 50,
    ) -> list[Entity]:
        """
        Search entities by name pattern.

        Args:
            name_pattern: SQL LIKE pattern for name
            entity_types: Filter by entity types
            limit: Maximum results

        Returns:
            List of matching entities
        """
        sql = "SELECT * FROM entities WHERE name LIKE ?"
        params: list[Any] = [f"%{name_pattern}%"]

        if entity_types:
            placeholders = ",".join("?" * len(entity_types))
            sql += f" AND type IN ({placeholders})"
            params.extend(t.value for t in entity_types)

        sql += f" LIMIT {limit}"

        cursor = await self._connection.execute(sql, params)
        rows = await cursor.fetchall()
        return [self._row_to_entity(row) for row in rows]

    async def delete_file_entities(self, file_path: Path) -> int:
        """
        Delete all entities from a file.

        Args:
            file_path: Path to the file

        Returns:
            Number of deleted entities
        """
        # Get entity IDs first
        cursor = await self._connection.execute(
            "SELECT id FROM entities WHERE file_path = ?",
            (str(file_path),),
        )
        entity_ids = [row[0] for row in await cursor.fetchall()]

        if not entity_ids:
            return 0

        # Delete relations
        placeholders = ",".join("?" * len(entity_ids))
        await self._connection.execute(
            f"DELETE FROM relations WHERE source_id IN ({placeholders})",
            entity_ids,
        )
        await self._connection.execute(
            f"DELETE FROM relations WHERE target_id IN ({placeholders})",
            entity_ids,
        )

        # Delete entities
        await self._connection.execute(
            f"DELETE FROM entities WHERE id IN ({placeholders})",
            entity_ids,
        )

        await self._connection.commit()
        return len(entity_ids)

    async def clear(self) -> None:
        """Clear all data from the graph."""
        await self._connection.execute("DELETE FROM relations")
        await self._connection.execute("DELETE FROM entities")
        await self._connection.execute("DELETE FROM communities")
        await self._connection.execute("DELETE FROM files")
        await self._connection.commit()
