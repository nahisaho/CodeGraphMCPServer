"""
Core Engine Module

This module provides the core functionality for code graph analysis:
- AST parsing with Tree-sitter
- Graph operations with SQLite backend
- Indexing and incremental updates
- Community detection
- Semantic analysis
- LLM integration
- GraphRAG search

Architecture: Library-First (ADR-001)
"""

from codegraph_mcp.core.community import Community, CommunityDetector
from codegraph_mcp.core.graph import GraphEngine, GraphQuery, QueryResult
from codegraph_mcp.core.graphrag import GraphRAGSearch
from codegraph_mcp.core.indexer import Indexer, IndexResult
from codegraph_mcp.core.llm import LLMClient, LLMConfig
from codegraph_mcp.core.parser import ASTParser, Entity, ParseResult, Relation
from codegraph_mcp.core.semantic import SemanticAnalyzer


__all__ = [
    # Parser
    "ASTParser",
    "Community",
    # Community
    "CommunityDetector",
    "Entity",
    # Graph
    "GraphEngine",
    "GraphQuery",
    # GraphRAG
    "GraphRAGSearch",
    "IndexResult",
    # Indexer
    "Indexer",
    # LLM
    "LLMClient",
    "LLMConfig",
    "ParseResult",
    "QueryResult",
    "Relation",
    # Semantic
    "SemanticAnalyzer",
]
