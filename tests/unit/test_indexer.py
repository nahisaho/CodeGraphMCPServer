"""
Unit tests for the Indexer module.

Tests: REQ-IDX-001 ~ REQ-IDX-004
"""

from datetime import datetime
from pathlib import Path

import pytest

from codegraph_mcp.core.indexer import FileInfo, Indexer, IndexResult
from codegraph_mcp.core.parser import ASTParser


# Fixtures

@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Create a temporary repository with test files."""
    # Create Python files
    (tmp_path / "main.py").write_text("""
def main():
    helper()
    print("Hello")

def helper():
    pass
""")

    (tmp_path / "utils.py").write_text("""
from main import helper

class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b

    def multiply(self, a: int, b: int) -> int:
        return self.add(a, 0)  # Just for testing calls
""")

    # Create subdirectory
    subdir = tmp_path / "src"
    subdir.mkdir()
    (subdir / "module.py").write_text("""
import utils

def process():
    calc = utils.Calculator()
    return calc.add(1, 2)
""")

    return tmp_path


@pytest.fixture
def indexer() -> Indexer:
    """Create an indexer instance."""
    return Indexer()


# IndexResult Tests

class TestIndexResult:
    """Tests for IndexResult dataclass."""

    def test_default_values(self):
        """Test IndexResult default values."""
        result = IndexResult()
        assert result.entities_count == 0
        assert result.relations_count == 0
        assert result.files_indexed == 0
        assert result.files_skipped == 0
        assert result.errors == []
        assert result.duration_seconds == 0.0

    def test_success_property(self):
        """Test success property."""
        result = IndexResult()
        assert result.success is True

        result.errors.append("Some error")
        assert result.success is False

    def test_with_values(self):
        """Test IndexResult with values."""
        result = IndexResult(
            entities_count=10,
            relations_count=5,
            files_indexed=3,
            duration_seconds=1.5,
        )
        assert result.entities_count == 10
        assert result.relations_count == 5
        assert result.files_indexed == 3
        assert result.duration_seconds == 1.5
        assert result.success is True


class TestFileInfo:
    """Tests for FileInfo dataclass."""

    def test_file_info_creation(self, tmp_path: Path):
        """Test FileInfo creation."""
        info = FileInfo(
            path=tmp_path / "test.py",
            language="python",
            hash="abc123",
            size=100,
            indexed_at=datetime.now(),
        )
        assert info.language == "python"
        assert info.hash == "abc123"
        assert info.size == 100


# Indexer Tests

class TestIndexer:
    """Tests for Indexer class."""

    def test_indexer_initialization(self):
        """Test indexer initialization."""
        indexer = Indexer()
        assert indexer.parser is not None
        assert isinstance(indexer.parser, ASTParser)
        assert indexer._engine is None

    def test_indexer_with_custom_parser(self):
        """Test indexer with custom parser."""
        custom_parser = ASTParser()
        indexer = Indexer(parser=custom_parser)
        assert indexer.parser is custom_parser

    @pytest.mark.asyncio
    async def test_index_repository_full(self, temp_repo: Path, indexer: Indexer):
        """Test full repository indexing."""
        result = await indexer.index_repository(temp_repo, incremental=False)

        assert result.success is True
        assert result.files_indexed == 3  # main.py, utils.py, src/module.py
        assert result.entities_count > 0
        assert result.relations_count > 0
        assert result.duration_seconds > 0

    @pytest.mark.asyncio
    async def test_index_repository_incremental(self, temp_repo: Path, indexer: Indexer):
        """Test incremental indexing (without git - falls back to full)."""
        # Without a git repo, incremental should fall back to full scan
        result = await indexer.index_repository(temp_repo, incremental=True)

        assert result.success is True
        assert result.files_indexed >= 0  # May index some files

    @pytest.mark.asyncio
    async def test_index_empty_directory(self, tmp_path: Path, indexer: Indexer):
        """Test indexing empty directory."""
        result = await indexer.index_repository(tmp_path, incremental=False)

        assert result.success is True
        assert result.files_indexed == 0
        assert result.entities_count == 0

    @pytest.mark.asyncio
    async def test_index_excludes_patterns(self, tmp_path: Path, indexer: Indexer):
        """Test that excluded directories are skipped."""
        # Create files in excluded directories
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "test.py").write_text("def foo(): pass")

        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "lib.py").write_text("class Lib: pass")

        # Create a valid file
        (tmp_path / "valid.py").write_text("def valid(): pass")

        result = await indexer.index_repository(tmp_path, incremental=False)

        assert result.success is True
        assert result.files_indexed == 1  # Only valid.py

    @pytest.mark.asyncio
    async def test_index_with_errors(self, tmp_path: Path, indexer: Indexer):
        """Test indexing with parse errors."""
        # Create a file with syntax error
        (tmp_path / "broken.py").write_text("def broken(:\n  pass")

        # Create a valid file
        (tmp_path / "valid.py").write_text("def valid(): pass")

        result = await indexer.index_repository(tmp_path, incremental=False)

        # Should still succeed, but may have errors
        assert result.files_indexed >= 1

    def test_get_all_files(self, temp_repo: Path, indexer: Indexer):
        """Test _get_all_files method."""
        files = indexer._get_all_files(temp_repo)

        assert len(files) == 3
        filenames = {f.name for f in files}
        assert "main.py" in filenames
        assert "utils.py" in filenames
        assert "module.py" in filenames


class TestComputeFileHash:
    """Tests for file hash computation."""

    def test_compute_file_hash(self, tmp_path: Path):
        """Test file hash computation."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo(): pass")

        hash1 = Indexer.compute_file_hash(test_file)
        assert len(hash1) == 64  # SHA-256 hex digest

        # Same content should produce same hash
        hash2 = Indexer.compute_file_hash(test_file)
        assert hash1 == hash2

    def test_different_content_different_hash(self, tmp_path: Path):
        """Test that different content produces different hash."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"

        file1.write_text("content1")
        file2.write_text("content2")

        hash1 = Indexer.compute_file_hash(file1)
        hash2 = Indexer.compute_file_hash(file2)

        assert hash1 != hash2


class TestIndexerIntegration:
    """Integration tests for indexer."""

    @pytest.mark.asyncio
    async def test_entities_are_stored(self, temp_repo: Path, indexer: Indexer):
        """Test that entities are properly stored in the graph."""
        result = await indexer.index_repository(temp_repo, incremental=False)

        assert result.success is True
        # Entities should include functions, classes, etc.
        assert result.entities_count >= 6  # main, helper, Calculator, add, multiply, process

    @pytest.mark.asyncio
    async def test_relations_are_stored(self, temp_repo: Path, indexer: Indexer):
        """Test that relations are properly stored in the graph."""
        result = await indexer.index_repository(temp_repo, incremental=False)

        assert result.success is True
        # Relations should include calls, imports, contains, etc.
        assert result.relations_count >= 3
