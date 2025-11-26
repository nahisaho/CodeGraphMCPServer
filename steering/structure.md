# Project Structure

**Project**: CodeGraph MCP Server
**Last Updated**: 2025-11-27
**Version**: 2.1
**Synced With**: design-architecture-overview.md, design-core-engine.md, design-mcp-interface.md, design-storage.md, pyproject.toml (v0.5.0)

---

## Architecture Pattern

**Primary Pattern**: MCP Native Server with Library-First Architecture (ADR-001)

CodeGraph MCP Serverは、Microsoft GraphRAGのコンセプトを参考に、ソースコード分析に最適化されたMCPサーバーです。外部データベース不要の自己完結型アーキテクチャを採用し、シングルバイナリまたはpip installで即座に利用可能です。

---

## Directory Organization

### Root Structure

```
codegraph-mcp/
├── pyproject.toml           # Project configuration
├── README.md                # Project documentation
├── LICENSE                  # License file
├── src/
│   └── codegraph_mcp/       # Main package
│       ├── __init__.py
│       ├── __main__.py      # CLI entry point (REQ-CLI-001~004)
│       ├── server.py        # MCP Server main (REQ-TRP-001~005)
│       ├── config.py        # Configuration management
│       │
│       ├── core/            # Core engine (Library-First)
│       │   ├── __init__.py
│       │   ├── parser.py    # Tree-sitter AST parser (REQ-AST-001~005)
│       │   ├── graph.py     # Graph engine (REQ-GRF-001~006)
│       │   ├── indexer.py   # Index management (REQ-IDX-001~004)
│       │   ├── community.py # Community detection (REQ-SEM-003~004)
│       │   └── semantic.py  # Semantic analysis (REQ-SEM-001~002)
│       │
│       ├── storage/         # Storage layer
│       │   ├── __init__.py
│       │   ├── sqlite.py    # SQLite storage (REQ-STR-001)
│       │   ├── cache.py     # File cache (REQ-STR-002)
│       │   └── vectors.py   # Vector store (REQ-STR-003)
│       │
│       ├── mcp/             # MCP interface layer
│       │   ├── __init__.py
│       │   ├── tools.py     # MCP Tools - 14 tools (REQ-TLS-001~014)
│       │   ├── resources.py # MCP Resources - 4 types (REQ-RSC-001~004)
│       │   └── prompts.py   # MCP Prompts - 6 prompts (REQ-PRM-001~006)
│       │
│       ├── languages/       # Language support
│       │   ├── __init__.py
│       │   ├── config.py    # Language configurations
│       │   ├── python.py    # Python parser
│       │   ├── typescript.py # TypeScript parser
│       │   └── rust.py      # Rust parser
│       │
│       └── utils/           # Utilities
│           ├── __init__.py
│           ├── git.py       # Git operations (REQ-STR-004)
│           └── logging.py   # Logging utilities
│
├── tests/                   # Test suites
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests (Article IX)
│   ├── e2e/                 # End-to-end tests
│   └── fixtures/            # Test fixtures
│
├── examples/                # Example configurations
│   ├── claude_desktop_config.json
│   └── sample_queries.md
│
├── steering/                # Project memory (MUSUBI SDD)
│   ├── structure.md         # This file
│   ├── tech.md              # Technology stack
│   ├── product.md           # Product context
│   └── rules/               # Constitutional governance
│
├── storage/                 # SDD artifacts
│   ├── specs/               # Requirements, design, tasks
│   ├── changes/             # Delta specifications
│   └── features/            # Feature tracking
│
└── templates/               # Document templates
```

---

## Library-First Pattern (Article I)

### Core Libraries

すべての機能は独立したライブラリとして `src/codegraph_mcp/core/` に実装されます。

#### 1. AST Parser Library (`core/parser.py`)

```python
# REQ-AST-001 ~ REQ-AST-005 を実装
class ASTParser:
    """Tree-sitterベースのAST解析ライブラリ"""
    
    def parse_file(self, file_path: str, language: str) -> ParseResult:
        """ファイルを解析してAST情報を抽出"""
        
    def extract_entities(self, ast: Tree) -> list[Entity]:
        """ASTからエンティティ（関数、クラス等）を抽出"""
```

#### 2. Graph Engine Library (`core/graph.py`)

```python
# REQ-GRF-001 ~ REQ-GRF-006 を実装
class GraphEngine:
    """SQLiteベースのグラフエンジンライブラリ"""
    
    def add_entity(self, entity: Entity) -> str:
        """エンティティをグラフに追加"""
        
    def add_relation(self, source_id: str, target_id: str, type: str) -> int:
        """関係をグラフに追加"""
        
    def query(self, query: GraphQuery) -> QueryResult:
        """グラフクエリを実行"""
```

