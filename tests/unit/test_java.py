"""
Java Language Extractor Tests

Tests for Java AST parsing and entity extraction.
"""

from pathlib import Path

import pytest

from codegraph_mcp.core.parser import EntityType, RelationType


# Fixture path
JAVA_FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "java" / "Calculator.java"


class TestJavaExtractor:
    """Test Java language extractor."""

    @pytest.fixture
    def java_source(self) -> str:
        """Load Java fixture source code."""
        return JAVA_FIXTURE_PATH.read_text()

    @pytest.fixture
    def parse_result(self, java_source: str):
        """Parse Java fixture and return result."""
        try:
            import tree_sitter_java as ts_java
        except ImportError:
            pytest.skip("tree-sitter-java not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.java import JavaExtractor

        # Initialize parser
        java_lang = ts.Language(ts_java.language())
        parser = ts.Parser(java_lang)

        # Parse source
        tree = parser.parse(java_source.encode())

        # Extract entities
        extractor = JavaExtractor()
        return extractor.extract(tree, JAVA_FIXTURE_PATH, java_source)

    def test_module_entity_created(self, parse_result):
        """Test that module entity is created for the file."""
        modules = [e for e in parse_result.entities if e.type == EntityType.MODULE]
        assert len(modules) == 1
        assert modules[0].name == "Calculator"

    def test_class_extraction(self, parse_result):
        """Test class extraction."""
        classes = [e for e in parse_result.entities if e.type == EntityType.CLASS]
        class_names = {c.name for c in classes}

        assert "Calculator" in class_names
        assert "AddOperation" in class_names

    def test_interface_extraction(self, parse_result):
        """Test interface extraction."""
        interfaces = [e for e in parse_result.entities if e.type == EntityType.INTERFACE]
        interface_names = {i.name for i in interfaces}

        assert "Operation" in interface_names

    def test_enum_extraction(self, parse_result):
        """Test enum extraction."""
        enums = [e for e in parse_result.entities if e.type == EntityType.ENUM]
        enum_names = {e.name for e in enums}

        assert "OperationType" in enum_names

    def test_method_extraction(self, parse_result):
        """Test method extraction."""
        methods = [e for e in parse_result.entities if e.type == EntityType.METHOD]
        method_names = {m.name for m in methods}

        # Calculator methods
        assert "add" in method_names
        assert "subtract" in method_names
        assert "multiply" in method_names
        assert "divide" in method_names
        assert "getMemory" in method_names
        assert "getHistory" in method_names
        assert "clear" in method_names

        # Interface methods
        assert "execute" in method_names
        assert "getName" in method_names

    def test_constructor_extraction(self, parse_result):
        """Test constructor extraction."""
        methods = [e for e in parse_result.entities if e.type == EntityType.METHOD]

        # Constructor should be extracted
        constructor = next((m for m in methods if "Calculator" in m.name and "init" in m.qualified_name), None)
        assert constructor is not None

    def test_import_relations(self, parse_result):
        """Test import relation extraction."""
        imports = [r for r in parse_result.relations if r.type == RelationType.IMPORTS]
        import_targets = {r.target_id for r in imports}

        assert any("java.util.List" in t for t in import_targets)
        assert any("java.util.ArrayList" in t for t in import_targets)

    def test_implements_relation(self, parse_result):
        """Test implements relation extraction."""
        implements = [r for r in parse_result.relations if r.type == RelationType.IMPLEMENTS]

        # AddOperation implements Operation
        assert any("Operation" in r.target_id for r in implements)

    def test_call_relations(self, parse_result):
        """Test method call relation extraction."""
        calls = [r for r in parse_result.relations if r.type == RelationType.CALLS]

        # Should have calls to storeResult, etc.
        call_targets = {r.target_id for r in calls}
        assert any("storeResult" in t for t in call_targets)

    def test_contains_relations(self, parse_result):
        """Test that contains relations link properly."""
        contains = [r for r in parse_result.relations if r.type == RelationType.CONTAINS]

        # Should have contains relations
        assert len(contains) > 0

    def test_method_signature(self, parse_result):
        """Test method signature extraction."""
        methods = [e for e in parse_result.entities if e.type == EntityType.METHOD]

        add_method = next((m for m in methods if m.name == "add"), None)
        assert add_method is not None
        assert add_method.signature is not None
        assert "double" in add_method.signature

    def test_entity_locations(self, parse_result):
        """Test that entities have valid locations."""
        for entity in parse_result.entities:
            assert entity.location is not None
            assert entity.location.start_line > 0
            assert entity.location.end_line >= entity.location.start_line


class TestJavaExtractorEdgeCases:
    """Test edge cases for Java extractor."""

    def test_empty_class(self):
        """Test parsing empty Java class."""
        try:
            import tree_sitter_java as ts_java
        except ImportError:
            pytest.skip("tree-sitter-java not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.java import JavaExtractor

        java_lang = ts.Language(ts_java.language())
        parser = ts.Parser(java_lang)

        source = "public class Empty {}\n"
        tree = parser.parse(source.encode())

        extractor = JavaExtractor()
        result = extractor.extract(tree, Path("Empty.java"), source)

        classes = [e for e in result.entities if e.type == EntityType.CLASS]
        assert len(classes) == 1
        assert classes[0].name == "Empty"

    def test_nested_class(self):
        """Test parsing nested class."""
        try:
            import tree_sitter_java as ts_java
        except ImportError:
            pytest.skip("tree-sitter-java not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.java import JavaExtractor

        java_lang = ts.Language(ts_java.language())
        parser = ts.Parser(java_lang)

        source = '''
public class Outer {
    public class Inner {
        public void innerMethod() {}
    }
}
'''
        tree = parser.parse(source.encode())

        extractor = JavaExtractor()
        result = extractor.extract(tree, Path("Outer.java"), source)

        classes = [e for e in result.entities if e.type == EntityType.CLASS]
        class_names = {c.name for c in classes}

        assert "Outer" in class_names
        assert "Inner" in class_names

    def test_abstract_class_with_extends(self):
        """Test abstract class with extends."""
        try:
            import tree_sitter_java as ts_java
        except ImportError:
            pytest.skip("tree-sitter-java not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.java import JavaExtractor

        java_lang = ts.Language(ts_java.language())
        parser = ts.Parser(java_lang)

        source = '''
abstract class Base {
    abstract void doSomething();
}

class Derived extends Base {
    void doSomething() {}
}
'''
        tree = parser.parse(source.encode())

        extractor = JavaExtractor()
        result = extractor.extract(tree, Path("Test.java"), source)

        # Check inheritance relation
        inherits = [r for r in result.relations if r.type == RelationType.INHERITS]
        assert any("Base" in r.target_id for r in inherits)
