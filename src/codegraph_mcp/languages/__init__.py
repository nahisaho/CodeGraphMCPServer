"""
Language Support Module

Language-specific AST extraction configurations and utilities.

Requirements: REQ-AST-001 ~ REQ-AST-003
Design Reference: design-core-engine.md §2.1
"""

from codegraph_mcp.languages.config import LanguageConfig, get_extractor
from codegraph_mcp.languages.python import PythonExtractor
from codegraph_mcp.languages.typescript import TypeScriptExtractor
from codegraph_mcp.languages.rust import RustExtractor
from codegraph_mcp.languages.javascript import JavaScriptExtractor

__all__ = [
    "LanguageConfig",
    "get_extractor",
    "PythonExtractor",
    "TypeScriptExtractor",
    "RustExtractor",
    "JavaScriptExtractor",
]
