"""
Language Configuration Module

Base classes and utilities for language-specific extraction.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from codegraph_mcp.core.parser import ParseResult


@dataclass
class LanguageConfig:
    """Configuration for a supported language."""

    name: str
    extensions: list[str]
    tree_sitter_name: str

    # Node types to extract as entities
    function_nodes: list[str]
    class_nodes: list[str]
    import_nodes: list[str]

    # Optional node types
    interface_nodes: list[str] | None = None
    module_nodes: list[str] | None = None


class BaseExtractor(ABC):
    """
    Base class for language-specific entity extraction.

    Subclasses implement language-specific extraction logic.
    """

    config: LanguageConfig

    # Store source as bytes for correct byte offset slicing
    _source_bytes: bytes = b""

    @abstractmethod
    def extract(
        self,
        tree: Any,
        file_path: Path,
        source_code: str,
    ) -> ParseResult:
        """
        Extract entities and relations from an AST.

        Args:
            tree: Tree-sitter parse tree
            file_path: Path to the source file
            source_code: Original source code

        Returns:
            ParseResult with entities and relations
        """
        pass

    def _set_source(self, source_code: str) -> None:
        """Set source code and cache bytes for correct offset handling."""
        self._source_bytes = source_code.encode("utf-8")

    def _generate_entity_id(
        self,
        file_path: Path,
        name: str,
        line: int,
    ) -> str:
        """Generate unique entity ID."""
        return f"{file_path}::{name}::{line}"

    def _get_node_text(self, node: Any, source_code: str) -> str:
        """Get text content of a node using byte offsets."""
        # Use cached bytes for correct slicing with byte offsets
        if self._source_bytes:
            return self._source_bytes[node.start_byte:node.end_byte].decode("utf-8")
        # Fallback (may be incorrect for non-ASCII)
        return source_code[node.start_byte:node.end_byte]

    def _get_docstring(self, node: Any, source_code: str) -> str | None:
        """Extract docstring from a node if present."""
        # Check first child for string literal (common docstring pattern)
        if node.child_count > 0:
            body = None
            for child in node.children:
                if child.type in {"block", "statement_block"}:
                    body = child
                    break

            if body and body.child_count > 0:
                first_stmt = body.children[0]
                if first_stmt.type in ("expression_statement", "string"):
                    string_node = first_stmt
                    if first_stmt.type == "expression_statement":
                        string_node = first_stmt.children[0] if first_stmt.child_count > 0 else None

                    if string_node and string_node.type == "string":
                        text = self._get_node_text(string_node, source_code)
                        # Strip quotes
                        if text.startswith('"""') or text.startswith("'''"):
                            return text[3:-3].strip()
                        elif text.startswith('"') or text.startswith("'"):
                            return text[1:-1].strip()

        return None


# Registry of extractors
_extractors: dict[str, type[BaseExtractor]] = {}


def register_extractor(language: str, extractor_class: type[BaseExtractor]) -> None:
    """Register an extractor for a language."""
    _extractors[language] = extractor_class


def get_extractor(language: str) -> BaseExtractor:
    """Get extractor instance for a language."""
    if language not in _extractors:
        raise ValueError(f"No extractor registered for language: {language}")
    return _extractors[language]()
