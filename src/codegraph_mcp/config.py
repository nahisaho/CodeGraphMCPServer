"""
Configuration Management Module

Provides centralized configuration management for CodeGraph MCP Server.
Supports environment variables, configuration files, and programmatic configuration.

Design Reference: design-core-engine.md §5
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class StorageConfig:
    """Storage layer configuration."""

    # SQLite database path (relative to repo or absolute)
    db_path: str = ".codegraph/graph.db"

    # Cache settings
    cache_enabled: bool = True
    cache_max_size_mb: int = 100
    cache_ttl_seconds: int = 3600

    # Vector store settings
    vector_enabled: bool = True
    vector_dimensions: int = 384  # MiniLM default


@dataclass
class ParserConfig:
    """AST parser configuration."""

    # Supported languages
    languages: list[str] = field(default_factory=lambda: ["python", "typescript", "rust"])

    # File size limit (bytes)
    max_file_size: int = 1_000_000  # 1MB

    # Timeout for parsing single file (seconds)
    parse_timeout: float = 30.0

    # Include/exclude patterns
    include_patterns: list[str] = field(default_factory=lambda: ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.rs"])
    exclude_patterns: list[str] = field(default_factory=lambda: [
        "**/node_modules/**",
        "**/.git/**",
        "**/venv/**",
        "**/__pycache__/**",
        "**/target/**",
        "**/dist/**",
        "**/build/**",
    ])


@dataclass
class GraphConfig:
    """Graph engine configuration."""

    # Community detection
    community_algorithm: str = "louvain"
    community_resolution: float = 1.0
    min_community_size: int = 3

    # Query settings
    max_query_depth: int = 10
    max_results: int = 100


@dataclass
class SemanticConfig:
    """Semantic analysis configuration."""

    # Embedding model
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_batch_size: int = 32

    # LLM settings for descriptions (optional)
    llm_enabled: bool = False
    llm_model: str = ""
    llm_api_key: str = ""


@dataclass
class ServerConfig:
    """MCP server configuration."""

    # Server info
    name: str = "codegraph-mcp"
    version: str = "0.1.0"

    # Transport settings
    default_transport: str = "stdio"
    sse_port: int = 8080

    # Request limits
    max_concurrent_requests: int = 10
    request_timeout: float = 60.0


@dataclass
class Config:
    """
    Main configuration class for CodeGraph MCP Server.

    Usage:
        config = Config(repo_path=Path("/path/to/repo"))
        config = Config.from_file(Path("codegraph.toml"))
        config = Config.from_env()
    """

    # Required: Repository path
    repo_path: Path = field(default_factory=Path.cwd)

    # Sub-configurations
    storage: StorageConfig = field(default_factory=StorageConfig)
    parser: ParserConfig = field(default_factory=ParserConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)
    semantic: SemanticConfig = field(default_factory=SemanticConfig)
    server: ServerConfig = field(default_factory=ServerConfig)

    # Logging
    log_level: str = "INFO"
    log_file: str | None = None

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        if isinstance(self.repo_path, str):
            self.repo_path = Path(self.repo_path)
        self.repo_path = self.repo_path.resolve()

    @property
    def db_path(self) -> Path:
        """Get absolute path to SQLite database."""
        db = Path(self.storage.db_path)
        if db.is_absolute():
            return db
        return self.repo_path / db

    @property
    def codegraph_dir(self) -> Path:
        """Get .codegraph directory path."""
        return self.repo_path / ".codegraph"

    @classmethod
    def from_env(cls) -> "Config":
        """
        Create configuration from environment variables.

        Environment variables:
            CODEGRAPH_REPO_PATH: Repository path
            CODEGRAPH_LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR)
            CODEGRAPH_DB_PATH: Database path
            CODEGRAPH_CACHE_ENABLED: Enable cache (true/false)
        """
        config = cls()

        if repo_path := os.getenv("CODEGRAPH_REPO_PATH"):
            config.repo_path = Path(repo_path)

        if log_level := os.getenv("CODEGRAPH_LOG_LEVEL"):
            config.log_level = log_level.upper()

        if db_path := os.getenv("CODEGRAPH_DB_PATH"):
            config.storage.db_path = db_path

        if cache := os.getenv("CODEGRAPH_CACHE_ENABLED"):
            config.storage.cache_enabled = cache.lower() in ("true", "1", "yes")

        return config

    @classmethod
    def from_file(cls, path: Path) -> "Config":
        """
        Load configuration from a TOML file.

        Args:
            path: Path to configuration file

        Returns:
            Config instance
        """
        import tomllib

        with open(path, "rb") as f:
            data = tomllib.load(f)

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Config":
        """Create configuration from dictionary."""
        config = cls()

        if "repo_path" in data:
            config.repo_path = Path(data["repo_path"])

        if "log_level" in data:
            config.log_level = data["log_level"]

        if "storage" in data:
            storage = data["storage"]
            if "db_path" in storage:
                config.storage.db_path = storage["db_path"]
            if "cache_enabled" in storage:
                config.storage.cache_enabled = storage["cache_enabled"]
            if "cache_max_size_mb" in storage:
                config.storage.cache_max_size_mb = storage["cache_max_size_mb"]

        if "parser" in data:
            parser = data["parser"]
            if "languages" in parser:
                config.parser.languages = parser["languages"]
            if "max_file_size" in parser:
                config.parser.max_file_size = parser["max_file_size"]
            if "include_patterns" in parser:
                config.parser.include_patterns = parser["include_patterns"]
            if "exclude_patterns" in parser:
                config.parser.exclude_patterns = parser["exclude_patterns"]

        return config

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "repo_path": str(self.repo_path),
            "log_level": self.log_level,
            "storage": {
                "db_path": self.storage.db_path,
                "cache_enabled": self.storage.cache_enabled,
                "cache_max_size_mb": self.storage.cache_max_size_mb,
            },
            "parser": {
                "languages": self.parser.languages,
                "max_file_size": self.parser.max_file_size,
                "include_patterns": self.parser.include_patterns,
                "exclude_patterns": self.parser.exclude_patterns,
            },
        }
