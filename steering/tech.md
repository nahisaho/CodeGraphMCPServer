# Technology Stack

**Project**: CodeGraphMCPServer
**Last Updated**: 2025-12-04
**Version**: 1.1

---

## Overview

CodeGraphMCPServer は MCP (Model Context Protocol) サーバーとして、
コードベースのグラフ分析と GraphRAG 機能を提供する Python パッケージです。

---

## Primary Technologies

### Programming Languages

| Language | Version | Usage | Notes |
|----------|---------|-------|-------|
| **Python** | 3.11+ | メインアプリケーション | asyncio 完全対応 |
| SQL | SQLite 3 | グラフデータ永続化 | aiosqlite 経由 |

### Runtime Environment

- **Python**: 3.11+ (LTS)
- **Package Manager**: pip / uv
- **Virtual Environment**: venv

---

## Core Dependencies

### MCP SDK

| Technology | Version | Purpose |
|------------|---------|---------|
| **mcp** | >= 1.0.0 | Model Context Protocol SDK |

### AST Parsing (Tree-sitter)

| Technology | Version | Purpose |
|------------|---------|---------|
| **tree-sitter** | >= 0.21.0 | AST パーサーコア |
| tree-sitter-python | >= 0.21.0 | Python サポート |
| tree-sitter-typescript | >= 0.21.0 | TypeScript サポート |
| tree-sitter-javascript | >= 0.21.0 | JavaScript サポート |
| tree-sitter-rust | >= 0.21.0 | Rust サポート |
| tree-sitter-go | >= 0.21.0 | Go サポート |
| tree-sitter-java | >= 0.21.0 | Java サポート |
| tree-sitter-php | >= 0.21.0 | PHP サポート |
| tree-sitter-c-sharp | >= 0.21.0 | C# サポート |
| tree-sitter-cpp | >= 0.21.0 | C/C++ サポート |
| tree-sitter-hcl | >= 0.21.0 | HCL (Terraform) サポート |
| tree-sitter-ruby | >= 0.21.0 | Ruby サポート |

### Database & Storage

| Technology | Version | Purpose |
|------------|---------|---------|
| **aiosqlite** | >= 0.19.0 | 非同期 SQLite アクセス |

### Data Validation

| Technology | Version | Purpose |
|------------|---------|---------|
| **pydantic** | >= 2.0.0 | データバリデーション |
| **pydantic-settings** | >= 2.0.0 | 設定管理 |

### Graph Algorithms

| Technology | Version | Purpose |
|------------|---------|---------|
| **networkx** | >= 3.0 | グラフアルゴリズム (Louvain等) |

### CLI & Display

| Technology | Version | Purpose |
|------------|---------|---------|
| **typer** | >= 0.9.0 | CLI フレームワーク |
| **rich** | >= 13.0.0 | ターミナル表示 |

### Utilities

| Technology | Version | Purpose |
|------------|---------|---------|
| **numpy** | >= 1.24.0 | ベクトル演算 |
| **tiktoken** | >= 0.5.0 | トークンカウント |
| **watchfiles** | >= 0.21.0 | ファイル監視 |
| **gitpython** | >= 3.1.0 | Git 操作 |

---

## Optional Dependencies

### Local Embeddings

```bash
pip install codegraph-mcp-server[embeddings]
```

| Technology | Version | Purpose |
|------------|---------|---------|
| sentence-transformers | >= 2.2.0 | ローカル埋め込みモデル |

### OpenAI Integration

```bash
pip install codegraph-mcp-server[openai]
```

| Technology | Version | Purpose |
|------------|---------|---------|
| openai | >= 1.0.0 | OpenAI API 統合 |

### SSE Transport

```bash
pip install codegraph-mcp-server[sse]
```

| Technology | Version | Purpose |
|------------|---------|---------|
| starlette | >= 0.27.0 | ASGI フレームワーク |
| uvicorn | >= 0.23.0 | ASGI サーバー |

---

## Development Dependencies

```bash
pip install codegraph-mcp-server[dev]
```

### Testing

