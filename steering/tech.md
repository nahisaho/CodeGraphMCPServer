# Technology Stack

**Project**: CodeGraph MCP Server
**Last Updated**: 2025-11-27
**Version**: 2.4
**Synced With**: design-adr.md (ADR-001〜010), pyproject.toml (v0.6.2)

---

## Overview

本ドキュメントはCodeGraph MCP Serverの承認済み技術スタックを定義します。すべての開発は、Phase -1 Gate（Article VIII: Anti-Abstraction）で明示的に承認されない限り、これらの技術を使用する必要があります。

**アーキテクチャ決定**: 技術選定の根拠は `storage/specs/design-adr.md` を参照してください。

---

## Primary Technologies

### Programming Language

| 言語 | バージョン | 用途 | 備考 |
|------|-----------|------|------|
| Python | 3.11+ | アプリケーション言語 | REQ-NFR-009 |
| SQL | SQLite 3 | データベースクエリ | SQLiteネイティブ |

### Runtime Environment

- **Python**: 3.11+ (REQ-NFR-009)
- **Package Manager**: pip / uv

---

## Core Dependencies

### MCP SDK (ADR-004)

| ライブラリ | バージョン | 用途 | 要件ID | ADR |
|-----------|-----------|------|--------|-----|
| mcp | >=1.0.0 | MCP Protocol SDK | REQ-TRP-001~005 | ADR-004 |

### AST Parsing - Tree-sitter (ADR-003)

| ライブラリ | バージョン | 用途 | 要件ID | ADR |
|-----------|-----------|------|--------|-----|
| tree-sitter | >=0.21.0 | AST解析基盤 | REQ-AST-001~005 | ADR-003 |
| tree-sitter-python | >=0.21.0 | Python解析 | REQ-AST-001 | |
| tree-sitter-javascript | >=0.21.0 | JavaScript解析 | ✅ | |
| tree-sitter-typescript | >=0.21.0 | TypeScript解析 | REQ-AST-002 | |
| tree-sitter-rust | >=0.21.0 | Rust解析 | REQ-AST-003 | |
| tree-sitter-go | >=0.21.0 | Go解析 | ✅ v0.2.0 | |
| tree-sitter-java | >=0.21.0 | Java解析 | ✅ v0.2.0 | |
| tree-sitter-php | >=0.21.0 | PHP解析 | ✅ v0.3.0 | |
| tree-sitter-c-sharp | >=0.21.0 | C#解析 | ✅ v0.3.0 | |
| tree-sitter-cpp | >=0.21.0 | C++解析 | ✅ v0.3.0 | |
| tree-sitter-hcl | >=0.21.0 | HCL (Terraform)解析 | ✅ v0.3.0 | |
| tree-sitter-ruby | >=0.21.0 | Ruby解析 | ✅ v0.3.0 | |

### Database & Storage (ADR-002)

| ライブラリ | バージョン | 用途 | 要件ID | ADR |
|-----------|-----------|------|--------|-----|
| aiosqlite | >=0.19.0 | 非同期SQLite | REQ-STR-001, REQ-GRF-005 | ADR-002 |

### Data Validation (ADR-006)

| ライブラリ | バージョン | 用途 | ADR |
|-----------|-----------|------|-----|
| pydantic | >=2.0.0 | データバリデーション・シリアライズ | ADR-006 |
| pydantic-settings | >=2.0.0 | 環境変数管理 | - |

### Graph Algorithms (ADR-005)

| ライブラリ | バージョン | 用途 | 要件ID | ADR |
|-----------|-----------|------|--------|-----|
| networkx | >=3.0 | グラフアルゴリズム（Louvain, PageRank等） | REQ-SEM-003 | ADR-005 |

### Vector Operations

| ライブラリ | バージョン | 用途 | 要件ID |
|-----------|-----------|------|--------|
| numpy | >=1.24.0 | ベクトル演算 | REQ-STR-003 |

### Utilities

| ライブラリ | バージョン | 用途 | 要件ID |
|-----------|-----------|------|--------|
| tiktoken | >=0.5.0 | トークンカウント | - |
| watchfiles | >=0.21.0 | ファイル監視 | - |
| gitpython | >=3.1.0 | Git操作 | REQ-STR-004 |
| rich | >=13.0.0 | CLIフォーマット | REQ-CLI-003 |
| typer | >=0.9.0 | CLIフレームワーク | REQ-CLI-001~004 |

---

## Optional Dependencies

### Embeddings (Optional)

| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| sentence-transformers | >=2.2.0 | ローカルエンベディング |

### OpenAI Integration (Optional)

| ライブラリ | バージョン | 用途 | 要件ID |
|-----------|-----------|------|--------|
| openai | >=1.0.0 | OpenAI API | REQ-SEM-001~002 |

### Anthropic Integration (Optional)

| ライブラリ | バージョン | 用途 | 要件ID |
|-----------|-----------|------|--------|
| anthropic | >=0.18.0 | Anthropic Claude API | REQ-SEM-001~002 |

---

## Implemented Modules (as of Phase 3)

### Core Modules

| Module | File | Description | Status |
|--------|------|-------------|--------|
| Parser | `core/parser.py` | Tree-sitter AST解析 | ✅ Implemented |
| Graph | `core/graph.py` | NetworkXグラフエンジン | ✅ Implemented |
| Indexer | `core/indexer.py` | リポジトリインデクサー | ✅ Implemented |
| Community | `core/community.py` | Louvainコミュニティ検出 | ✅ Implemented |
| Semantic | `core/semantic.py` | セマンティック分析 | ✅ Implemented |
| LLM | `core/llm.py` | マルチプロバイダーLLM統合 | ✅ Implemented |
| GraphRAG | `core/graphrag.py` | GraphRAG検索 | ✅ Implemented |

### MCP Modules

| Module | File | Description | Status |
|--------|------|-------------|--------|
| Tools | `mcp/tools.py` | MCPツール（14種） | ✅ Implemented |
| Resources | `mcp/resources.py` | MCPリソース（4種） | ✅ Implemented |
| Prompts | `mcp/prompts.py` | MCPプロンプト（6種） | ✅ Implemented |

### Storage Modules

| Module | File | Description | Status |
|--------|------|-------------|--------|
| SQLite | `storage/sqlite.py` | SQLiteストレージ | ✅ Implemented |
| Cache | `storage/cache.py` | ファイルキャッシュ | ✅ Implemented |
| Vectors | `storage/vectors.py` | ベクトルストア | ✅ Implemented |

---

## pyproject.toml Configuration

```toml
[project]
name = "codegraph-mcp"
version = "0.1.0"
requires-python = ">=3.11"
description = "MCP Server for code graph analysis with GraphRAG capabilities"
authors = [
    {name = "Your Name", email = "your@email.com"}
]
license = {text = "MIT"}
readme = "README.md"
keywords = ["mcp", "code-analysis", "graphrag", "ast", "tree-sitter"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "mcp>=1.0.0",
    "tree-sitter>=0.21.0",
    "tree-sitter-python>=0.21.0",
    "tree-sitter-javascript>=0.21.0",
    "tree-sitter-typescript>=0.21.0",
    "tree-sitter-rust>=0.21.0",
    "aiosqlite>=0.19.0",
    "pydantic>=2.0.0",
    "networkx>=3.0",
    "numpy>=1.24.0",
    "tiktoken>=0.5.0",
    "watchfiles>=0.21.0",
    "gitpython>=3.1.0",
    "rich>=13.0.0",
    "typer>=0.9.0",
]

[project.optional-dependencies]
embeddings = [
    "sentence-transformers>=2.2.0",
]
openai = [
    "openai>=1.0.0",
]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[project.scripts]
codegraph-mcp = "codegraph_mcp.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/codegraph_mcp"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.mypy]
python_version = "3.11"
strict = true
```

---

## Testing Stack

### Test Frameworks

| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| pytest | >=7.0.0 | テストランナー |
| pytest-asyncio | >=0.21.0 | 非同期テスト |
| pytest-cov | >=4.0.0 | カバレッジ |

### Test Guidelines (Article III, IX)

- **Unit Tests**: モック使用可、ライブラリごとに独立
- **Integration Tests**: 実際のSQLiteを使用（Article IX）
- **Coverage**: 最低80%

---

## Code Quality Tools

| ツール | バージョン | 用途 |
|--------|-----------|------|
| ruff | >=0.1.0 | Linter & Formatter |
| mypy | >=1.0.0 | 型チェック |

### Ruff Configuration

```toml
[tool.ruff]
target-version = "py311"
line-length = 100
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = []

[tool.ruff.isort]
known-first-party = ["codegraph_mcp"]
```

---

## Performance Requirements

