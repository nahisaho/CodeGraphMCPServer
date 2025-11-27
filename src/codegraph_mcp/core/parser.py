"""
AST Parser Module

Tree-sitter based AST parsing for extracting code entities and relations.

Requirements: REQ-AST-001 ~ REQ-AST-005
Design Reference: design-core-engine.md §2.1
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class EntityType(str, Enum):
    """Types of code entities."""

    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    INTERFACE = "interface"  # TypeScript
    TYPE_ALIAS = "type_alias"
    STRUCT = "struct"  # Rust
    TRAIT = "trait"  # Rust
    ENUM = "enum"


class RelationType(str, Enum):
    """Types of relations between entities."""

    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    USES = "uses"
    CONTAINS = "contains"
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"


@dataclass
class Location:
    """Source code location."""

    file_path: Path
    start_line: int
    start_column: int
    end_line: int
    end_column: int

    def __str__(self) -> str:
        return f"{self.file_path}:{self.start_line}:{self.start_column}"


@dataclass
class Entity:
    """
    Represents a code entity (function, class, module, etc.).

    Requirements: REQ-GRF-003
    """

    id: str
    type: EntityType
    name: str
    qualified_name: str
    location: Location
    signature: str | None = None
    docstring: str | None = None
    source_code: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def file_path(self) -> Path:
        return self.location.file_path

    @property
    def start_line(self) -> int:
        return self.location.start_line

    @property
    def end_line(self) -> int:
        return self.location.end_line


@dataclass
class Relation:
    """
    Represents a relation between two entities.

    Requirements: REQ-GRF-004
    """

    source_id: str
    target_id: str
    type: RelationType
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParseError:
    """Represents a parsing error."""

    file_path: Path
    line: int
    column: int
    message: str
    severity: str = "error"


@dataclass
class ParseResult:
    """
    Result of parsing a file or set of files.

    Requirements: REQ-AST-004
    """

    entities: list[Entity] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)
    errors: list[ParseError] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def merge(self, other: "ParseResult") -> "ParseResult":
        """Merge another parse result into this one."""
        return ParseResult(
            entities=self.entities + other.entities,
            relations=self.relations + other.relations,
            errors=self.errors + other.errors,
        )


class ASTParser:
    """
    Tree-sitter based AST parser.

    Extracts code entities and relations from source files.

    Requirements: REQ-AST-001 ~ REQ-AST-005
    Design Reference: design-core-engine.md §2.1

    Usage:
        parser = ASTParser()
        result = parser.parse_file(Path("example.py"))

        for entity in result.entities:
            print(f"{entity.type}: {entity.name}")
    """

    # Language extension mappings
    LANGUAGE_EXTENSIONS: dict[str, str] = {
        ".py": "python",
        ".pyi": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".rs": "rust",
        ".c": "cpp",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".h": "cpp",
        ".hpp": "cpp",
        ".hxx": "cpp",
    }

    def __init__(self) -> None:
        """Initialize the parser."""
        self._parsers: dict[str, Any] = {}
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Lazily initialize tree-sitter parsers."""
        if self._initialized:
            return

        try:
            import tree_sitter_cpp
            import tree_sitter_python
            import tree_sitter_rust
            import tree_sitter_typescript
            from tree_sitter import Language, Parser

            # Initialize parsers for each language
            self._parsers["python"] = Parser(
                Language(tree_sitter_python.language())
            )
            self._parsers["typescript"] = Parser(
                Language(tree_sitter_typescript.language_typescript())
            )
            self._parsers["rust"] = Parser(
                Language(tree_sitter_rust.language())
            )
            self._parsers["cpp"] = Parser(
                Language(tree_sitter_cpp.language())
            )

            self._initialized = True
        except ImportError as e:
            raise ImportError(
                f"Tree-sitter language bindings not installed: {e}. "
                "Install with: pip install tree-sitter-python tree-sitter-typescript tree-sitter-rust tree-sitter-cpp"
            )

    def detect_language(self, file_path: Path) -> str | None:
        """
        Detect language from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Language name or None if not supported
        """
        return self.LANGUAGE_EXTENSIONS.get(file_path.suffix.lower())

    def parse_file(self, file_path: Path, language: str | None = None) -> ParseResult:
        """
        Parse a single file and extract entities and relations.

        Args:
            file_path: Path to the file to parse
            language: Language name (auto-detected if not provided)

        Returns:
            ParseResult with entities and relations

        Requirements: REQ-AST-001, REQ-AST-004
        """
        self._ensure_initialized()

        if language is None:
            language = self.detect_language(file_path)

        if language is None:
            return ParseResult(
                errors=[ParseError(
                    file_path=file_path,
                    line=0,
                    column=0,
                    message=f"Unsupported file type: {file_path.suffix}",
                )]
            )

        if language not in self._parsers:
            return ParseResult(
                errors=[ParseError(
                    file_path=file_path,
                    line=0,
                    column=0,
                    message=f"No parser available for language: {language}",
                )]
            )

        try:
            content = file_path.read_bytes()
            parser = self._parsers[language]
            tree = parser.parse(content)

            # Delegate to language-specific extraction
            from codegraph_mcp.languages import get_extractor
            extractor = get_extractor(language)
            return extractor.extract(tree, file_path, content.decode("utf-8"))

        except Exception as e:
            return ParseResult(
                errors=[ParseError(
                    file_path=file_path,
                    line=0,
                    column=0,
                    message=str(e),
                )]
            )

    def parse_files(self, file_paths: list[Path]) -> ParseResult:
        """
        Parse multiple files.

        Args:
            file_paths: List of file paths to parse

        Returns:
            Merged ParseResult
        """
        result = ParseResult()
        for path in file_paths:
            result = result.merge(self.parse_file(path))
        return result
