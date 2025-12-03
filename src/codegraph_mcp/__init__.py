"""
CodeGraph MCP Server

A Model Context Protocol server for code graph analysis with GraphRAG capabilities.
Provides semantic code understanding through AST parsing, graph-based analysis,
and community detection.

Architecture: Library-First (ADR-001)
"""

from codegraph_mcp.config import Config


__version__ = "0.7.2"
__author__ = "CodeGraph Team"

__all__ = [
    "Config",
    "__version__",
]
