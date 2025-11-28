# CodeGraphMCPServer

**A lightweight, high-performance source code analysis MCP server with zero configuration**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-1.0-green.svg)](https://modelcontextprotocol.io/)
[![Tests](https://img.shields.io/badge/tests-308%20passed-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-64%25-yellow.svg)]()
[![CI](https://github.com/nahisaho/CodeGraphMCPServer/actions/workflows/ci.yml/badge.svg)](https://github.com/nahisaho/CodeGraphMCPServer/actions/workflows/ci.yml)

[🇯🇵 日本語版 README](README.ja.md)

## Overview

CodeGraphMCPServer is an MCP server that understands codebase structure and provides GraphRAG (Graph Retrieval-Augmented Generation) capabilities. With a self-contained architecture requiring no external database, it enables structural understanding and efficient code completion from MCP-compatible AI tools (GitHub Copilot, Claude Desktop, Cursor, etc.).

### 🧠 GraphRAG Features

- **Community Detection**: Automatic code module clustering using Louvain algorithm
- **LLM Integration**: Multi-provider design supporting OpenAI/Anthropic/Local LLMs
- **Global Search**: Codebase-wide understanding using community summaries
- **Local Search**: Context retrieval from entity neighborhoods

### ✨ Features

| Feature | Description |
|---------|-------------|
| 🚀 **Zero Configuration** | No external DB required, `pip install && serve` to start immediately |
| 🌳 **AST Analysis** | Fast and accurate code analysis with Tree-sitter |
| 🔗 **Graph Construction** | Builds graphs of relationships between code entities |
| 🔍 **14 MCP Tools** | Dependency analysis, call tracing, code search |
| 📚 **4 MCP Resources** | Entities, files, communities, statistics |
| 💬 **6 MCP Prompts** | Code review, feature implementation, debug assistance |
| ⚡ **Fast Indexing** | 100K lines in under 30 seconds, incremental updates in under 2 seconds |
| 🌐 **Multi-language Support** | Python, TypeScript, JavaScript, Rust, Go, Java, PHP, C#, C, C++, HCL, Ruby (12 languages) |

## Requirements

- Python 3.11+
- MCP-compatible client (GitHub Copilot, Claude Desktop, Cursor, Windsurf)

## Installation

### Install with pip

```bash
pip install codegraph-mcp-server
```

### Install from source (for development)

```bash
git clone https://github.com/nahisaho/CodeGraphMCPServer.git
cd CodeGraphMCPServer
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -e ".[dev]"
```

## Quick Start

### 1. Index a Repository

```bash
# Full index
codegraph-mcp index /path/to/repository --full

# Incremental index (default)
codegraph-mcp index /path/to/repository

# Auto re-index with file watching (v0.7.0 NEW)
codegraph-mcp watch /path/to/repository
codegraph-mcp watch /path/to/repository --debounce 2.0  # 2 second debounce
codegraph-mcp watch /path/to/repository --community     # Community detection after re-index
```

**Output example:**
```
Indexed 16 entities, 37 relations in 0.81s
```

### 2. Check Statistics

```bash
codegraph-mcp stats /path/to/repository
```

**Output example:**
```
Repository Statistics
=====================
Repository: /path/to/repository

Entities: 16
Relations: 37
Communities: 0
Files: 1

Entities by type:
  - class: 2
  - function: 2
  - method: 11
  - module: 1
```

### 3. Search Code

```bash
codegraph-mcp query "Calculator" --repo /path/to/repository
```

### 4. Start as MCP Server

```bash
# stdio transport (default)
codegraph-mcp serve --repo /path/to/repository

# SSE transport
codegraph-mcp start --repo /path/to/repository --port 8080
```

## MCP Client Configuration

### Claude Desktop

`~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "codegraph": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "/path/to/your/project"]
    }
  }
}
```

### Claude Code

```bash
# stdio transport
claude mcp add codegraph -- codegraph-mcp serve --repo /path/to/project

# HTTP transport (SSE server)
codegraph-mcp start --port 8080  # In another terminal
claude mcp add --transport http codegraph http://0.0.0.0:8080
```

### VS Code (GitHub Copilot)

`.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "codegraph": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "${workspaceFolder}"]
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "codegraph": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "/path/to/your/project"]
    }
  }
}
```

## 🛠 MCP Tools (14)

### Graph Query Tools

| Tool | Description | Main Arguments |
|------|-------------|----------------|
| `query_codebase` | Search code graph with natural language | `query`, `max_results` |
| `find_dependencies` | Find entity dependencies | `entity_id`, `depth` |
| `find_callers` | Find callers of function/method | `entity_id` |
| `find_callees` | Find callees of function/method | `entity_id` |
| `find_implementations` | Find interface implementations | `entity_id` |
| `analyze_module_structure` | Analyze module structure | `file_path` |

### Code Retrieval Tools

| Tool | Description | Main Arguments |
|------|-------------|----------------|
| `get_code_snippet` | Get entity source code | `entity_id`, `include_context` |
| `read_file_content` | Get file content | `file_path`, `start_line`, `end_line` |
| `get_file_structure` | Get file structure overview | `file_path` |

### GraphRAG Tools

| Tool | Description | Main Arguments |
|------|-------------|----------------|
| `global_search` | Cross-community global search | `query` |
| `local_search` | Local search in entity neighborhood | `query`, `entity_id` |

### Management Tools

| Tool | Description | Main Arguments |
|------|-------------|----------------|
| `suggest_refactoring` | Suggest refactoring | `entity_id`, `type` |
| `reindex_repository` | Re-index repository | `incremental` |
| `execute_shell_command` | Execute shell command | `command`, `timeout` |

## 📚 MCP Resources (4)

| URI Pattern | Description |
|-------------|-------------|
| `codegraph://entities/{id}` | Entity details |
| `codegraph://files/{path}` | Entities in file |
| `codegraph://communities/{id}` | Community information |
| `codegraph://stats` | Graph statistics |

## 💬 MCP Prompts (6)

| Prompt | Description | Arguments |
|--------|-------------|-----------|
| `code_review` | Perform code review | `entity_id`, `focus_areas` |
| `explain_codebase` | Explain codebase | `scope`, `detail_level` |
| `implement_feature` | Feature implementation guide | `feature_description`, `constraints` |
| `debug_issue` | Debug assistance | `issue_description`, `context` |
| `refactor_guidance` | Refactoring guide | `entity_id`, `goal` |
| `test_generation` | Test generation | `entity_id`, `test_type` |

## Usage Examples

### Conversation with AI Assistant

```
You: What are the dependencies of the UserService class?

AI: [Using find_dependencies tool]
    UserService depends on:
    - DatabaseConnection (database.py)
    - Logger (utils/logging.py)
    - UserRepository (repositories/user.py)
```

```
You: What would be affected if I modify the authenticate method?

AI: [Using find_callers tool]
    Callers of authenticate:
    - LoginController.login() (controllers/auth.py:45)
    - APIMiddleware.verify_token() (middleware/api.py:23)
    - TestUserService.test_auth() (tests/test_user.py:78)
```

```
You: Explain the main components of this project

AI: [Using global_search tool]
    [Using explain_codebase prompt]
    
    This project uses a 3-tier architecture:
    1. Controllers layer: HTTP request handling
    2. Services layer: Business logic
    3. Repositories layer: Data access
```

## Development

### Run Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src/codegraph_mcp --cov-report=html

# Specific tests
pytest tests/unit/test_parser.py -v
```

### Lint & Format

```bash
# Lint with Ruff
ruff check src tests

# Format with Ruff
ruff format src tests

# Type check with MyPy
mypy src
```

## Architecture

```
src/codegraph_mcp/
├── __init__.py          # Package initialization
├── __main__.py          # CLI entry point
├── server.py            # MCP server
├── config.py            # Configuration management
├── core/                # Core logic
│   ├── parser.py        # Tree-sitter AST parser
│   ├── graph.py         # NetworkX graph engine
│   ├── indexer.py       # Repository indexer
│   ├── community.py     # Community detection (Louvain)
│   ├── semantic.py      # Semantic analysis
│   ├── llm.py           # LLM integration (OpenAI/Anthropic/Local)
│   └── graphrag.py      # GraphRAG search engine
├── storage/             # Storage layer
│   ├── sqlite.py        # SQLite persistence
│   ├── cache.py         # File cache
│   └── vectors.py       # Vector store
├── mcp/                 # MCP interface
│   ├── tools.py         # 14 MCP Tools
│   ├── resources.py     # 4 MCP Resources
│   └── prompts.py       # 6 MCP Prompts
└── languages/           # Language support (12 languages)
    ├── python.py        # Python extractor
    ├── typescript.py    # TypeScript extractor
    ├── javascript.py    # JavaScript extractor
    ├── rust.py          # Rust extractor
    ├── go.py            # Go extractor
    ├── java.py          # Java extractor
    ├── php.py           # PHP extractor
    ├── csharp.py        # C# extractor
    ├── c.py             # C extractor
    ├── cpp.py           # C++ extractor
    ├── hcl.py           # HCL (Terraform) extractor
    └── ruby.py          # Ruby extractor
```

## Performance

### Measured Values (v0.3.0)

| Metric | Measured | Notes |
|--------|----------|-------|
| Indexing speed | **32 entities/sec** | 67 files, 941 entities |
| File processing speed | **0.44 sec/file** | Python/TS/Rust mixed |
| Incremental index | **< 2 sec** | Changed files only |
| Query response | **< 2ms** | Graph search |

### Target Values

| Metric | Target |
|--------|--------|
| Initial index (100K lines) | < 30 sec |
| Incremental index | < 2 sec |
| Query response | < 500ms |
| Startup time | < 2 sec |
| Memory usage | < 500MB |

## License

MIT License - See [LICENSE](LICENSE)

## Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification
- [Tree-sitter](https://tree-sitter.github.io/) - AST analysis
- [NetworkX](https://networkx.org/) - Graph algorithms
- [Microsoft GraphRAG](https://github.com/microsoft/graphrag) - GraphRAG concept

## Related Links

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
