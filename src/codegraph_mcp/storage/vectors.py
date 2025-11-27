"""
Vector Store Module

Vector storage and similarity search for code embeddings.

Requirements: REQ-STR-003
Design Reference: design-storage.md §4
"""

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class SearchResult:
    """Vector search result."""

    entity_id: str
    score: float
    distance: float


class VectorStore:
    """
    Vector storage for code embeddings with similarity search.

    Requirements: REQ-STR-003
    Design Reference: design-storage.md §4

    Uses SQLite BLOB storage for vectors with in-memory
    index for fast similarity search.

    Usage:
        store = VectorStore(dimensions=384)
        store.add("entity_1", embedding_vector)
        results = store.search(query_vector, top_k=10)
    """

    def __init__(
        self,
        dimensions: int = 384,
        storage: Any = None,
    ) -> None:
        """
        Initialize vector store.

        Args:
            dimensions: Vector dimensions (must match embedding model)
            storage: SQLiteStorage instance for persistence
        """
        self.dimensions = dimensions
        self.storage = storage

        # In-memory index for fast search
        self._vectors: dict[str, np.ndarray] = {}
        self._loaded = False

    async def initialize(self) -> None:
        """Load vectors from storage into memory."""
        if self._loaded or self.storage is None:
            return

        rows = await self.storage.fetch_all(
            "SELECT id, embedding FROM entities WHERE embedding IS NOT NULL"
        )

        for entity_id, embedding_blob in rows:
            if embedding_blob:
                vector = self._deserialize_vector(embedding_blob)
                self._vectors[entity_id] = vector

        self._loaded = True

    def add(self, entity_id: str, vector: list[float] | np.ndarray) -> None:
        """
        Add vector to store.

        Args:
            entity_id: Entity identifier
            vector: Embedding vector
        """
        if isinstance(vector, list):
            vector = np.array(vector, dtype=np.float32)

        if vector.shape[0] != self.dimensions:
            raise ValueError(
                f"Vector dimension mismatch: expected {self.dimensions}, "
                f"got {vector.shape[0]}"
            )

        # Normalize for cosine similarity
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        self._vectors[entity_id] = vector

    async def add_persistent(
        self,
        entity_id: str,
        vector: list[float] | np.ndarray,
    ) -> None:
        """Add vector and persist to storage."""
        self.add(entity_id, vector)

        if self.storage:
            blob = self._serialize_vector(self._vectors[entity_id])
            await self.storage.execute(
                "UPDATE entities SET embedding = ? WHERE id = ?",
                (blob, entity_id),
            )
            await self.storage.commit()

    def search(
        self,
        query_vector: list[float] | np.ndarray,
        top_k: int = 10,
        threshold: float = 0.0,
    ) -> list[SearchResult]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1)

        Returns:
            List of SearchResult sorted by similarity
        """
        if isinstance(query_vector, list):
            query_vector = np.array(query_vector, dtype=np.float32)

        # Normalize query vector
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm

        if not self._vectors:
            return []

        # Compute similarities
        results: list[SearchResult] = []

        for entity_id, vector in self._vectors.items():
            # Cosine similarity (vectors are normalized)
            similarity = float(np.dot(query_vector, vector))

            if similarity >= threshold:
                results.append(SearchResult(
                    entity_id=entity_id,
                    score=similarity,
                    distance=1.0 - similarity,
                ))

        # Sort by score descending
        results.sort(key=lambda x: -x.score)

        return results[:top_k]

    def search_by_entity(
        self,
        entity_id: str,
        top_k: int = 10,
        exclude_self: bool = True,
    ) -> list[SearchResult]:
        """
        Find entities similar to a given entity.

        Args:
            entity_id: Entity to find similar entities for
            top_k: Number of results
            exclude_self: Whether to exclude the query entity

        Returns:
            List of similar entities
        """
        if entity_id not in self._vectors:
            return []

        query_vector = self._vectors[entity_id]
        results = self.search(query_vector, top_k=top_k + 1)

        if exclude_self:
            results = [r for r in results if r.entity_id != entity_id]

        return results[:top_k]

    def remove(self, entity_id: str) -> bool:
        """
        Remove vector from store.

        Args:
            entity_id: Entity identifier

        Returns:
            True if removed
        """
        if entity_id in self._vectors:
            del self._vectors[entity_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all vectors from memory."""
        self._vectors.clear()
        self._loaded = False

    def _serialize_vector(self, vector: np.ndarray) -> bytes:
        """Serialize vector to bytes for storage."""
        return vector.astype(np.float32).tobytes()

    def _deserialize_vector(self, blob: bytes) -> np.ndarray:
        """Deserialize vector from bytes."""
        return np.frombuffer(blob, dtype=np.float32)

    def get_stats(self) -> dict[str, Any]:
        """Get vector store statistics."""
        return {
            "dimensions": self.dimensions,
            "vector_count": len(self._vectors),
            "memory_bytes": len(self._vectors) * self.dimensions * 4,
            "loaded": self._loaded,
        }
