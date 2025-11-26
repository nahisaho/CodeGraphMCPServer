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

from codegraph_mcp.core.parser import ASTParser, ParseResult, Entity, Relation
from codegraph_mcp.core.graph import GraphEngine, GraphQuery, QueryResult
from codegraph_mcp.core.indexer import Indexer, IndexResult
from codegraph_mcp.core.community import CommunityDetector, Community
from codegraph_mcp.core.semantic import SemanticAnalyzer
from codegraph_mcp.core.llm import LLMClient, LLMConfig
from codegraph_mcp.core.graphrag import GraphRAGSearch

__all__ = [
    # Parser
    "ASTParser",
    "ParseResult",
    "Entity",
    "Relation",
    # Graph
    "GraphEngine",
    "GraphQuery",
    "QueryResult",
    # Indexer
    "Indexer",
    "IndexResult",
    # Community
    "CommunityDetector",
    "Community",
    # Semantic
    "SemanticAnalyzer",
    # LLM
    "LLMClient",
    "LLMConfig",
    # GraphRAG
    "GraphRAGSearch",
]
