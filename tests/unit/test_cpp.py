"""
C++ Language Extractor Tests

Tests for C++ AST parsing and entity extraction.
"""

from pathlib import Path

import pytest

from codegraph_mcp.core.parser import EntityType, RelationType


# Fixture path
CPP_FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "cpp" / "calculator.cpp"


class TestCppExtractor:
    """Test C++ language extractor."""

    @pytest.fixture
    def cpp_source(self) -> str:
        """Load C++ fixture source code."""
        return CPP_FIXTURE_PATH.read_text()

    @pytest.fixture
    def parse_result(self, cpp_source: str):
        """Parse C++ fixture and return result."""
        try:
            import tree_sitter_cpp as ts_cpp
        except ImportError:
            pytest.skip("tree-sitter-cpp not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.cpp import CppExtractor

        # Initialize parser
        cpp_lang = ts.Language(ts_cpp.language())
        parser = ts.Parser(cpp_lang)

        # Parse source
        tree = parser.parse(cpp_source.encode())

        # Extract entities
        extractor = CppExtractor()
        return extractor.extract(tree, CPP_FIXTURE_PATH, cpp_source)

    def test_module_entity_created(self, parse_result):
        """Test that module entity is created for the file."""
        modules = [e for e in parse_result.entities if e.type == EntityType.MODULE]
        assert len(modules) >= 1
        assert modules[0].name == "calculator"

    def test_class_extraction(self, parse_result):
        """Test class extraction."""
        classes = [e for e in parse_result.entities if e.type == EntityType.CLASS]
        class_names = {c.name for c in classes}

        assert "BaseCalculator" in class_names
        assert "Calculator" in class_names
        assert "AdvancedCalculator" in class_names

    def test_struct_extraction(self, parse_result):
        """Test struct extraction."""
        structs = [e for e in parse_result.entities if e.type == EntityType.STRUCT]
        struct_names = {s.name for s in structs}

        assert "Point" in struct_names

    def test_function_extraction(self, parse_result):
        """Test free function extraction."""
        functions = [e for e in parse_result.entities if e.type == EntityType.FUNCTION]
        func_names = {f.name for f in functions}

        assert "createDefaultPrecision" in func_names

    def test_method_extraction(self, parse_result):
        """Test method extraction."""
        methods = [e for e in parse_result.entities if e.type == EntityType.METHOD]
        method_names = {m.name for m in methods}

        assert "add" in method_names
        assert "subtract" in method_names
        assert "multiply" in method_names
        assert "divide" in method_names

    def test_inheritance_relations(self, parse_result):
        """Test inheritance relation extraction."""
        inherits = [r for r in parse_result.relations if r.type == RelationType.INHERITS]

        # Calculator inherits from BaseCalculator
        assert any("BaseCalculator" in r.target_id for r in inherits)

    def test_include_relations(self, parse_result):
        """Test #include extraction."""
        imports = [r for r in parse_result.relations if r.type == RelationType.IMPORTS]
        import_targets = {r.target_id for r in imports}

        assert any("iostream" in t for t in import_targets)
        assert any("cmath" in t for t in import_targets)

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


class TestCppExtractorEdgeCases:
    """Test edge cases for C++ extractor."""

    def test_empty_file(self):
        """Test parsing empty C++ file."""
        try:
            import tree_sitter_cpp as ts_cpp
        except ImportError:
            pytest.skip("tree-sitter-cpp not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.cpp import CppExtractor

        cpp_lang = ts.Language(ts_cpp.language())
        parser = ts.Parser(cpp_lang)

        source = "// Empty file\n"
        tree = parser.parse(source.encode())

        extractor = CppExtractor()
        result = extractor.extract(tree, Path("empty.cpp"), source)

        # Should have module entity
        assert len(result.entities) >= 1

    def test_single_function(self):
        """Test file with single function."""
        try:
            import tree_sitter_cpp as ts_cpp
        except ImportError:
            pytest.skip("tree-sitter-cpp not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.cpp import CppExtractor

        cpp_lang = ts.Language(ts_cpp.language())
        parser = ts.Parser(cpp_lang)

        source = '''
int main() {
    return 0;
}
'''
        tree = parser.parse(source.encode())

        extractor = CppExtractor()
        result = extractor.extract(tree, Path("main.cpp"), source)

        functions = [e for e in result.entities if e.type == EntityType.FUNCTION]
        assert len(functions) == 1
        assert functions[0].name == "main"

    def test_template_class(self):
        """Test template class extraction."""
        try:
            import tree_sitter_cpp as ts_cpp
        except ImportError:
            pytest.skip("tree-sitter-cpp not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.cpp import CppExtractor

        cpp_lang = ts.Language(ts_cpp.language())
        parser = ts.Parser(cpp_lang)

        source = '''
template<typename T>
class Container {
public:
    T getValue() const { return value; }
private:
    T value;
};
'''
        tree = parser.parse(source.encode())

        extractor = CppExtractor()
        result = extractor.extract(tree, Path("container.cpp"), source)

        classes = [e for e in result.entities if e.type == EntityType.CLASS]
        assert len(classes) == 1
        assert classes[0].name == "Container"

    def test_namespace(self):
        """Test namespace handling."""
        try:
            import tree_sitter_cpp as ts_cpp
        except ImportError:
            pytest.skip("tree-sitter-cpp not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.cpp import CppExtractor

        cpp_lang = ts.Language(ts_cpp.language())
        parser = ts.Parser(cpp_lang)

        source = '''
namespace MyApp {
    class Widget {
    public:
        void draw() {}
    };
}
'''
        tree = parser.parse(source.encode())

        extractor = CppExtractor()
        result = extractor.extract(tree, Path("widget.cpp"), source)

        classes = [e for e in result.entities if e.type == EntityType.CLASS]
        assert len(classes) == 1
        assert classes[0].name == "Widget"

    def test_header_only_declaration(self):
        """Test header-style method declarations."""
        try:
            import tree_sitter_cpp as ts_cpp
        except ImportError:
            pytest.skip("tree-sitter-cpp not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.cpp import CppExtractor

        cpp_lang = ts.Language(ts_cpp.language())
        parser = ts.Parser(cpp_lang)

        source = '''
class Calculator {
public:
    int add(int a, int b);
    int subtract(int a, int b);
};
'''
        tree = parser.parse(source.encode())

        extractor = CppExtractor()
        result = extractor.extract(tree, Path("calc.h"), source)

        classes = [e for e in result.entities if e.type == EntityType.CLASS]
        assert len(classes) == 1

        methods = [e for e in result.entities if e.type == EntityType.METHOD]
        assert len(methods) == 2