#### 3. Semantic Analyzer Library (`core/semantic.py`)

```python
# REQ-SEM-001 ~ REQ-SEM-004 を実装
class SemanticAnalyzer:
    """LLMベースのセマンティック分析ライブラリ"""
    
    async def generate_description(self, entity: Entity) -> str:
        """エンティティの自然言語説明を生成"""
        
    async def generate_community_summary(self, community: Community) -> str:
        """コミュニティの要約を生成"""
```

#### 4. Indexer Library (`core/indexer.py`)

```python
# REQ-IDX-001 ~ REQ-IDX-004 を実装
class Indexer:
    """リポジトリインデックス管理ライブラリ"""
    
    def index_repository(self, path: str, incremental: bool = True) -> IndexResult:
        """リポジトリをインデックス"""
        
    def get_changed_files(self, path: str) -> list[str]:
        """Git差分から変更ファイルを取得"""
```

### Library Guidelines

- **Independence**: ライブラリはアプリケーションコードに依存しない
- **Public API**: すべてのエクスポートは `__init__.py` 経由
- **Testing**: 独立したテストスイート
- **CLI**: 各ライブラリはCLIインターフェースを公開（Article II）

---

## CLI Interface (Article II)

### CLI Entry Point (`__main__.py`)

```bash
# サーバー起動
codegraph-mcp serve --repo /path/to/project

# インデックス作成
codegraph-mcp index /path/to/project

# クエリ実行（デバッグ用）
codegraph-mcp query "find all functions that call authenticate"

# ヘルプ表示
codegraph-mcp --help
```

### CLI Commands

| コマンド | 説明 | 要件ID |
|----------|------|--------|
| `serve` | MCPサーバーを起動 | REQ-CLI-001 |
| `index` | リポジトリをインデックス | REQ-IDX-001 |
| `query` | グラフクエリを実行 | REQ-TLS-001 |
| `stats` | 統計情報を表示 | REQ-RSC-004 |

---

## MCP Interface Organization

### Tools (`mcp/tools.py`)

14ツールを以下のカテゴリで整理:

```python
# グラフクエリツール (REQ-TLS-001 ~ REQ-TLS-006)
- query_codebase
- find_dependencies
- find_callers
- find_callees
- find_implementations
- analyze_module_structure

# コード取得ツール (REQ-TLS-007 ~ REQ-TLS-009)
- get_code_snippet
- read_file_content
- get_file_structure

# GraphRAGツール (REQ-TLS-010 ~ REQ-TLS-011)
- global_search
- local_search

# 編集・管理ツール (REQ-TLS-012 ~ REQ-TLS-014)
- suggest_refactoring
- reindex_repository
- execute_shell_command
```

### Resources (`mcp/resources.py`)

4リソースタイプ:

```python
# REQ-RSC-001 ~ REQ-RSC-004
- codegraph://entities/{entity_id}
- codegraph://files/{file_path}
- codegraph://communities/{community_id}
- codegraph://stats
```

### Prompts (`mcp/prompts.py`)

6プロンプトテンプレート:

```python
# REQ-PRM-001 ~ REQ-PRM-006
- code_review
- explain_codebase
- implement_feature
- debug_issue
- refactor_guidance
- test_generation
```

---

## Storage Layer Organization

### SQLite Schema (`storage/sqlite.py`)

```sql
-- エンティティテーブル (REQ-GRF-003)
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    qualified_name TEXT,
    file_path TEXT,
    start_line INTEGER,
    end_line INTEGER,
    signature TEXT,
    docstring TEXT,
    source_code TEXT,
    embedding BLOB,
    community_id INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 関係テーブル (REQ-GRF-004)
CREATE TABLE relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    type TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    metadata TEXT,
    FOREIGN KEY (source_id) REFERENCES entities(id),
    FOREIGN KEY (target_id) REFERENCES entities(id)
);

-- コミュニティテーブル (REQ-SEM-003)
CREATE TABLE communities (
    id INTEGER PRIMARY KEY,
    level INTEGER NOT NULL,
    name TEXT,
    summary TEXT,
    member_count INTEGER,
    created_at TIMESTAMP
);

-- インデックス (REQ-GRF-006)
CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_entities_file ON entities(file_path);
CREATE INDEX idx_entities_community ON entities(community_id);
CREATE INDEX idx_relations_source ON relations(source_id);
CREATE INDEX idx_relations_target ON relations(target_id);
CREATE INDEX idx_relations_type ON relations(type);
```

---

## Test Organization

### Test Structure

