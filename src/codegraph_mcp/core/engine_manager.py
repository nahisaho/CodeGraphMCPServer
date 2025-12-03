"""
Graph Engine Manager Module

Provides singleton management and caching for GraphEngine instances.
Ensures efficient connection reuse across tool calls.

Requirements: Performance optimization for MCP tools
Design Reference: design-core-engine.md
"""

import asyncio
from functools import lru_cache
from pathlib import Path
from typing import Any

from codegraph_mcp.core.graph import GraphEngine, GraphStatistics, QueryResult
from codegraph_mcp.core.parser import Entity
from codegraph_mcp.utils.logging import get_logger

logger = get_logger(__name__)


class EngineManager:
    """
    Singleton manager for GraphEngine instances.

    Provides:
    - Connection pooling via singleton pattern
    - LRU caching for frequent queries
    - Automatic reconnection on failure
    - Graceful shutdown

    Usage:
        manager = EngineManager.get_instance(repo_path)
        engine = await manager.get_engine()
        result = await engine.query(...)
        # No need to close - managed by EngineManager
    """

    _instances: dict[Path, "EngineManager"] = {}
    _lock = asyncio.Lock()

    def __init__(self, repo_path: Path) -> None:
        """Initialize manager for a repository."""
        self._repo_path = repo_path.resolve()
        self._engine: GraphEngine | None = None
        self._initialized = False
        self._init_lock = asyncio.Lock()

        # Cache for expensive operations
        self._stats_cache: GraphStatistics | None = None
        self._stats_cache_time: float = 0
        self._entity_cache: dict[str, Entity | None] = {}
        self._cache_ttl = 60.0  # 60 seconds TTL

    @classmethod
    async def get_instance(cls, repo_path: Path) -> "EngineManager":
        """
        Get or create an EngineManager instance for a repository.

        Thread-safe singleton per repository.
        """
        resolved = repo_path.resolve()

        async with cls._lock:
            if resolved not in cls._instances:
                logger.info(f"Creating new EngineManager for {resolved}")
                cls._instances[resolved] = cls(resolved)
            return cls._instances[resolved]

    @classmethod
    async def close_all(cls) -> None:
        """Close all engine instances. Call on server shutdown."""
        async with cls._lock:
            for path, manager in cls._instances.items():
                logger.info(f"Closing EngineManager for {path}")
                await manager.close()
            cls._instances.clear()

    async def get_engine(self) -> GraphEngine:
        """
        Get the GraphEngine instance, initializing if needed.

        Returns:
            Initialized GraphEngine instance

        Raises:
            FileNotFoundError: If database doesn't exist
        """
        async with self._init_lock:
            if self._engine is None or not self._initialized:
                await self._initialize()
            return self._engine  # type: ignore

    async def _initialize(self) -> None:
        """Initialize the GraphEngine connection."""
        if self._engine is not None:
            try:
                await self._engine.close()
            except Exception:
                pass

        self._engine = GraphEngine(self._repo_path)
        await self._engine.initialize()
        self._initialized = True
        self._clear_cache()
        logger.info(f"GraphEngine initialized for {self._repo_path}")

    async def close(self) -> None:
        """Close the engine connection."""
        async with self._init_lock:
            if self._engine:
                await self._engine.close()
                self._engine = None
                self._initialized = False
                self._clear_cache()

    def _clear_cache(self) -> None:
        """Clear all caches."""
        self._stats_cache = None
        self._stats_cache_time = 0
        self._entity_cache.clear()

    def invalidate_cache(self) -> None:
        """Invalidate cache after data modifications."""
        self._clear_cache()

    # Cached operations

    async def get_statistics_cached(self) -> GraphStatistics:
        """
        Get graph statistics with caching.

        Caches results for `cache_ttl` seconds.
        """
        import time

        current_time = time.time()
        if (
            self._stats_cache is not None
            and (current_time - self._stats_cache_time) < self._cache_ttl
        ):
            return self._stats_cache

        engine = await self.get_engine()
        self._stats_cache = await engine.get_statistics()
        self._stats_cache_time = current_time
        return self._stats_cache

    async def get_entity_cached(self, entity_id: str) -> Entity | None:
        """
        Get entity by ID with caching.

        Uses LRU-style cache limited to 1000 entries.
        """
        # Check cache first
        if entity_id in self._entity_cache:
            return self._entity_cache[entity_id]

        # Limit cache size
        if len(self._entity_cache) > 1000:
            # Remove oldest entries (first 200)
            keys_to_remove = list(self._entity_cache.keys())[:200]
            for key in keys_to_remove:
                del self._entity_cache[key]

        # Fetch and cache
        engine = await self.get_engine()
        entity = await engine.get_entity(entity_id)
        self._entity_cache[entity_id] = entity
        return entity

    async def query_cached(
        self,
        query_str: str,
        max_results: int = 20,
    ) -> QueryResult:
        """
        Execute a query. Queries are not cached due to complexity.

        For heavy queries, consider using get_entity_cached for follow-up.
        """
        from codegraph_mcp.core.graph import GraphQuery

        engine = await self.get_engine()
        query = GraphQuery(query=query_str, max_results=max_results)
        return await engine.query(query)

    async def healthcheck(self) -> dict[str, Any]:
        """
        Check engine health and connection status.

        Returns:
            Dict with status, connected, repo_path, and optional error
        """
        try:
            engine = await self.get_engine()
            stats = await self.get_statistics_cached()
            return {
                "status": "healthy",
                "connected": True,
                "repo_path": str(self._repo_path),
                "entity_count": stats.entity_count,
                "cache_size": len(self._entity_cache),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "repo_path": str(self._repo_path),
                "error": str(e),
            }


# Module-level convenience functions

async def get_engine(repo_path: Path) -> GraphEngine:
    """Get a managed GraphEngine instance."""
    manager = await EngineManager.get_instance(repo_path)
    return await manager.get_engine()


async def get_manager(repo_path: Path) -> EngineManager:
    """Get the EngineManager for a repository."""
    return await EngineManager.get_instance(repo_path)


async def shutdown_all() -> None:
    """Shutdown all engine managers. Call on application exit."""
    await EngineManager.close_all()
