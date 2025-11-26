# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-26

### Added

#### Core Features
- **AST Parsing**: Tree-sitter based multi-language code analysis
  - Python support with full class/function/method extraction
  - TypeScript support with interface and type alias handling
  - JavaScript support (ES6+, JSX, CommonJS, ESM)
  - Rust support with struct/enum/trait/impl extraction

- **Code Graph Engine**: NetworkX-based graph construction
  - Entity extraction (classes, functions, methods, modules)
  - Relation detection (calls, contains, imports, implements, extends)
  - Dependency analysis with configurable depth

- **GraphRAG Integration**: Graph-based Retrieval Augmented Generation
  - Community detection using Louvain algorithm
  - Global search across all code communities
  - Local search within entity neighborhoods
  - LLM integration (OpenAI, Anthropic, Ollama, Rule-based)

- **Storage Layer**: SQLite-based persistence
  - Async database operations with aiosqlite
  - File-based caching for performance
  - Vector storage for semantic search

#### MCP Interface
- **14 MCP Tools**:
  - Graph Query: `query_codebase`, `find_dependencies`, `find_callers`, `find_callees`, `find_implementations`, `analyze_module_structure`
  - Code Retrieval: `get_code_snippet`, `read_file_content`, `get_file_structure`
  - GraphRAG: `global_search`, `local_search`
  - Management: `suggest_refactoring`, `reindex_repository`, `execute_shell_command`

- **4 MCP Resources**:
  - `codegraph://entities/{id}` - Entity details
  - `codegraph://files/{path}` - File graph information
  - `codegraph://communities/{id}` - Community data
  - `codegraph://stats` - Graph statistics

- **6 MCP Prompts**:
  - `code_review` - Code review assistance
  - `explain_codebase` - Codebase explanation
  - `implement_feature` - Feature implementation guidance
  - `debug_issue` - Debug assistance
  - `refactor_guidance` - Refactoring suggestions
  - `test_generation` - Test generation help

#### Transport Protocols
- stdio transport (default) for standard MCP clients
- SSE transport for HTTP-based integrations

#### CLI Commands
- `codegraph-mcp serve` - Start MCP server
- `codegraph-mcp index` - Index repository
- `codegraph-mcp query` - Search code entities
- `codegraph-mcp stats` - Display graph statistics

#### Documentation
- Comprehensive API reference (`docs/api.md`)
- Configuration guide (`docs/configuration.md`)
- Usage examples (`docs/examples.md`)
- Sample scripts in `examples/` directory

### Performance
- Initial indexing: ~700 entities in 21 seconds
- Query response: < 2ms average
- Incremental indexing: < 2 seconds

### Testing
- 182 unit and integration tests
- 80%+ code coverage target
- Async test support with pytest-asyncio

### Supported Platforms
- Python 3.11+
- Linux, macOS, Windows
- MCP Clients: Claude Desktop, VS Code, Cursor, Windsurf

---

## [Unreleased]

### Planned
- Go language support
- Java language support
- Performance optimizations for 100k+ line repositories
- MkDocs documentation site
- GitHub Actions CI/CD pipeline

---

[0.1.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.1.0
[Unreleased]: https://github.com/nahisaho/CodeGraphMCPServer/compare/v0.1.0...HEAD