```
tests/
├── unit/                    # ユニットテスト
│   ├── test_parser.py       # ASTパーサーテスト
│   ├── test_graph.py        # グラフエンジンテスト
│   └── test_semantic.py     # セマンティック分析テスト
├── integration/             # 統合テスト (Article IX)
│   ├── test_indexer.py      # インデクサー統合テスト
│   ├── test_tools.py        # MCPツール統合テスト
│   └── test_mcp_server.py   # MCPサーバー統合テスト
├── e2e/                     # E2Eテスト
│   └── test_client_workflow.py
└── fixtures/
    ├── sample_repos/        # テスト用サンプルリポジトリ
    │   ├── python_project/
    │   └── typescript_project/
    └── expected_outputs/    # 期待される出力
```

### Test Guidelines (Article III, IX)

- **Test-First**: テストは実装前に作成
- **Real Services**: 統合テストは実際のSQLiteを使用
- **Coverage**: 最低80%のカバレッジ
- **Naming**: `test_*.py` または `*_test.py`

---

## Requirements Traceability

### Component → Requirements Mapping

| コンポーネント | 要件ID | 説明 |
|---------------|--------|------|
| `core/parser.py` | REQ-AST-001 ~ REQ-AST-005 | ASTパーサー |
| `core/graph.py` | REQ-GRF-001 ~ REQ-GRF-006 | グラフエンジン |
| `core/semantic.py` | REQ-SEM-001 ~ REQ-SEM-004 | セマンティック分析 |
| `core/indexer.py` | REQ-IDX-001 ~ REQ-IDX-004 | インデックス管理 |
| `storage/sqlite.py` | REQ-STR-001, REQ-GRF-005 | SQLiteストレージ |
| `storage/cache.py` | REQ-STR-002 | ファイルキャッシュ |
| `storage/vectors.py` | REQ-STR-003 | ベクトルストア |
| `mcp/tools.py` | REQ-TLS-001 ~ REQ-TLS-014 | MCPツール |
| `mcp/resources.py` | REQ-RSC-001 ~ REQ-RSC-004 | MCPリソース |
| `mcp/prompts.py` | REQ-PRM-001 ~ REQ-PRM-006 | MCPプロンプト |
| `server.py` | REQ-TRP-001 ~ REQ-TRP-005 | MCPサーバー |
| `__main__.py` | REQ-CLI-001 ~ REQ-CLI-004 | CLI |

---

## Deployment Structure

### Deployment Units

**Projects** (independently deployable):

1. **codegraph-mcp** - Main MCP server package (pip installable)

> ✅ **Simplicity Gate (Article VII)**: 1 project - compliant

### Distribution

- **PyPI**: `pip install codegraph-mcp`
- **GitHub Releases**: Pre-built binaries (optional)

---

## Naming Conventions

### File Naming

- **Python Modules**: `snake_case.py` (e.g., `ast_parser.py`)
- **Classes**: `PascalCase` (e.g., `GraphEngine`)
- **Functions/Methods**: `snake_case` (e.g., `find_callers`)
- **Constants**: `SCREAMING_SNAKE_CASE` (e.g., `MAX_DEPTH`)
- **Tests**: `test_*.py` (e.g., `test_parser.py`)

### Variable Naming

- **Variables**: `snake_case`
- **Constants**: `SCREAMING_SNAKE_CASE`
- **Types**: `PascalCase`
- **Private members**: `_leading_underscore`

---

## Version Control

### Branch Organization

- `main` - Production branch
- `develop` - Development branch
- `feature/*` - Feature branches
- `hotfix/*` - Hotfix branches

### Commit Message Convention

```
<type>(<scope>): <subject>

<body>

Refs: <REQ-ID>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Example**:
```
feat(parser): implement Python AST parsing

Add Tree-sitter based Python parsing with function,
class, and import extraction.

