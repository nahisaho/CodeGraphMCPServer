"""
JavaScript Extractor Unit Tests

Tests for JavaScript language extraction.

Task: TASK-052
"""


import pytest

from codegraph_mcp.languages.javascript import JavaScriptExtractor


class TestJavaScriptExtractor:
    """Test JavaScript-specific extraction configuration."""

    @pytest.fixture
    def extractor(self) -> JavaScriptExtractor:
        """Create JavaScript extractor instance."""
        return JavaScriptExtractor()

    def test_extractor_config(self, extractor: JavaScriptExtractor) -> None:
        """Test extractor configuration."""
        assert extractor.config.name == "javascript"
        assert ".js" in extractor.config.extensions
        assert ".jsx" in extractor.config.extensions
        assert ".mjs" in extractor.config.extensions
        assert ".cjs" in extractor.config.extensions
        assert extractor.config.tree_sitter_name == "javascript"

    def test_function_nodes_config(self, extractor: JavaScriptExtractor) -> None:
        """Test function node types configuration."""
        assert "function_declaration" in extractor.config.function_nodes
        assert "function_expression" in extractor.config.function_nodes
        assert "arrow_function" in extractor.config.function_nodes
        assert "method_definition" in extractor.config.function_nodes
        assert "generator_function_declaration" in extractor.config.function_nodes

    def test_class_nodes_config(self, extractor: JavaScriptExtractor) -> None:
        """Test class node types configuration."""
        assert "class_declaration" in extractor.config.class_nodes

    def test_import_nodes_config(self, extractor: JavaScriptExtractor) -> None:
        """Test import node types configuration."""
        assert "import_statement" in extractor.config.import_nodes

    def test_no_interface_nodes(self, extractor: JavaScriptExtractor) -> None:
        """Test that JavaScript has no interface nodes (not TypeScript)."""
        assert len(extractor.config.interface_nodes) == 0

    def test_extractor_inherits_base(self, extractor: JavaScriptExtractor) -> None:
        """Test that extractor inherits from BaseExtractor."""
        from codegraph_mcp.languages.config import BaseExtractor
        assert isinstance(extractor, BaseExtractor)

    def test_extractor_has_extract_method(self, extractor: JavaScriptExtractor) -> None:
        """Test that extractor has extract method."""
        assert hasattr(extractor, "extract")
        assert callable(extractor.extract)

    def test_extractor_has_helper_methods(self, extractor: JavaScriptExtractor) -> None:
        """Test that extractor has expected helper methods."""
        assert hasattr(extractor, "_walk_tree")
        assert hasattr(extractor, "_extract_function")
        assert hasattr(extractor, "_extract_class")
        assert hasattr(extractor, "_extract_method")
        assert hasattr(extractor, "_extract_import")
        assert hasattr(extractor, "_extract_calls")


class TestJavaScriptExtractorRegistration:
    """Test JavaScript extractor registration."""

    def test_extractor_is_registered(self) -> None:
        """Test that JavaScript extractor is registered."""
        from codegraph_mcp.languages.config import get_extractor
        extractor = get_extractor("javascript")
        assert extractor is not None
        assert isinstance(extractor, JavaScriptExtractor)

    def test_extractor_in_all_exports(self) -> None:
        """Test that JavaScript extractor is in __all__."""
        from codegraph_mcp import languages
        assert "JavaScriptExtractor" in languages.__all__