| Technology | Version | Purpose |
|------------|---------|---------|
| **pytest** | >= 7.0.0 | テストフレームワーク |
| **pytest-asyncio** | >= 0.21.0 | 非同期テスト |
| **pytest-cov** | >= 4.0.0 | カバレッジ計測 |

### Code Quality

| Technology | Version | Purpose |
|------------|---------|---------|
| **ruff** | >= 0.1.0 | Linter & Formatter |
| **mypy** | >= 1.0.0 | 型チェック |
| **pre-commit** | >= 3.0.0 | Git フック |

---

## CI/CD Stack

### GitHub Actions

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | push/PR | テスト・リント実行 |
| `release.yml` | tag `v*` | PyPI 公開 |

### Deployment

| Technology | Purpose |
|------------|---------|
| **PyPI** | パッケージ配布 |
| **GitHub Releases** | リリース管理 |

---

## Architecture Decisions (ADRs)

| ADR | Decision | Rationale |
|-----|----------|-----------|
| ADR-001 | Library-First | 再利用可能なコア機能 |
| ADR-002 | SQLite Storage | 外部 DB 不要、ゼロ設定 |
| ADR-003 | Tree-sitter | 高速・正確な AST 解析 |
| ADR-004 | MCP SDK | 標準プロトコル準拠 |
| ADR-005 | NetworkX | 豊富なグラフアルゴリズム |
| ADR-006 | Pydantic | 型安全な設定・バリデーション |

---

## Configuration

### pyproject.toml

パッケージ設定、依存関係、ツール設定を一元管理:

- **[project]**: パッケージメタデータ
- **[project.dependencies]**: 本番依存関係
- **[project.optional-dependencies]**: オプション依存関係
- **[tool.pytest]**: テスト設定
- **[tool.ruff]**: Linter/Formatter 設定
- **[tool.mypy]**: 型チェック設定
- **[tool.coverage]**: カバレッジ設定

### 環境変数

| 変数 | 説明 | デフォルト |
|------|------|-----------|
| `CODEGRAPH_REPO_PATH` | リポジトリパス | `.` |
| `CODEGRAPH_DB_PATH` | DB パス | `.codegraph/graph.db` |
| `CODEGRAPH_LOG_LEVEL` | ログレベル | `INFO` |
| `OPENAI_API_KEY` | OpenAI API キー | - |
| `ANTHROPIC_API_KEY` | Anthropic API キー | - |

---

## Performance Characteristics

### 測定値 (v0.7.2)

| 指標 | 測定値 | 備考 |
|------|--------|------|
| インデックス速度 | 32 entities/sec | 69ファイル、1,004エンティティ |
| インクリメンタル | < 2 sec | 変更ファイルのみ |
| クエリ応答 | < 2ms | グラフ検索 |

### 目標値

| 指標 | 目標 |
|------|------|
| 初回インデックス (100K行) | < 30 sec |
| インクリメンタル | < 2 sec |
| クエリ応答 | < 500ms |
| 起動時間 | < 2 sec |
| メモリ使用量 | < 500MB |

---

## Supported Languages (12)

| Language | Extension | Extractor |
|----------|-----------|-----------|
| Python | `.py`, `.pyi` | PythonExtractor |
| TypeScript | `.ts`, `.tsx` | TypeScriptExtractor |
| JavaScript | `.js`, `.jsx` | JavaScriptExtractor |
| Rust | `.rs` | RustExtractor |
| Go | `.go` | GoExtractor |
| Java | `.java` | JavaExtractor |
| PHP | `.php` | PHPExtractor |
| C# | `.cs` | CSharpExtractor |
| C/C++ | `.c`, `.cpp`, `.h` | CppExtractor |
| HCL | `.tf`, `.hcl` | HCLExtractor |
| Ruby | `.rb` | RubyExtractor |

---

## Security

### 依存関係スキャン

```bash
pip audit                    # 脆弱性スキャン
```

### シークレット管理

- `.env` ファイル (ローカル開発)
- 環境変数 (本番環境)
- `.gitignore` で `.env` を除外

---

**Last Updated**: 2025-12-04
**Maintained By**: GitHub Copilot / nahisaho
