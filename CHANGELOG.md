# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.1] - 2025-11-27

### Fixed

#### SSE Transport
- Fixed SSE endpoint configuration using `Mount` instead of `Route` for `/messages/`
- Added proper `Response()` return to avoid NoneType errors on client disconnect
- Follows official MCP SSE implementation pattern

#### CLI Unicode Compatibility
- Removed Unicode emoji characters that caused encoding errors on some terminals
- Removed `SpinnerColumn` to avoid surrogate encoding issues
- Added `legacy_windows=True` to Rich console for broader compatibility

### Tested
- Successfully indexed Rust compiler repository (230K+ entities, 34K+ files)
- Verified all 14 MCP tools working via SSE transport

---

## [0.6.0] - 2025-11-27

### Added

#### Background Server Management
- **`codegraph-mcp start`**: Start MCP server in background (daemon mode)
  - Default SSE transport on port 8080
  - PID file stored at `~/.codegraph/server.pid`
  - Logs written to `~/.codegraph/server.log`
- **`codegraph-mcp stop`**: Stop background MCP server gracefully
- **`codegraph-mcp status`**: Check server status with recent log output

### Changed
- `codegraph-mcp serve` now explicitly documented as foreground mode
- Background mode uses SSE transport by default (stdio for foreground)

---

## [0.5.0] - 2025-11-27

### Changed

#### Performance Optimization - Batch Database Writes
- **47x faster indexing**: Implemented batch write operations for entities and relations
  - Before: 29.47s for 67 files (32 entities/sec)
  - After: 0.63s for 67 files (1495 entities/sec)
- Reduced database commits from ~5700 per repository to 3
- Added `add_entities_batch()` and `add_relations_batch()` methods to GraphEngine
- Updated Indexer to collect all parse results before batch writing

#### Technical Details
- Uses SQLite `executemany()` for bulk inserts
- Single commit per batch instead of per-entity/relation
- Batch file tracking updates

---

## [0.4.0] - 2025-11-27

### Added

#### CLI Enhancement
- **Rich Progress Display**: Added animated progress bar for `codegraph-mcp index` command
  - Spinner animation with real-time progress bar
  - File-by-file processing display
  - Results table with entity/relation counts and duration
  - Color-coded status messages

#### Performance Metrics (Measured)
- Indexing speed: **32 entities/second**
- File processing: **0.44 seconds/file**
- Incremental indexing: **< 2 seconds**
- Query response: **< 2ms**

### Changed
- Added `rich>=13.0.0` dependency for CLI progress display
- Updated `Indexer.index_repository()` with optional `progress_callback` parameter

---

## [0.3.0] - 2025-11-27

### Added

#### Language Support - 5 New Languages
- **PHP Language Support**: Full AST parsing for PHP source files
  - Class, interface, and trait extraction
  - Method and function extraction
  - Namespace handling
  - Inheritance and implements relation detection

- **C# Language Support**: Comprehensive C# parsing
  - Class, struct, interface, and enum extraction
  - Method, constructor, and property extraction
  - Namespace handling
  - Inheritance relation detection
  - Using directive handling

- **C++ Language Support**: Full C++ parsing
  - Class and struct extraction
  - Function and method extraction (including header declarations)
  - Namespace handling
  - Include directive handling
  - Inheritance relation detection
  - Template class support

- **HCL (Terraform) Language Support**: Infrastructure as Code parsing
  - Resource and data source extraction
  - Variable and output extraction
  - Module and locals block extraction
  - Provider block extraction

- **Ruby Language Support**: Full Ruby parsing
  - Class and module extraction
  - Method and singleton method extraction
  - Inheritance relation detection
  - require/require_relative handling
  - Module include/extend detection

### Changed
- Updated dependencies to include `tree-sitter-php`, `tree-sitter-c-sharp`, `tree-sitter-cpp`, `tree-sitter-hcl`, `tree-sitter-ruby`
- Extended language registry with 5 new extractors

### Testing
- Added 73 new tests for PHP, C#, C++, HCL, and Ruby parsers
- Total tests: 286 (from 212 in v0.2.0)

---

## [0.2.0] - 2025-11-27

### Added

#### Language Support
- **Go Language Support**: Full AST parsing for Go source files
  - Function and method extraction with receiver types
  - Struct and interface extraction
  - Package and import handling
  - Call relation detection

- **Java Language Support**: Comprehensive Java parsing
  - Class, interface, and enum extraction
  - Method and constructor extraction
  - Inheritance (extends/implements) relation detection
  - Import statement handling

### Changed
- Updated dependencies to include `tree-sitter-go` and `tree-sitter-java`
- Extended language registry with Go and Java extractors

### Testing
- Added 30 new tests for Go and Java parsers
- Total tests: 212 (from 182 in v0.1.0)

---

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
- Performance optimizations for 100k+ line repositories
- MkDocs documentation site
- GitHub Actions CI/CD pipeline

---

[0.4.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.4.0
[0.3.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.3.0
[0.2.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.2.0
[0.1.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.1.0
[Unreleased]: https://github.com/nahisaho/CodeGraphMCPServer/compare/v0.4.0...HEAD
