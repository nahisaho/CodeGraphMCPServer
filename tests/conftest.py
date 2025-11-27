"""
Shared Test Fixtures
====================

すべてのテストで共有されるフィクスチャ。
"""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


# ========================
# Temporary Directory Fixtures
# ========================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """一時ディレクトリを提供"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_repo(temp_dir: Path) -> Generator[Path, None, None]:
    """
    一時的なGitリポジトリを提供

    git init 済みのディレクトリを作成します。
    """
    import subprocess
    subprocess.run(
        ["git", "init"],
        cwd=temp_dir,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=temp_dir,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=temp_dir,
        capture_output=True,
        check=True,
    )
    yield temp_dir


# ========================
# Sample Code Fixtures
# ========================

@pytest.fixture
def sample_python_code() -> str:
    """サンプルのPythonコード"""
    return '''
"""Sample module for testing."""

from typing import Optional


class Person:
    """A person class."""

    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def greet(self) -> str:
        """Return a greeting message."""
        return f"Hello, I am {self.name}"


def calculate_sum(a: int, b: int) -> int:
    """Calculate sum of two numbers."""
    return a + b


async def async_operation(value: Optional[str] = None) -> str:
    """Async operation example."""
    return value or "default"
'''


@pytest.fixture
def sample_typescript_code() -> str:
    """サンプルのTypeScriptコード"""
    return '''
/**
 * Sample TypeScript module for testing
 */

interface Person {
    name: string;
    age: number;
}

class Employee implements Person {
    constructor(
        public name: string,
        public age: number,
        private department: string
    ) {}

    greet(): string {
        return `Hello, I am ${this.name}`;
    }
}

function calculateSum(a: number, b: number): number {
    return a + b;
}

export { Person, Employee, calculateSum };
'''


@pytest.fixture
def sample_rust_code() -> str:
    """サンプルのRustコード"""
    return '''
//! Sample Rust module for testing

use std::fmt;

/// A person struct
#[derive(Debug, Clone)]
pub struct Person {
    pub name: String,
    pub age: u32,
}

impl Person {
    /// Create a new person
    pub fn new(name: impl Into<String>, age: u32) -> Self {
        Self {
            name: name.into(),
            age,
        }
    }

    /// Get a greeting message
    pub fn greet(&self) -> String {
        format!("Hello, I am {}", self.name)
    }
}

impl fmt::Display for Person {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Person({}, {})", self.name, self.age)
    }
}

/// Calculate sum of two numbers
pub fn calculate_sum(a: i32, b: i32) -> i32 {
    a + b
}
'''


# ========================
# Mock Data Fixtures
# ========================

@pytest.fixture
def sample_entity_data() -> dict:
    """サンプルのエンティティデータ"""
    return {
        "id": "test_entity_001",
        "name": "TestClass",
        "type": "class",
        "file_path": "/test/sample.py",
        "start_line": 10,
        "end_line": 30,
        "docstring": "A test class",
    }


@pytest.fixture
def sample_relation_data() -> dict:
    """サンプルのリレーションデータ"""
    return {
        "source_id": "test_entity_001",
        "target_id": "test_entity_002",
        "relation_type": "inherits",
    }


# ========================
# Configuration Fixtures
# ========================

@pytest.fixture
def test_config() -> dict:
    """テスト用設定"""
    return {
        "storage": {
            "db_path": ":memory:",
            "cache_size": 100,
        },
        "parser": {
            "languages": ["python"],
            "max_file_size": 1_000_000,
        },
        "server": {
            "host": "localhost",
            "port": 8080,
        },
    }


# ========================
# Database Fixtures
# ========================

@pytest.fixture
async def memory_db():
    """インメモリSQLiteデータベース"""
    # Note: 実際の実装は storage/ モジュールに依存
    # 現時点ではスタブとして定義
    yield None


# ========================
# MCP Server Fixtures
# ========================

@pytest.fixture
async def mcp_server():
    """MCPサーバーインスタンス"""
    # Note: 実際の実装は server.py に依存
    # 現時点ではスタブとして定義
    yield None
