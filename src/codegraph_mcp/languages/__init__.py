"""
Language Support Module

Language-specific AST extraction configurations and utilities.

Requirements: REQ-AST-001 ~ REQ-AST-009
Design Reference: design-core-engine.md §2.1
"""

from codegraph_mcp.languages.config import LanguageConfig, get_extractor
from codegraph_mcp.languages.cpp import CppExtractor
from codegraph_mcp.languages.csharp import CSharpExtractor
from codegraph_mcp.languages.go import GoExtractor
from codegraph_mcp.languages.hcl import HCLExtractor
from codegraph_mcp.languages.java import JavaExtractor
from codegraph_mcp.languages.javascript import JavaScriptExtractor
from codegraph_mcp.languages.php import PHPExtractor
from codegraph_mcp.languages.python import PythonExtractor
from codegraph_mcp.languages.ruby import RubyExtractor
from codegraph_mcp.languages.rust import RustExtractor
from codegraph_mcp.languages.typescript import TypeScriptExtractor


__all__ = [
    "CSharpExtractor",
    "CppExtractor",
    "GoExtractor",
    "HCLExtractor",
    "JavaExtractor",
    "JavaScriptExtractor",
    "LanguageConfig",
    "PHPExtractor",
    "PythonExtractor",
    "RubyExtractor",
    "RustExtractor",
    "TypeScriptExtractor",
    "get_extractor",
]
