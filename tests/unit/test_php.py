"""
PHP Language Extractor Tests

Tests for PHP AST parsing and entity extraction.
"""

from pathlib import Path

import pytest

from codegraph_mcp.core.parser import EntityType, RelationType


# Fixture path
PHP_FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "php" / "calculator.php"


class TestPHPExtractor:
    """Test PHP language extractor."""

    @pytest.fixture
    def php_source(self) -> str:
        """Load PHP fixture source code."""
        return PHP_FIXTURE_PATH.read_text()

    @pytest.fixture
    def parse_result(self, php_source: str):
        """Parse PHP fixture and return result."""
        try:
            import tree_sitter_php as ts_php
        except ImportError:
            pytest.skip("tree-sitter-php not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.php import PHPExtractor

        # Initialize parser
        php_lang = ts.Language(ts_php.language_php())
        parser = ts.Parser(php_lang)

        # Parse source
        tree = parser.parse(php_source.encode())

        # Extract entities
        extractor = PHPExtractor()
        return extractor.extract(tree, PHP_FIXTURE_PATH, php_source)

    def test_module_entity_created(self, parse_result):
        """Test that module entity is created for the file."""
        modules = [e for e in parse_result.entities if e.type == EntityType.MODULE]
        assert len(modules) >= 1

    def test_class_extraction(self, parse_result):
        """Test class extraction."""
        classes = [e for e in parse_result.entities if e.type == EntityType.CLASS]
        class_names = {c.name for c in classes}

        assert "Calculator" in class_names
        assert "AdvancedCalculator" in class_names

    def test_interface_extraction(self, parse_result):
        """Test interface extraction."""
        interfaces = [e for e in parse_result.entities if e.type == EntityType.INTERFACE]
        interface_names = {i.name for i in interfaces}

        assert "CalculatorInterface" in interface_names

    def test_trait_extraction(self, parse_result):
        """Test trait extraction."""
        traits = [e for e in parse_result.entities if e.type == EntityType.TRAIT]
        trait_names = {t.name for t in traits}

        assert "Loggable" in trait_names

    def test_method_extraction(self, parse_result):
        """Test method extraction."""
        methods = [e for e in parse_result.entities if e.type == EntityType.METHOD]
        method_names = {m.name for m in methods}

        assert "add" in method_names
        assert "subtract" in method_names
        assert "multiply" in method_names
        assert "divide" in method_names

    def test_function_extraction(self, parse_result):
        """Test function extraction."""
        functions = [e for e in parse_result.entities if e.type == EntityType.FUNCTION]
        func_names = {f.name for f in functions}

        assert "createCalculator" in func_names

    def test_inheritance_relations(self, parse_result):
        """Test inheritance relation extraction."""
        inherits = [r for r in parse_result.relations if r.type == RelationType.INHERITS]

        # AdvancedCalculator extends Calculator
        assert any("Calculator" in r.target_id for r in inherits)

    def test_implements_relations(self, parse_result):
        """Test implements relation extraction."""
        implements = [r for r in parse_result.relations if r.type == RelationType.IMPLEMENTS]

        # Calculator implements CalculatorInterface
        assert any("CalculatorInterface" in r.target_id for r in implements)

    def test_contains_relations(self, parse_result):
        """Test that contains relations link classes to methods."""
        contains = [r for r in parse_result.relations if r.type == RelationType.CONTAINS]
        assert len(contains) > 0

    def test_entity_locations(self, parse_result):
        """Test that entities have valid locations."""
        for entity in parse_result.entities:
            assert entity.location is not None
            assert entity.location.start_line > 0
            assert entity.location.end_line >= entity.location.start_line


class TestPHPExtractorEdgeCases:
    """Test edge cases for PHP extractor."""

    def test_empty_file(self):
        """Test parsing empty PHP file."""
        try:
            import tree_sitter_php as ts_php
        except ImportError:
            pytest.skip("tree-sitter-php not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.php import PHPExtractor

        php_lang = ts.Language(ts_php.language_php())
        parser = ts.Parser(php_lang)

        source = "<?php\n"
        tree = parser.parse(source.encode())

        extractor = PHPExtractor()
        result = extractor.extract(tree, Path("empty.php"), source)

        # Should have module entity
        assert len(result.entities) >= 1

    def test_single_class(self):
        """Test file with single class."""
        try:
            import tree_sitter_php as ts_php
        except ImportError:
            pytest.skip("tree-sitter-php not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.php import PHPExtractor

        php_lang = ts.Language(ts_php.language_php())
        parser = ts.Parser(php_lang)

        source = '''<?php
class HelloWorld {
    public function greet() {
        echo "Hello!";
    }
}
'''
        tree = parser.parse(source.encode())

        extractor = PHPExtractor()
        result = extractor.extract(tree, Path("hello.php"), source)

        classes = [e for e in result.entities if e.type == EntityType.CLASS]
        assert len(classes) == 1
        assert classes[0].name == "HelloWorld"

    def test_namespaced_class(self):
        """Test class with namespace."""
        try:
            import tree_sitter_php as ts_php
        except ImportError:
            pytest.skip("tree-sitter-php not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.php import PHPExtractor

        php_lang = ts.Language(ts_php.language_php())
        parser = ts.Parser(php_lang)

        source = '''<?php
namespace App\\Models;

class User {
    private string $name;
}
'''
        tree = parser.parse(source.encode())

        extractor = PHPExtractor()
        result = extractor.extract(tree, Path("User.php"), source)

        classes = [e for e in result.entities if e.type == EntityType.CLASS]
        assert len(classes) == 1
        assert classes[0].name == "User"

    def test_abstract_class(self):
        """Test abstract class extraction."""
        try:
            import tree_sitter_php as ts_php
        except ImportError:
            pytest.skip("tree-sitter-php not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.php import PHPExtractor

        php_lang = ts.Language(ts_php.language_php())
        parser = ts.Parser(php_lang)

        source = '''<?php
abstract class BaseController {
    abstract public function handle();

    public function respond() {
        return "OK";
    }
}
'''
        tree = parser.parse(source.encode())

        extractor = PHPExtractor()
        result = extractor.extract(tree, Path("base.php"), source)

        classes = [e for e in result.entities if e.type == EntityType.CLASS]
        assert len(classes) == 1
        assert classes[0].name == "BaseController"

    def test_static_method(self):
        """Test static method extraction."""
        try:
            import tree_sitter_php as ts_php
        except ImportError:
            pytest.skip("tree-sitter-php not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.php import PHPExtractor

        php_lang = ts.Language(ts_php.language_php())
        parser = ts.Parser(php_lang)

        source = '''<?php
class Factory {
    public static function create(): self {
        return new self();
    }
}
'''
        tree = parser.parse(source.encode())

        extractor = PHPExtractor()
        result = extractor.extract(tree, Path("factory.php"), source)

        methods = [e for e in result.entities if e.type == EntityType.METHOD]
        assert len(methods) == 1
        assert methods[0].name == "create"
