"""
SQLite Storage Module

SQLite-based storage for graph data with async support.

Requirements: REQ-STR-001, REQ-GRF-005
Design Reference: design-storage.md §2
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import aiosqlite


class SQLiteStorage:
    """
    Async SQLite storage backend.

    Requirements: REQ-STR-001
    Design Reference: design-storage.md §2

    Usage:
        storage = SQLiteStorage(Path(".codegraph/graph.db"))
        async with storage.connection() as conn:
            await conn.execute("SELECT * FROM entities")
    """

    def __init__(self, db_path: Path) -> None:
        """
        Initialize SQLite storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Initialize database and create schema."""
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = await aiosqlite.connect(self.db_path)

        # Enable foreign keys
        await self._connection.execute("PRAGMA foreign_keys = ON")

        # Create schema
        await self._create_schema()

    async def _create_schema(self) -> None:
        """Create database schema."""
        schema_sql = """
        -- Entities table
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

        -- Relations table
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

        -- Communities table
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

        -- Files table
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            language TEXT,
            hash TEXT NOT NULL,
            size INTEGER,
            entity_count INTEGER DEFAULT 0,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Indexes
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

        for statement in schema_sql.split(";"):
            statement = statement.strip()
            if statement:
                await self._connection.execute(statement)

        await self._connection.commit()

    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[aiosqlite.Connection]:
        """Get database connection context."""
        if self._connection is None:
            await self.initialize()
        yield self._connection

    async def execute(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
    ) -> aiosqlite.Cursor:
        """Execute SQL statement."""
        if self._connection is None:
            await self.initialize()

        if params:
            return await self._connection.execute(sql, params)
        return await self._connection.execute(sql)

    async def execute_many(
        self,
        sql: str,
        params_list: list[tuple[Any, ...]],
    ) -> None:
        """Execute SQL statement with multiple parameter sets."""
        if self._connection is None:
            await self.initialize()

        await self._connection.executemany(sql, params_list)
        await self._connection.commit()

    async def fetch_one(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
    ) -> tuple[Any, ...] | None:
        """Fetch single row."""
        cursor = await self.execute(sql, params)
        return await cursor.fetchone()

    async def fetch_all(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
    ) -> list[tuple[Any, ...]]:
        """Fetch all rows."""
        cursor = await self.execute(sql, params)
        return await cursor.fetchall()

    async def commit(self) -> None:
        """Commit transaction."""
        if self._connection:
            await self._connection.commit()

    async def vacuum(self) -> None:
        """Optimize database."""
        if self._connection:
            await self._connection.execute("VACUUM")

    async def get_table_stats(self) -> dict[str, int]:
        """Get row counts for all tables."""
        stats = {}
        tables = ["entities", "relations", "communities", "files"]

        for table in tables:
            cursor = await self.execute(f"SELECT COUNT(*) FROM {table}")
            row = await cursor.fetchone()
            stats[table] = row[0] if row else 0

        return stats
