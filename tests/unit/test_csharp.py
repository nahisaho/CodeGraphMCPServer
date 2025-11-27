"""
C# Language Extractor Tests

Tests for C# AST parsing and entity extraction.
"""

from pathlib import Path

import pytest

from codegraph_mcp.core.parser import EntityType, RelationType


# Fixture path
CSHARP_FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "csharp" / "Calculator.cs"


class TestCSharpExtractor:
    """Test C# language extractor."""

    @pytest.fixture
    def csharp_source(self) -> str:
        """Load C# fixture source code."""
        return CSHARP_FIXTURE_PATH.read_text()

    @pytest.fixture
    def parse_result(self, csharp_source: str):
        """Parse C# fixture and return result."""
        try:
            import tree_sitter_c_sharp as ts_csharp
        except ImportError:
            pytest.skip("tree-sitter-c-sharp not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.csharp import CSharpExtractor

        # Initialize parser
        csharp_lang = ts.Language(ts_csharp.language())
        parser = ts.Parser(csharp_lang)

        # Parse source
        tree = parser.parse(csharp_source.encode())

        # Extract entities
        extractor = CSharpExtractor()
        return extractor.extract(tree, CSHARP_FIXTURE_PATH, csharp_source)

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

        assert "ICalculator" in interface_names

    def test_struct_extraction(self, parse_result):
        """Test struct extraction."""
        structs = [e for e in parse_result.entities if e.type == EntityType.STRUCT]
        struct_names = {s.name for s in structs}

        assert "Point" in struct_names

    def test_enum_extraction(self, parse_result):
        """Test enum extraction."""
        enums = [e for e in parse_result.entities if e.type == EntityType.ENUM]
        enum_names = {e.name for e in enums}

        assert "Operation" in enum_names

    def test_method_extraction(self, parse_result):
        """Test method extraction."""
        methods = [e for e in parse_result.entities if e.type == EntityType.METHOD]
        method_names = {m.name for m in methods}

        assert "Add" in method_names
        assert "Subtract" in method_names
        assert "Multiply" in method_names
        assert "Divide" in method_names

    def test_constructor_extraction(self, parse_result):
        """Test constructor extraction."""
        methods = [e for e in parse_result.entities if e.type == EntityType.METHOD]
        # Constructor should be named after the class
        assert any("Calculator" in m.name or "Point" in m.name for m in methods)

    def test_inheritance_relations(self, parse_result):
        """Test inheritance relation extraction."""
        inherits = [r for r in parse_result.relations if r.type == RelationType.INHERITS]

        # AdvancedCalculator inherits from Calculator
        assert any("Calculator" in r.target_id for r in inherits)

    def test_import_relations(self, parse_result):
        """Test using directive extraction."""
        imports = [r for r in parse_result.relations if r.type == RelationType.IMPORTS]
        import_targets = {r.target_id for r in imports}

        assert any("System" in t for t in import_targets)

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


class TestCSharpExtractorEdgeCases:
    """Test edge cases for C# extractor."""

    def test_empty_file(self):
        """Test parsing empty C# file."""
        try:
            import tree_sitter_c_sharp as ts_csharp
        except ImportError:
            pytest.skip("tree-sitter-c-sharp not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.csharp import CSharpExtractor

        csharp_lang = ts.Language(ts_csharp.language())
        parser = ts.Parser(csharp_lang)

        source = "// Empty file\n"
        tree = parser.parse(source.encode())

        extractor = CSharpExtractor()
        result = extractor.extract(tree, Path("empty.cs"), source)

        # Should have module entity
        assert len(result.entities) >= 1

    def test_single_class(self):
        """Test file with single class."""
        try:
            import tree_sitter_c_sharp as ts_csharp
        except ImportError:
            pytest.skip("tree-sitter-c-sharp not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.csharp import CSharpExtractor

        csharp_lang = ts.Language(ts_csharp.language())
        parser = ts.Parser(csharp_lang)

        source = '''
public class HelloWorld
{
    public void Greet()
    {
        Console.WriteLine("Hello!");
    }
}
'''
        tree = parser.parse(source.encode())

        extractor = CSharpExtractor()
        result = extractor.extract(tree, Path("Hello.cs"), source)

        classes = [e for e in result.entities if e.type == EntityType.CLASS]
        assert len(classes) == 1
        assert classes[0].name == "HelloWorld"

    def test_generic_class(self):
        """Test generic class extraction."""
        try:
            import tree_sitter_c_sharp as ts_csharp
        except ImportError:
            pytest.skip("tree-sitter-c-sharp not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.csharp import CSharpExtractor

        csharp_lang = ts.Language(ts_csharp.language())
        parser = ts.Parser(csharp_lang)

        source = '''
public class Container<T>
{
    private T _value;

    public T GetValue() => _value;
}
'''
        tree = parser.parse(source.encode())

        extractor = CSharpExtractor()
        result = extractor.extract(tree, Path("container.cs"), source)

        classes = [e for e in result.entities if e.type == EntityType.CLASS]
        assert len(classes) == 1

    def test_static_class(self):
        """Test static class extraction."""
        try:
            import tree_sitter_c_sharp as ts_csharp
        except ImportError:
            pytest.skip("tree-sitter-c-sharp not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.csharp import CSharpExtractor

        csharp_lang = ts.Language(ts_csharp.language())
        parser = ts.Parser(csharp_lang)

        source = '''
public static class Utilities
{
    public static int Double(int x) => x * 2;
}
'''
        tree = parser.parse(source.encode())

        extractor = CSharpExtractor()
        result = extractor.extract(tree, Path("utils.cs"), source)

        classes = [e for e in result.entities if e.type == EntityType.CLASS]
        assert len(classes) == 1
        assert classes[0].name == "Utilities"
