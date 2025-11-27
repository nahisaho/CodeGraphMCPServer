"""
HCL Language Extractor Tests

Tests for HCL/Terraform AST parsing and entity extraction.
"""

from pathlib import Path

import pytest

from codegraph_mcp.core.parser import EntityType, RelationType


# Fixture path
HCL_FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "hcl" / "main.tf"


class TestHCLExtractor:
    """Test HCL/Terraform language extractor."""

    @pytest.fixture
    def hcl_source(self) -> str:
        """Load HCL fixture source code."""
        return HCL_FIXTURE_PATH.read_text()

    @pytest.fixture
    def parse_result(self, hcl_source: str):
        """Parse HCL fixture and return result."""
        try:
            import tree_sitter_hcl as ts_hcl
        except ImportError:
            pytest.skip("tree-sitter-hcl not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.hcl import HCLExtractor

        # Initialize parser
        hcl_lang = ts.Language(ts_hcl.language())
        parser = ts.Parser(hcl_lang)

        # Parse source
        tree = parser.parse(hcl_source.encode())

        # Extract entities
        extractor = HCLExtractor()
        return extractor.extract(tree, HCL_FIXTURE_PATH, hcl_source)

    def test_module_entity_created(self, parse_result):
        """Test that module entity is created for the file."""
        modules = [e for e in parse_result.entities if e.type == EntityType.MODULE]
        assert len(modules) >= 1

    def test_resource_extraction(self, parse_result):
        """Test resource block extraction."""
        classes = [e for e in parse_result.entities if e.type == EntityType.CLASS]
        entity_names = {c.name for c in classes}

        # Resources are extracted as CLASS type
        assert any("aws_vpc" in name for name in entity_names)
        assert any("aws_subnet" in name for name in entity_names)
        assert any("aws_security_group" in name for name in entity_names)
        assert any("aws_instance" in name for name in entity_names)

    def test_variable_extraction(self, parse_result):
        """Test variable block extraction."""
        functions = [e for e in parse_result.entities if e.type == EntityType.FUNCTION]
        entity_names = {f.name for f in functions}

        # Variables are extracted as FUNCTION type
        assert any("aws_region" in name for name in entity_names)
        assert any("instance_type" in name for name in entity_names)
        assert any("environment" in name for name in entity_names)

    def test_output_extraction(self, parse_result):
        """Test output block extraction."""
        functions = [e for e in parse_result.entities if e.type == EntityType.FUNCTION]
        entity_names = {f.name for f in functions}

        assert any("instance_id" in name for name in entity_names)
        assert any("public_ip" in name for name in entity_names)

    def test_data_source_extraction(self, parse_result):
        """Test data source extraction."""
        classes = [e for e in parse_result.entities if e.type == EntityType.CLASS]
        entity_names = {c.name for c in classes}

        assert any("data.aws_ami" in name for name in entity_names)

    def test_contains_relations(self, parse_result):
        """Test that contains relations link file to blocks."""
        contains = [r for r in parse_result.relations if r.type == RelationType.CONTAINS]
        assert len(contains) > 0

    def test_entity_locations(self, parse_result):
        """Test that entities have valid locations."""
        for entity in parse_result.entities:
            assert entity.location is not None
            assert entity.location.start_line > 0
            assert entity.location.end_line >= entity.location.start_line


class TestHCLExtractorEdgeCases:
    """Test edge cases for HCL extractor."""

    def test_empty_file(self):
        """Test parsing empty HCL file."""
        try:
            import tree_sitter_hcl as ts_hcl
        except ImportError:
            pytest.skip("tree-sitter-hcl not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.hcl import HCLExtractor

        hcl_lang = ts.Language(ts_hcl.language())
        parser = ts.Parser(hcl_lang)

        source = "# Empty file\n"
        tree = parser.parse(source.encode())

        extractor = HCLExtractor()
        result = extractor.extract(tree, Path("empty.tf"), source)

        # Should have module entity
        assert len(result.entities) >= 1

    def test_single_resource(self):
        """Test file with single resource."""
        try:
            import tree_sitter_hcl as ts_hcl
        except ImportError:
            pytest.skip("tree-sitter-hcl not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.hcl import HCLExtractor

        hcl_lang = ts.Language(ts_hcl.language())
        parser = ts.Parser(hcl_lang)

        source = '''
resource "aws_s3_bucket" "example" {
  bucket = "my-bucket"
}
'''
        tree = parser.parse(source.encode())

        extractor = HCLExtractor()
        result = extractor.extract(tree, Path("bucket.tf"), source)

        classes = [e for e in result.entities if e.type == EntityType.CLASS]
        assert len(classes) >= 1
        assert any("aws_s3_bucket" in c.name for c in classes)

    def test_variable_with_default(self):
        """Test variable with default value."""
        try:
            import tree_sitter_hcl as ts_hcl
        except ImportError:
            pytest.skip("tree-sitter-hcl not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.hcl import HCLExtractor

        hcl_lang = ts.Language(ts_hcl.language())
        parser = ts.Parser(hcl_lang)

        source = '''
variable "region" {
  type        = string
  default     = "us-west-2"
  description = "AWS region"
}
'''
        tree = parser.parse(source.encode())

        extractor = HCLExtractor()
        result = extractor.extract(tree, Path("vars.tf"), source)

        functions = [e for e in result.entities if e.type == EntityType.FUNCTION]
        assert len(functions) >= 1
        assert any("region" in f.name for f in functions)

    def test_locals_block(self):
        """Test locals block extraction."""
        try:
            import tree_sitter_hcl as ts_hcl
        except ImportError:
            pytest.skip("tree-sitter-hcl not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.hcl import HCLExtractor

        hcl_lang = ts.Language(ts_hcl.language())
        parser = ts.Parser(hcl_lang)

        source = '''
locals {
  common_tags = {
    Environment = "dev"
    Team        = "platform"
  }
}
'''
        tree = parser.parse(source.encode())

        extractor = HCLExtractor()
        result = extractor.extract(tree, Path("locals.tf"), source)

        # Locals should be extracted
        assert len(result.entities) >= 1

    def test_module_block(self):
        """Test module block extraction."""
        try:
            import tree_sitter_hcl as ts_hcl
        except ImportError:
            pytest.skip("tree-sitter-hcl not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.hcl import HCLExtractor

        hcl_lang = ts.Language(ts_hcl.language())
        parser = ts.Parser(hcl_lang)

        source = '''
module "vpc" {
  source = "./modules/vpc"

  cidr_block = "10.0.0.0/16"
}
'''
        tree = parser.parse(source.encode())

        extractor = HCLExtractor()
        result = extractor.extract(tree, Path("main.tf"), source)

        modules = [e for e in result.entities if e.type == EntityType.MODULE]
        assert any("module.vpc" in m.name for m in modules)

    def test_provider_block(self):
        """Test provider block extraction."""
        try:
            import tree_sitter_hcl as ts_hcl
        except ImportError:
            pytest.skip("tree-sitter-hcl not installed")

        import tree_sitter as ts

        from codegraph_mcp.languages.hcl import HCLExtractor

        hcl_lang = ts.Language(ts_hcl.language())
        parser = ts.Parser(hcl_lang)

        source = '''
provider "aws" {
  region = "us-west-2"
}
'''
        tree = parser.parse(source.encode())

        extractor = HCLExtractor()
        result = extractor.extract(tree, Path("provider.tf"), source)

        modules = [e for e in result.entities if e.type == EntityType.MODULE]
        assert any("provider" in m.name for m in modules)
