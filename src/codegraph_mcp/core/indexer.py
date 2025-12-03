"""
Indexer Module

Repository indexing with incremental update support.

Requirements: REQ-IDX-001 ~ REQ-IDX-004
Design Reference: design-core-engine.md §2.4
"""

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from codegraph_mcp.core.graph import GraphEngine
from codegraph_mcp.core.parser import ASTParser, ParseResult


# Type alias for progress callback
ProgressCallback = Callable[[int, int, Path | None], None]


@dataclass
class IndexResult:
    """Result of indexing operation."""

    entities_count: int = 0
    relations_count: int = 0
    files_indexed: int = 0
    files_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    # Track entity IDs that were added/updated for incremental community update
    changed_entity_ids: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


@dataclass
class FileInfo:
    """Information about an indexed file."""

    path: Path
    language: str | None
    hash: str
    size: int
    indexed_at: datetime


class Indexer:
    """
    Repository indexer with incremental update support.

    Requirements: REQ-IDX-001 ~ REQ-IDX-004
    Design Reference: design-core-engine.md §2.4

    Usage:
        indexer = Indexer()
        result = await indexer.index_repository(Path("/repo"))
    """

    def __init__(
        self,
        parser: ASTParser | None = None,
        config: Any = None,
    ) -> None:
        """
        Initialize the indexer.

        Args:
            parser: AST parser instance (creates default if not provided)
            config: Configuration object
        """
        self.parser = parser or ASTParser()
        self.config = config
        self._engine: GraphEngine | None = None

    async def index_repository(
        self,
        repo_path: Path,
        incremental: bool = True,
        progress_callback: ProgressCallback | None = None,
    ) -> IndexResult:
        """
        Index a repository.

        Args:
            repo_path: Path to the repository
            incremental: If True, only index changed files
            progress_callback: Optional callback(current, total, file_path)

        Returns:
            IndexResult with statistics

        Requirements: REQ-IDX-001
        """
        import time

        from codegraph_mcp.core.parser import Entity, Relation

        start_time = time.time()

        result = IndexResult()
        repo_path = repo_path.resolve()

        # Initialize graph engine
        self._engine = GraphEngine(repo_path)
        await self._engine.initialize()

        # Batch accumulators
        all_entities: list[Entity] = []
        all_relations: list[Relation] = []
        file_updates: list[tuple[Path, ParseResult]] = []

        try:
            # Get files to index
            if incremental:
                # Check if index already exists (has entities)
                stats = await self._engine.get_statistics()
                if stats.entity_count == 0:
                    # No existing index - do full scan for initial indexing
                    files = self._get_all_files(repo_path)
                else:
                    # Existing index - only get changed files
                    files = await self._get_changed_files(repo_path)
            else:
                files = self._get_all_files(repo_path)

            total_files = len(files)

            # Parse each file and collect results
            for idx, file_path in enumerate(files):
                # Report progress
                if progress_callback:
                    progress_callback(idx, total_files, file_path)

                try:
                    parse_result = self.parser.parse_file(file_path)

                    if parse_result.success:
                        all_entities.extend(parse_result.entities)
                        all_relations.extend(parse_result.relations)
                        file_updates.append((file_path, parse_result))
                        result.entities_count += len(parse_result.entities)
                        result.relations_count += len(parse_result.relations)
                        # Track changed entity IDs for incremental community
                        result.changed_entity_ids.extend(
                            e.id for e in parse_result.entities
                        )

                    result.files_indexed += 1
                except Exception as e:
                    result.errors.append(f"{file_path}: {e}")

            # Batch write all entities and relations
            if self._engine:
                await self._engine.add_entities_batch(all_entities)
                await self._engine.add_relations_batch(all_relations)

                # Update file tracking in batch
                await self._update_files_batch(file_updates)

            # Final progress update
            if progress_callback:
                progress_callback(total_files, total_files, None)

            result.duration_seconds = time.time() - start_time

        finally:
            await self._engine.close()

        return result

    async def _update_files_batch(
        self,
        file_updates: list[tuple[Path, ParseResult]],
    ) -> None:
        """Update file tracking information in batch."""
        if not self._engine or not self._engine._connection:
            return
        if not file_updates:
            return

        data = []
        for file_path, parse_result in file_updates:
            content = file_path.read_bytes()
            file_hash = hashlib.sha256(content).hexdigest()
            language = self.parser.detect_language(file_path)
            data.append((
                str(file_path),
                language,
                file_hash,
                len(content),
                len(parse_result.entities),
            ))

        await self._engine._connection.executemany(
            """
            INSERT OR REPLACE INTO files
            (path, language, hash, size, entity_count, indexed_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            data,
        )
        await self._engine._connection.commit()

    async def _get_changed_files(self, repo_path: Path) -> list[Path]:
        """
        Get list of changed files using Git.

        Requirements: REQ-IDX-002
        """
        from codegraph_mcp.utils.git import ChangeType, GitOperations

        try:
            git_ops = GitOperations(repo_path)
            changes = await git_ops.get_changed_files()

            # Get supported extensions
            supported_extensions = set(self.parser.LANGUAGE_EXTENSIONS.keys())

            # Filter to supported file types (excluding deleted files)
            changed_files = []
            for change in changes:
                if change.change_type == ChangeType.DELETED:
                    # Handle deleted files - remove from graph
                    await self._handle_deleted_file(repo_path / change.path)
                    continue

                full_path = repo_path / change.path
                if full_path.suffix.lower() in supported_extensions:
                    changed_files.append(full_path)

            return changed_files
        except ValueError:
            # Not a git repository - fall back to full scan
            return self._get_all_files(repo_path)

    async def _handle_deleted_file(self, file_path: Path) -> None:
        """Handle a deleted file by removing its entities from the graph."""
        if self._engine:
            await self._engine.delete_file_entities(file_path)

    def _get_all_files(self, repo_path: Path) -> list[Path]:
        """Get all supported files in repository."""
        files: list[Path] = []
        supported_extensions = set(self.parser.LANGUAGE_EXTENSIONS.keys())

        # Default exclude patterns
        exclude_dirs = {
            ".git", "node_modules", "__pycache__", "venv",
            ".venv", "target", "dist", "build", ".codegraph",
        }

        for path in repo_path.rglob("*"):
            if path.is_file():
                # Check if in excluded directory
                if any(ex in path.parts for ex in exclude_dirs):
                    continue

                if path.suffix.lower() in supported_extensions:
                    files.append(path)

        return files

    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()
