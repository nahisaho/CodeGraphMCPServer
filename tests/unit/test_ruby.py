"""
Ruby Language Extractor Tests

Tests for Ruby AST parsing and entity extraction.
"""

from pathlib import Path

import pytest

from codegraph_mcp.core.parser import EntityType, RelationType


# Fixture path
RUBY_FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "ruby" / "calculator.rb"


class TestRubyExtractor:
    """Test Ruby language extractor."""

    @pytest.fixture
    def ruby_source(self) -> str:
        """Load Ruby fixture source code."""
        return RUBY_FIXTURE_PATH.read_text()

    @pytest.fixture
    def parse_result(self, ruby_source: str):
        """Parse Ruby fixture and return result."""
        try:
            import tree_sitter_ruby as ts_ruby
        except ImportError:
            pytest.skip("tree-sitter-ruby not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.ruby import RubyExtractor

        # Initialize parser
        ruby_lang = ts.Language(ts_ruby.language())
        parser = ts.Parser(ruby_lang)

        # Parse source
        tree = parser.parse(ruby_source.encode())

        # Extract entities
        extractor = RubyExtractor()
        return extractor.extract(tree, RUBY_FIXTURE_PATH, ruby_source)

    def test_module_entity_created(self, parse_result):
        """Test that module entity is created for the file."""
        modules = [e for e in parse_result.entities if e.type == EntityType.MODULE]
        assert len(modules) >= 1

    def test_class_extraction(self, parse_result):
        """Test class extraction."""
        classes = [e for e in parse_result.entities if e.type == EntityType.CLASS]
        class_names = {c.name for c in classes}

        assert "Base" in class_names
        assert "Advanced" in class_names
        assert "Full" in class_names

    def test_module_extraction(self, parse_result):
        """Test module extraction."""
        modules = [e for e in parse_result.entities if e.type == EntityType.MODULE]
        module_names = {m.name for m in modules}

        assert "Loggable" in module_names
        assert "Calculator" in module_names
        assert "Scientific" in module_names

    def test_method_extraction(self, parse_result):
        """Test method extraction."""
        methods = [e for e in parse_result.entities if e.type == EntityType.METHOD]
        method_names = {m.name for m in methods}

        assert "add" in method_names
        assert "subtract" in method_names
        assert "multiply" in method_names
        assert "divide" in method_names
        assert "power" in method_names

    def test_singleton_method_extraction(self, parse_result):
        """Test singleton (class) method extraction."""
        methods = [e for e in parse_result.entities if e.type == EntityType.METHOD]
        method_names = {m.name for m in methods}

        # Class methods should have self. prefix
        assert any("self.create_default" in name for name in method_names)

    def test_function_extraction(self, parse_result):
        """Test top-level function extraction."""
        # Note: In Ruby context, top-level defs are still methods
        # but we should find create_calculator
        all_entities = parse_result.entities
        entity_names = {e.name for e in all_entities}

        assert "create_calculator" in entity_names or any("create_calculator" in str(e.name) for e in all_entities)

    def test_inheritance_relations(self, parse_result):
        """Test inheritance relation extraction."""
        inherits = [r for r in parse_result.relations if r.type == RelationType.INHERITS]

        # Advanced < Base
        assert any("Base" in r.target_id for r in inherits)

    def test_import_relations(self, parse_result):
        """Test require statement extraction."""
        imports = [r for r in parse_result.relations if r.type == RelationType.IMPORTS]
        import_targets = {r.target_id for r in imports}

        assert any("logger" in t for t in import_targets)

    def test_include_relations(self, parse_result):
        """Test include/extend extraction."""
        implements = [r for r in parse_result.relations if r.type == RelationType.IMPLEMENTS]

        # Classes include Loggable
        assert any("Loggable" in r.target_id for r in implements)

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


class TestRubyExtractorEdgeCases:
    """Test edge cases for Ruby extractor."""

    def test_empty_file(self):
        """Test parsing empty Ruby file."""
        try:
            import tree_sitter_ruby as ts_ruby
        except ImportError:
            pytest.skip("tree-sitter-ruby not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.ruby import RubyExtractor

        ruby_lang = ts.Language(ts_ruby.language())
        parser = ts.Parser(ruby_lang)

        source = "# Empty file\n"
        tree = parser.parse(source.encode())

        extractor = RubyExtractor()
        result = extractor.extract(tree, Path("empty.rb"), source)

        # Should have module entity
        assert len(result.entities) >= 1

    def test_single_class(self):
        """Test file with single class."""
        try:
            import tree_sitter_ruby as ts_ruby
        except ImportError:
            pytest.skip("tree-sitter-ruby not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.ruby import RubyExtractor

        ruby_lang = ts.Language(ts_ruby.language())
        parser = ts.Parser(ruby_lang)

        source = '''
class HelloWorld
  def greet
    puts "Hello!"
  end
end
'''
        tree = parser.parse(source.encode())

        extractor = RubyExtractor()
        result = extractor.extract(tree, Path("hello.rb"), source)

        classes = [e for e in result.entities if e.type == EntityType.CLASS]
        assert len(classes) == 1
        assert classes[0].name == "HelloWorld"

    def test_nested_class(self):
        """Test nested class extraction."""
        try:
            import tree_sitter_ruby as ts_ruby
        except ImportError:
            pytest.skip("tree-sitter-ruby not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.ruby import RubyExtractor

        ruby_lang = ts.Language(ts_ruby.language())
        parser = ts.Parser(ruby_lang)

        source = '''
module App
  class Base
    def initialize
    end
  end

  class Child < Base
    def process
    end
  end
end
'''
        tree = parser.parse(source.encode())

        extractor = RubyExtractor()
        result = extractor.extract(tree, Path("app.rb"), source)

        classes = [e for e in result.entities if e.type == EntityType.CLASS]
        class_names = {c.name for c in classes}

        assert "Base" in class_names
        assert "Child" in class_names

    def test_attr_accessor(self):
        """Test class with attr_accessor."""
        try:
            import tree_sitter_ruby as ts_ruby
        except ImportError:
            pytest.skip("tree-sitter-ruby not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.ruby import RubyExtractor

        ruby_lang = ts.Language(ts_ruby.language())
        parser = ts.Parser(ruby_lang)

        source = '''
class Person
  attr_reader :name
  attr_accessor :age

  def initialize(name, age)
    @name = name
    @age = age
  end
end
'''
        tree = parser.parse(source.encode())

        extractor = RubyExtractor()
        result = extractor.extract(tree, Path("person.rb"), source)

        classes = [e for e in result.entities if e.type == EntityType.CLASS]
        assert len(classes) == 1
        assert classes[0].name == "Person"

    def test_module_mixin(self):
        """Test module mixin patterns."""
        try:
            import tree_sitter_ruby as ts_ruby
        except ImportError:
            pytest.skip("tree-sitter-ruby not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.ruby import RubyExtractor

        ruby_lang = ts.Language(ts_ruby.language())
        parser = ts.Parser(ruby_lang)

        source = '''
module Comparable
  def <=>(other)
    raise NotImplementedError
  end
end

class Item
  include Comparable

  def <=>(other)
    self.value <=> other.value
  end
end
'''
        tree = parser.parse(source.encode())

        extractor = RubyExtractor()
        result = extractor.extract(tree, Path("item.rb"), source)

        modules = [e for e in result.entities if e.type == EntityType.MODULE]
        module_names = {m.name for m in modules}
        assert "Comparable" in module_names

        classes = [e for e in result.entities if e.type == EntityType.CLASS]
        assert len(classes) == 1
        assert classes[0].name == "Item"
