"""
File Cache Module

Caching layer for parsed files and intermediate results.

Requirements: REQ-STR-002
Design Reference: design-storage.md §3
"""

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CacheEntry:
    """Cache entry metadata."""

    key: str
    size: int
    created_at: float
    expires_at: float | None
    hits: int = 0


class FileCache:
    """
    File-based cache for parsed content and results.

    Requirements: REQ-STR-002
    Design Reference: design-storage.md §3

    Usage:
        cache = FileCache(Path(".codegraph/cache"))
        cache.set("key", {"data": "value"})
        data = cache.get("key")
    """

    def __init__(
        self,
        cache_dir: Path,
        max_size_mb: int = 100,
        ttl_seconds: int = 3600,
    ) -> None:
        """
        Initialize file cache.

        Args:
            cache_dir: Directory for cache files
            max_size_mb: Maximum cache size in MB
            ttl_seconds: Default time-to-live in seconds
        """
        self.cache_dir = cache_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.ttl_seconds = ttl_seconds
        self._metadata: dict[str, CacheEntry] = {}

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load metadata
        self._load_metadata()

    def _key_to_path(self, key: str) -> Path:
        """Convert cache key to file path."""
        # Hash the key to create a safe filename
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self.cache_dir / f"{key_hash}.cache"

    def _metadata_path(self) -> Path:
        """Get metadata file path."""
        return self.cache_dir / "_metadata.json"

    def _load_metadata(self) -> None:
        """Load cache metadata from disk."""
        meta_path = self._metadata_path()
        if meta_path.exists():
            try:
                data = json.loads(meta_path.read_text())
                self._metadata = {
                    k: CacheEntry(**v) for k, v in data.items()
                }
            except (json.JSONDecodeError, TypeError):
                self._metadata = {}

    def _save_metadata(self) -> None:
        """Save cache metadata to disk."""
        data = {
            k: {
                "key": v.key,
                "size": v.size,
                "created_at": v.created_at,
                "expires_at": v.expires_at,
                "hits": v.hits,
            }
            for k, v in self._metadata.items()
        }
        self._metadata_path().write_text(json.dumps(data))

    def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        entry = self._metadata.get(key)
        if entry is None:
            return None

        # Check expiration
        now = time.time()
        if entry.expires_at and now > entry.expires_at:
            self.delete(key)
            return None

        # Read from file
        cache_path = self._key_to_path(key)
        if not cache_path.exists():
            del self._metadata[key]
            return None

        try:
            data = json.loads(cache_path.read_text())
            entry.hits += 1
            return data
        except (OSError, json.JSONDecodeError):
            self.delete(key)
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (uses default if None)
        """
        # Serialize value
        data = json.dumps(value)
        size = len(data.encode())

        # Check if we need to evict entries
        self._ensure_space(size)

        # Write to file
        cache_path = self._key_to_path(key)
        cache_path.write_text(data)

        # Update metadata
        now = time.time()
        ttl = ttl if ttl is not None else self.ttl_seconds

        self._metadata[key] = CacheEntry(
            key=key,
            size=size,
            created_at=now,
            expires_at=now + ttl if ttl > 0 else None,
        )

        self._save_metadata()

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if entry was deleted
        """
        if key not in self._metadata:
            return False

        cache_path = self._key_to_path(key)
        if cache_path.exists():
            cache_path.unlink()

        del self._metadata[key]
        self._save_metadata()
        return True

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        count = len(self._metadata)

        for key in list(self._metadata.keys()):
            cache_path = self._key_to_path(key)
            if cache_path.exists():
                cache_path.unlink()

        self._metadata.clear()
        self._save_metadata()
        return count

    def _ensure_space(self, needed_bytes: int) -> None:
        """Ensure there's enough space by evicting old entries."""
        current_size = sum(e.size for e in self._metadata.values())

        if current_size + needed_bytes <= self.max_size_bytes:
            return

        # Sort by last access (LRU eviction)
        entries = sorted(
            self._metadata.items(),
            key=lambda x: (x[1].hits, x[1].created_at),
        )

        # Evict until we have space
        for key, entry in entries:
            if current_size + needed_bytes <= self.max_size_bytes:
                break

            current_size -= entry.size
            self.delete(key)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_size = sum(e.size for e in self._metadata.values())
        total_hits = sum(e.hits for e in self._metadata.values())

        return {
            "entries": len(self._metadata),
            "size_bytes": total_size,
            "size_mb": total_size / (1024 * 1024),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "usage_percent": (total_size / self.max_size_bytes) * 100,
            "total_hits": total_hits,
        }

    def cleanup_expired(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries removed
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self._metadata.items()
            if entry.expires_at and now > entry.expires_at
        ]

        for key in expired_keys:
            self.delete(key)

        return len(expired_keys)
