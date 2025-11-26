"""
CodeGraph MCP Server

A Model Context Protocol server for code graph analysis with GraphRAG capabilities.
Provides semantic code understanding through AST parsing, graph-based analysis,
and community detection.

Architecture: Library-First (ADR-001)
"""

__version__ = "0.6.0"
__author__ = "CodeGraph Team"

from codegraph_mcp.config import Config

__all__ = [
    "__version__",
    "Config",
]