| 指標 | 目標値 | 実測値 (v0.5.0) | 要件ID |
|------|--------|-----------------|--------|
| 初回インデックス (10万行) | < 30秒 | **0.63秒** (67 files, 942 entities) | REQ-NFR-001 |
| 増分インデックス | < 2秒 | < 0.5秒 | REQ-NFR-002 |
| クエリレスポンス | < 500ms | < 2ms | REQ-NFR-003 |
| 起動時間 | < 2秒 | < 1秒 | REQ-NFR-004 |
| メモリ使用量 | < 500MB | ~200MB | REQ-NFR-005 |
| ディスク使用量 | < 100MB/10万行 | ~5MB | REQ-NFR-006 |
| エンティティ/秒 | - | **1,495** (47x improved in v0.5.0) | - |

---

## Development Tools

### Recommended IDE

- **Visual Studio Code** with extensions:
  - Python
  - Pylance
  - Ruff
  - GitLens

### Database Tools

| ツール | 用途 |
|--------|------|
| DB Browser for SQLite | SQLiteデータ確認 |
| SQLite CLI | コマンドライン操作 |

---

## Anti-Abstraction Policy (Article VIII)

**CRITICAL**: フレームワークAPIを直接使用してください。カスタム抽象化レイヤーは作成しないでください。

### ✅ 許可

```python
# Tree-sitterを直接使用
parser = tree_sitter.Parser()
parser.set_language(tree_sitter_python.language())
tree = parser.parse(source_code)

# aiosqliteを直接使用
async with aiosqlite.connect(db_path) as db:
    await db.execute("INSERT INTO entities ...")

# MCPを直接使用
@mcp.tool()
async def query_codebase(query: str) -> list[CodeEntity]:
    ...
```

### ❌ 禁止（Phase -1 Gate承認なし）

```python
# ❌ カスタムデータベースラッパー
class MyDatabase:
    async def find(self, id: str): ...  # aiosqliteをラップ

# ❌ カスタムパーサーラッパー
class MyParser:
    def parse(self, code: str): ...  # Tree-sitterをラップ
```

---

## Security Requirements

| 要件 | 説明 | 要件ID |
|------|------|--------|
| シェルコマンド実行 | タイムアウト制限を適用 | REQ-NFR-012 |
| ファイルアクセス | 指定リポジトリパスに制限 | REQ-NFR-013 |

---

## Compatibility Requirements

| 対象 | 要件 | 要件ID |
|------|------|--------|
| Python | 3.11+ | REQ-NFR-009 |
| MCP Specification | 1.0 | REQ-NFR-010 |
| MCPクライアント | GitHub Copilot, Claude Code, Cursor, Windsurf | REQ-NFR-011 |

---

## Changelog

### Version 2.3 (2025-11-27)

- v0.6.0-dev 機能追加:
  - `resolve_entity_id()`: 部分一致ID解決
  - `search_entities()`: パターンベース検索
  - `update_incremental()`: 増分コミュニティ更新
  - `GraphQuery.include_related/include_community`: 拡張クエリオプション
  - `QueryResult.scores/communities`: スコアリング・コミュニティ情報
- IndexResultに`changed_entity_ids`追加
- テスト: 300 passed

### Version 2.4 (2025-11-27)

- v0.6.2リリース:
  - コミュニティ検出最適化: `add_nodes_from()`/`add_edges_from()` バッチ処理
  - `executemany()` によるDB書き込み最適化
  - `max_nodes=50000` サンプリングによる大規模グラフ対応
  - 230K+エンティティ（Rustコンパイラ）で検証済み
- テスト: 300 passed

### Version 2.3 (2025-11-27)

- v0.6.0-dev機能追加
- テスト: 294 passed

### Version 2.2 (2025-11-27)

- v0.5.0リリースに伴う更新
- 11言語サポート（PHP, C#, C++, HCL, Ruby追加）
- パフォーマンス実測値追加（47x改善）
- バッチDB書き込みによる最適化

### Version 2.1 (2025-11-26)

- Phase 3実装完了に伴う更新
- Anthropic SDK追加（LLM統合）
- Implemented Modulesセクション追加

### Version 2.0 (2025-11-26)

- ADR参照を追加（ADR-001〜010）
- 設計書（design-*.md）との同期
- pydantic-settings追加

### Version 1.1 (2025-11-26)

- Updated based on requirements specification
- Added performance requirements mapping
- Added compatibility requirements
- Added security requirements
- Added pyproject.toml configuration

### Version 1.0 (2025-11-26)

- Initial technology stack

---

**Last Updated**: 2025-11-27
**Maintained By**: MUSUBI SDD
