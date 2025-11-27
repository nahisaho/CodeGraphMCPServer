"""
Go Language Extractor Tests

Tests for Go AST parsing and entity extraction.
"""

from pathlib import Path

import pytest

from codegraph_mcp.core.parser import EntityType, RelationType


# Fixture path
GO_FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "go" / "calculator.go"


class TestGoExtractor:
    """Test Go language extractor."""

    @pytest.fixture
    def go_source(self) -> str:
        """Load Go fixture source code."""
        return GO_FIXTURE_PATH.read_text()

    @pytest.fixture
    def parse_result(self, go_source: str):
        """Parse Go fixture and return result."""
        try:
            import tree_sitter_go as ts_go
        except ImportError:
            pytest.skip("tree-sitter-go not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.go import GoExtractor

        # Initialize parser
        go_lang = ts.Language(ts_go.language())
        parser = ts.Parser(go_lang)

        # Parse source
        tree = parser.parse(go_source.encode())

        # Extract entities
        extractor = GoExtractor()
        return extractor.extract(tree, GO_FIXTURE_PATH, go_source)

    def test_module_entity_created(self, parse_result):
        """Test that module entity is created for the file."""
        modules = [e for e in parse_result.entities if e.type == EntityType.MODULE]
        assert len(modules) == 1
        assert modules[0].name == "calculator"

    def test_function_extraction(self, parse_result):
        """Test function extraction."""
        functions = [e for e in parse_result.entities if e.type == EntityType.FUNCTION]
        func_names = {f.name for f in functions}

        # Check expected functions
        assert "Add" in func_names
        assert "Subtract" in func_names
        assert "Multiply" in func_names
        assert "Divide" in func_names
        assert "SquareRoot" in func_names
        assert "PrintResult" in func_names

    def test_struct_extraction(self, parse_result):
        """Test struct extraction."""
        structs = [e for e in parse_result.entities if e.type == EntityType.STRUCT]
        struct_names = {s.name for s in structs}

        assert "Calculator" in struct_names
        assert "AddOperation" in struct_names

    def test_interface_extraction(self, parse_result):
        """Test interface extraction."""
        interfaces = [e for e in parse_result.entities if e.type == EntityType.INTERFACE]
        interface_names = {i.name for i in interfaces}

        assert "Operation" in interface_names

    def test_method_extraction(self, parse_result):
        """Test method extraction."""
        methods = [e for e in parse_result.entities if e.type == EntityType.METHOD]
        method_names = {m.name for m in methods}

        # Calculator methods
        assert "Calculate" in method_names
        assert "Clear" in method_names
        assert "GetHistory" in method_names

        # AddOperation methods
        assert "Execute" in method_names
        assert "Name" in method_names

    def test_method_receiver_in_qualified_name(self, parse_result):
        """Test that methods include receiver type in qualified name."""
        methods = [e for e in parse_result.entities if e.type == EntityType.METHOD]

        calculate_method = next((m for m in methods if m.name == "Calculate"), None)
        assert calculate_method is not None
        assert "Calculator" in calculate_method.qualified_name

    def test_import_relations(self, parse_result):
        """Test import relation extraction."""
        imports = [r for r in parse_result.relations if r.type == RelationType.IMPORTS]
        import_targets = {r.target_id for r in imports}

        assert "module::fmt" in import_targets
        assert "module::math" in import_targets

    def test_call_relations(self, parse_result):
        """Test function call relation extraction."""
        calls = [r for r in parse_result.relations if r.type == RelationType.CALLS]

        # Should have calls to math.Sqrt, fmt.Printf, etc.
        call_targets = {r.target_id for r in calls}

        # Check for some expected calls
        assert any("math.Sqrt" in t or "Sqrt" in t for t in call_targets)
        assert any("fmt.Printf" in t or "Printf" in t for t in call_targets)

    def test_contains_relations(self, parse_result):
        """Test that contains relations link module to entities."""
        contains = [r for r in parse_result.relations if r.type == RelationType.CONTAINS]

        # Module should contain functions, structs, interfaces
        assert len(contains) > 0

    def test_function_signature(self, parse_result):
        """Test function signature extraction."""
        functions = [e for e in parse_result.entities if e.type == EntityType.FUNCTION]

        add_func = next((f for f in functions if f.name == "Add"), None)
        assert add_func is not None
        assert add_func.signature is not None
        assert "func Add" in add_func.signature

    def test_entity_locations(self, parse_result):
        """Test that entities have valid locations."""
        for entity in parse_result.entities:
            assert entity.location is not None
            assert entity.location.start_line > 0
            assert entity.location.end_line >= entity.location.start_line

    def test_source_code_captured(self, parse_result):
        """Test that source code is captured for entities."""
        functions = [e for e in parse_result.entities if e.type == EntityType.FUNCTION]

        add_func = next((f for f in functions if f.name == "Add"), None)
        assert add_func is not None
        assert add_func.source_code is not None
        assert "return a + b" in add_func.source_code


class TestGoExtractorEdgeCases:
    """Test edge cases for Go extractor."""

    def test_empty_file(self):
        """Test parsing empty Go file."""
        try:
            import tree_sitter_go as ts_go
        except ImportError:
            pytest.skip("tree-sitter-go not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.go import GoExtractor

        go_lang = ts.Language(ts_go.language())
        parser = ts.Parser(go_lang)

        source = "package main\n"
        tree = parser.parse(source.encode())

        extractor = GoExtractor()
        result = extractor.extract(tree, Path("empty.go"), source)

        # Should have module entity
        assert len(result.entities) >= 1
        assert result.entities[0].type == EntityType.MODULE

    def test_single_function(self):
        """Test file with single function."""
        try:
            import tree_sitter_go as ts_go
        except ImportError:
            pytest.skip("tree-sitter-go not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.go import GoExtractor

        go_lang = ts.Language(ts_go.language())
        parser = ts.Parser(go_lang)

        source = '''package main

func main() {
    println("Hello")
}
'''
        tree = parser.parse(source.encode())

        extractor = GoExtractor()
        result = extractor.extract(tree, Path("main.go"), source)

        functions = [e for e in result.entities if e.type == EntityType.FUNCTION]
        assert len(functions) == 1
        assert functions[0].name == "main"

    def test_pointer_receiver(self):
        """Test method with pointer receiver."""
        try:
            import tree_sitter_go as ts_go
        except ImportError:
            pytest.skip("tree-sitter-go not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.go import GoExtractor

        go_lang = ts.Language(ts_go.language())
        parser = ts.Parser(go_lang)

        source = '''package main

type Counter struct {
    value int
}

func (c *Counter) Increment() {
    c.value++
}
'''
        tree = parser.parse(source.encode())

        extractor = GoExtractor()
        result = extractor.extract(tree, Path("counter.go"), source)

        methods = [e for e in result.entities if e.type == EntityType.METHOD]
        assert len(methods) == 1
        assert methods[0].name == "Increment"
        assert "Counter" in methods[0].qualified_name