Refs: REQ-AST-001
```

---

## Constitutional Compliance

This structure enforces:

- **Article I**: Library-first pattern in `core/`
- **Article II**: CLI interfaces via `__main__.py`
- **Article III**: Test structure supports Test-First
- **Article VI**: Steering files maintain project memory
- **Article VII**: Single project - compliant
- **Article VIII**: Direct framework usage (no abstraction layers)
- **Article IX**: Integration tests use real SQLite

---

## Implementation Status (Phase 4 Complete)

### Core Modules ✅

| File | Lines | Status | Description |
|------|-------|--------|-------------|
| `core/parser.py` | ~400 | ✅ Complete | Tree-sitter AST解析 |
| `core/graph.py` | ~500 | ✅ Complete | NetworkXグラフエンジン |
| `core/indexer.py` | ~350 | ✅ Complete | リポジトリインデクサー |
| `core/community.py` | ~200 | ✅ Complete | Louvainコミュニティ検出 |
| `core/semantic.py` | ~300 | ✅ Complete | セマンティック分析 |
| `core/llm.py` | ~350 | ✅ Complete | マルチプロバイダーLLM統合 |
| `core/graphrag.py` | ~300 | ✅ Complete | GraphRAG検索 |

### Language Modules ✅ (11 Languages in v0.3.0+)

| File | Lines | Status | Description |
|------|-------|--------|-------------|
| `languages/python.py` | ~200 | ✅ Complete | Python ASTエクストラクター |
| `languages/typescript.py` | ~250 | ✅ Complete | TypeScript ASTエクストラクター |
| `languages/javascript.py` | ~100 | ✅ Complete | JavaScript ASTエクストラクター |
| `languages/rust.py` | ~300 | ✅ Complete | Rust ASTエクストラクター |
| `languages/go.py` | ~250 | ✅ v0.2.0 | Go ASTエクストラクター |
| `languages/java.py` | ~280 | ✅ v0.2.0 | Java ASTエクストラクター |
| `languages/php.py` | ~250 | ✅ v0.3.0 | PHP ASTエクストラクター |
| `languages/csharp.py` | ~280 | ✅ v0.3.0 | C# ASTエクストラクター |
| `languages/cpp.py` | ~300 | ✅ v0.3.0 | C++ ASTエクストラクター |
| `languages/hcl.py` | ~200 | ✅ v0.3.0 | HCL (Terraform) ASTエクストラクター |
| `languages/ruby.py` | ~250 | ✅ v0.3.0 | Ruby ASTエクストラクター |

### MCP Modules ✅

| File | Lines | Status | Description |
|------|-------|--------|-------------|
| `mcp/tools.py` | ~600 | ✅ Complete | 14 MCPツール |
| `mcp/resources.py` | ~200 | ✅ Complete | 4 MCPリソース |
| `mcp/prompts.py` | ~300 | ✅ Complete | 6 MCPプロンプト |

### Storage Modules ✅

| File | Lines | Status | Description |
|------|-------|--------|-------------|
| `storage/sqlite.py` | ~400 | ✅ Complete | SQLiteストレージ |
| `storage/cache.py` | ~150 | ✅ Complete | ファイルキャッシュ |
| `storage/vectors.py` | ~250 | ✅ Complete | ベクトルストア |

### Documentation ✅

| File | Status | Description |
|------|--------|-------------|
| `docs/api.md` | ✅ Complete | API リファレンス |
| `docs/configuration.md` | ✅ Complete | 設定ガイド |
| `docs/examples.md` | ✅ Complete | 使用例 |
| `CHANGELOG.md` | ✅ Complete | 変更履歴 |
| `RELEASE_NOTES.md` | ✅ Complete | リリースノート |

### Test Coverage (v0.5.0)

| Directory | Tests | Status |
|-----------|-------|--------|
| `tests/unit/` | 200+ | ✅ All Pass |
| `tests/integration/` | 50+ | ✅ All Pass |
| `tests/e2e/` | 10+ | ✅ All Pass |
| **Total** | **286** | **285 passed, 1 skipped** |

### Release Artifacts (v0.5.0)

| File | Size | Status |
|------|------|--------|
| `codegraph_mcp_server-0.5.0-py3-none-any.whl` | ~110KB | ✅ PyPI Published |
| `codegraph_mcp_server-0.5.0.tar.gz` | ~118KB | ✅ PyPI Published |

### Release History

| Version | Date | Highlights |
|---------|------|------------|
| v0.1.0 | 2025-11-26 | Initial: Python, TS, JS, Rust |
| v0.2.0 | 2025-11-27 | +Go, Java |
| v0.3.0 | 2025-11-27 | +PHP, C#, C++, HCL, Ruby (11 languages) |
| v0.4.0 | 2025-11-27 | CLI Progress Display |
| **v0.5.0** | **2025-11-27** | **47x Performance (Batch DB)** |

---

## Changelog

### Version 2.3 (2025-11-27)

- v0.5.0リリースに伴う更新
- 11言語パーサーモジュール追記
- テストカウント: 286（285 passed, 1 skipped）
- パフォーマンス改善: 47x高速化（バッチDB書き込み）
- Release History追加

### Version 2.2 (2025-11-26)

- Phase 4完了を反映
- Language Modules追加（javascript.py）
- Documentation追加（docs/）
- Release Artifacts追加
- テスト数: 173 → 182

### Version 2.1 (2025-11-26)

- Phase 3完了に伴う実装ステータス追加
- 全モジュールの実装状況を記録
- テストカバレッジ情報追加

### Version 2.0 (2025-11-26)

- 設計書（design-*.md）との同期
- ADR-001参照追加
- 設計書へのトレーサビリティ追加

### Version 1.1 (2025-11-26)

- Updated based on requirements specification
- Added component → requirements traceability
- Added MCP interface organization
- Added storage layer schema
- Added naming conventions

### Version 1.0 (2025-11-26)

- Initial structure

---

**Last Updated**: 2025-11-27
**Maintained By**: MUSUBI SDD
