# Changelog

[🇯🇵 日本語版](CHANGELOG.ja.md)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] - 2025-12-11

### Added

#### New Language Support (4 languages)
- **Kotlin** (`kotlin.py`): Classes, interfaces, objects, functions, properties
  - Supported extensions: `.kt`, `.kts`
  - tree-sitter-kotlin >= 1.0.0
- **Swift** (`swift.py`): Classes, structs, protocols, functions, extensions
  - Supported extensions: `.swift`
  - tree-sitter-swift >= 0.0.1
- **Scala** (`scala.py`): Classes, traits, objects, functions
  - Supported extensions: `.scala`, `.sc`
  - tree-sitter-scala >= 0.20.0
- **Lua** (`lua.py`): Functions, local functions, table assignments
  - Supported extensions: `.lua`
  - tree-sitter-lua >= 0.1.0

### Changed
- Total supported languages: **16** (was 12)
- Updated parser.py with LANGUAGE_EXTENSIONS for new languages
- Updated `__init__.py` with new extractor registrations

### Tests
- Added 26 new tests for Kotlin, Swift, Scala, Lua extractors
- Total: **334 passed**, 1 skipped

---

## [0.7.1] - 2025-11-27

### Added

#### C Language Support
- Added `.c` file extension support (pure C language)
- C files are parsed using tree-sitter-cpp parser
- Supported extensions: `.c`, `.cpp`, `.cc`, `.cxx`, `.h`, `.hpp`, `.hxx`
- Total supported languages: **12** (was 11)

#### Qiita Article Metadata
- Added Qiita frontmatter (tags, private, updated_at, etc.)

### Changed
- Updated cpp.py extractor docstring to "C/C++-specific"
- Updated parser.py LANGUAGE_EXTENSIONS with C/C++ mappings

---

## [0.7.0] - 2025-11-27

### Added

#### File Watching (`watch` command)
- **`codegraph-mcp watch`**: Watch repository and auto-reindex on file changes
  - Real-time file monitoring with configurable debounce
  - `--debounce` option for delay between changes (default: 1.0s)
  - `--community` flag to run community detection after each reindex
  - Filters to supported language files only
  - Graceful shutdown with Ctrl+C

#### GitHub Actions CI/CD
- **CI Workflow** (`.github/workflows/ci.yml`):
  - Runs on push/PR to main branch
  - Tests on Python 3.11 and 3.12
  - Linting with ruff, type checking with mypy
  - Coverage reporting to Codecov
  - Build verification
- **Release Workflow** (`.github/workflows/release.yml`):
  - Triggers on version tags (v*)
  - Runs tests before release
  - Creates GitHub Release with artifacts
  - Auto-publishes to PyPI

### Tests
- Added 8 new CLI tests for watch command
- Total: 308 passed, 1 skipped

---

## [0.6.2] - 2025-11-27

### Added

#### Entity ID Partial Matching
- **`resolve_entity_id()`**: Resolve partial entity IDs to full IDs
  - Exact match, name match, qualified_name suffix match
  - `file::name` pattern support (e.g., `linux.rs::hashmap_random_keys`)
- **`search_entities()`**: Pattern-based entity search
- Partial ID support in `find_callers()`, `find_callees()`, `find_dependencies()`

#### Auto Community Detection
- **`--community` flag** (default): Auto-detect communities after indexing
- **`--no-community` flag**: Skip community detection for large repositories
- Displays community count and modularity in index results

#### Enhanced query_codebase
- **Relevance scoring**: Exact match (1.0), starts with (0.8), contains (0.6)
- **`include_related`**: Include related entities in results
- **`include_community`**: Include community information
- **`entity_types` filter**: Filter by function, class, method, etc.
- Score and community_id included in JSON output

#### Incremental Community Update
- **`update_incremental()`**: Reassign changed entities to best-fit communities
- 20% change threshold triggers full re-detection
- `IndexResult.changed_entity_ids` for tracking changes

### Changed

#### Community Detection Performance
- **Batch graph building**: `add_nodes_from()` / `add_edges_from()` for speed
- **Batch DB writes**: `executemany()` for community storage
- **Large graph sampling**: `max_nodes=50000` with degree-based sampling
- Successfully processes 230K+ entity repositories

### Tests
- Added 6 new tests for scoring and community integration
- Total: 300 passed, 1 skipped

---

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
- Web UI for graph visualization

---

[0.7.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.7.0
[0.6.2]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.6.2
[0.6.1]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.6.1
[0.6.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.6.0
[0.5.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.5.0
[0.4.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.4.0
[0.3.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.3.0
[0.2.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.2.0
[0.1.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.1.0
[Unreleased]: https://github.com/nahisaho/CodeGraphMCPServer/compare/v0.7.0...HEAD
