# CodeGraphMCPServer

**ゼロ構成で起動可能な軽量・高速なソースコード分析MCPサーバー**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-1.0-green.svg)](https://modelcontextprotocol.io/)
[![Tests](https://img.shields.io/badge/tests-308%20passed-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-64%25-yellow.svg)]()
[![CI](https://github.com/nahisaho/CodeGraphMCPServer/actions/workflows/ci.yml/badge.svg)](https://github.com/nahisaho/CodeGraphMCPServer/actions/workflows/ci.yml)

## 概要

CodeGraphMCPServer は、コードベースの構造を理解し、GraphRAG（Graph Retrieval-Augmented Generation）機能を提供するMCPサーバーです。外部データベース不要の自己完結型アーキテクチャで、MCP対応AIツール（GitHub Copilot、Claude Desktop、Cursor等）からコードベースの構造的理解と効率的なコード補完を実現します。

### 🧠 GraphRAG機能

- **コミュニティ検出**: Louvainアルゴリズムによるコードモジュールの自動クラスタリング
- **LLM統合**: OpenAI/Anthropic/ローカルLLM対応のマルチプロバイダー設計
- **グローバル検索**: コミュニティサマリーを活用したコードベース全体の理解
- **ローカル検索**: エンティティ近傍のコンテキスト取得

### ✨ 特徴

| 特徴 | 説明 |
|------|------|
| 🚀 **ゼロ構成起動** | 外部DB不要、`pip install && serve` で即座に利用開始 |
| 🌳 **AST解析** | Tree-sitterによる高速・正確なコード解析 |
| 🔗 **グラフ構築** | コードエンティティ間の関係をグラフ化 |
| 🔍 **14 MCP Tools** | 依存関係分析、呼び出し追跡、コード検索 |
| 📚 **4 MCP Resources** | エンティティ、ファイル、コミュニティ、統計情報 |
| 💬 **6 MCP Prompts** | コードレビュー、機能実装、デバッグ支援 |
| ⚡ **高速インデックス** | 10万行を30秒以内、増分更新は2秒以内 |
| 🌐 **多言語対応** | Python, TypeScript, JavaScript, Rust, Go, Java, PHP, C#, C, C++, HCL, Ruby, Kotlin, Swift, Scala, Lua をサポート（16言語） |

## 動作要件

- Python 3.11+
- MCP対応クライアント (GitHub Copilot, Claude Desktop, Cursor, Windsurf)

## インストール

### pip でインストール

```bash
pip install codegraph-mcp
```

### ソースからインストール（開発用）

```bash
git clone https://github.com/nahisaho/CodeGraphMCPServer.git
cd CodeGraphMCPServer
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -e ".[dev]"
```

## クイックスタート

### 1. リポジトリをインデックス

```bash
# フルインデックス
codegraph-mcp index /path/to/repository --full

# 増分インデックス（デフォルト）
codegraph-mcp index /path/to/repository

# ファイル監視で自動再インデックス (v0.7.0 NEW)
codegraph-mcp watch /path/to/repository
codegraph-mcp watch /path/to/repository --debounce 2.0  # 2秒のデバウンス
codegraph-mcp watch /path/to/repository --community     # 再インデックス後にコミュニティ検出
```

**出力例:**
```
Indexed 16 entities, 37 relations in 0.81s
```

### 2. 統計情報を確認

```bash
codegraph-mcp stats /path/to/repository
```

**出力例:**
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

### 3. コードを検索

```bash
codegraph-mcp query "Calculator" --repo /path/to/repository
```

### 4. MCPサーバーとして起動

```bash
# stdio トランスポート（デフォルト）
codegraph-mcp serve --repo /path/to/repository

# SSE トランスポート
codegraph-mcp serve --repo /path/to/repository --transport sse --port 8080
```

## MCP クライアント設定

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

## 🛠 MCP Tools (14種)

### グラフクエリツール

| Tool | 説明 | 主な引数 |
|------|------|----------|
| `query_codebase` | 自然言語でコードグラフを検索 | `query`, `max_results` |
| `find_dependencies` | エンティティの依存関係を検索 | `entity_id`, `depth` |
| `find_callers` | 関数/メソッドの呼び出し元を検索 | `entity_id` |
| `find_callees` | 関数/メソッドの呼び出し先を検索 | `entity_id` |
| `find_implementations` | インターフェースの実装を検索 | `entity_id` |
| `analyze_module_structure` | モジュール構造を分析 | `file_path` |

### コード取得ツール

| Tool | 説明 | 主な引数 |
|------|------|----------|
| `get_code_snippet` | エンティティのソースコードを取得 | `entity_id`, `include_context` |
| `read_file_content` | ファイル内容を取得 | `file_path`, `start_line`, `end_line` |
| `get_file_structure` | ファイルの構造概要を取得 | `file_path` |

### GraphRAG ツール

| Tool | 説明 | 主な引数 |
|------|------|----------|
| `global_search` | コミュニティ横断のグローバル検索 | `query` |
| `local_search` | エンティティ近傍のローカル検索 | `query`, `entity_id` |

### 管理ツール

| Tool | 説明 | 主な引数 |
|------|------|----------|
| `suggest_refactoring` | リファクタリング提案 | `entity_id`, `type` |
| `reindex_repository` | リポジトリを再インデックス | `incremental` |
| `execute_shell_command` | シェルコマンドを実行 | `command`, `timeout` |

## 📚 MCP Resources (4種)

| URI パターン | 説明 |
|-------------|------|
| `codegraph://entities/{id}` | エンティティ詳細情報 |
| `codegraph://files/{path}` | ファイル内のエンティティ一覧 |
| `codegraph://communities/{id}` | コミュニティ情報 |
| `codegraph://stats` | グラフ統計情報 |

## 💬 MCP Prompts (6種)

| Prompt | 説明 | 引数 |
|--------|------|------|
| `code_review` | コードレビュー実施 | `entity_id`, `focus_areas` |
| `explain_codebase` | コードベース説明 | `scope`, `detail_level` |
| `implement_feature` | 機能実装ガイド | `feature_description`, `constraints` |
| `debug_issue` | デバッグ支援 | `issue_description`, `context` |
| `refactor_guidance` | リファクタリングガイド | `entity_id`, `goal` |
| `test_generation` | テスト生成 | `entity_id`, `test_type` |

## 使用例

### AIアシスタントとの対話例

```
You: UserService クラスの依存関係を教えて

AI: [find_dependencies ツールを使用]
    UserService は以下に依存しています:
    - DatabaseConnection (database.py)
    - Logger (utils/logging.py)
    - UserRepository (repositories/user.py)
```

```
You: authenticate メソッドを変更した場合の影響範囲は？

AI: [find_callers ツールを使用]
    authenticate の呼び出し元:
    - LoginController.login() (controllers/auth.py:45)
    - APIMiddleware.verify_token() (middleware/api.py:23)
    - TestUserService.test_auth() (tests/test_user.py:78)
```

```
You: このプロジェクトの主要なコンポーネントを説明して

AI: [global_search ツールを使用]
    [explain_codebase プロンプトを使用]
    
    このプロジェクトは3層アーキテクチャで構成されています:
    1. Controllers層: HTTPリクエストの処理
    2. Services層: ビジネスロジック
    3. Repositories層: データアクセス
```

## 開発

### テスト実行

```bash
# 全テスト実行
pytest

# カバレッジ付き
pytest --cov=src/codegraph_mcp --cov-report=html

# 特定のテスト
pytest tests/unit/test_parser.py -v
```

### リント & フォーマット

```bash
# Ruff でリント
ruff check src tests

# Ruff でフォーマット
ruff format src tests

# MyPy で型チェック
mypy src
```

## アーキテクチャ

```
src/codegraph_mcp/
├── __init__.py          # パッケージ初期化
├── __main__.py          # CLI エントリーポイント
├── server.py            # MCP サーバー
├── config.py            # 設定管理
├── core/                # コアロジック
│   ├── parser.py        # Tree-sitter AST パーサー
│   ├── graph.py         # NetworkX グラフエンジン
│   ├── indexer.py       # リポジトリインデクサー
│   ├── community.py     # コミュニティ検出 (Louvain)
│   ├── semantic.py      # セマンティック分析
│   ├── llm.py           # LLM統合 (OpenAI/Anthropic/Local)
│   └── graphrag.py      # GraphRAG検索エンジン
├── storage/             # ストレージ層
│   ├── sqlite.py        # SQLite 永続化
│   ├── cache.py         # ファイルキャッシュ
│   └── vectors.py       # ベクトルストア
├── mcp/                 # MCP インターフェース
│   ├── tools.py         # 14 MCP Tools
│   ├── resources.py     # 4 MCP Resources
│   └── prompts.py       # 6 MCP Prompts
└── languages/           # 言語サポート (11言語)
    ├── python.py        # Python エクストラクター
    ├── typescript.py    # TypeScript エクストラクター
    ├── javascript.py    # JavaScript エクストラクター
    ├── rust.py          # Rust エクストラクター
    ├── go.py            # Go エクストラクター
    ├── java.py          # Java エクストラクター
    ├── php.py           # PHP エクストラクター
    ├── csharp.py        # C# エクストラクター
    ├── cpp.py           # C++ エクストラクター
    ├── hcl.py           # HCL (Terraform) エクストラクター
    └── ruby.py          # Ruby エクストラクター
```

## パフォーマンス

### 実測値 (v0.3.0)

| メトリクス | 実測値 | 備考 |
|-----------|--------|------|
| インデックス速度 | **32 エンティティ/秒** | 67ファイル, 941エンティティ |
| ファイル処理速度 | **0.44秒/ファイル** | Python/TS/Rust混在 |
| 増分インデックス | **< 2秒** | 変更ファイルのみ |
| クエリレスポンス | **< 2ms** | グラフ検索 |

### 目標値

| メトリクス | 目標値 |
|-----------|--------|
| 初回インデックス (10万行) | < 30秒 |
| 増分インデックス | < 2秒 |
| クエリレスポンス | < 500ms |
| 起動時間 | < 2秒 |
| メモリ使用量 | < 500MB |

## ライセンス

MIT License - [LICENSE](LICENSE) を参照

## 謝辞

- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP仕様
- [Tree-sitter](https://tree-sitter.github.io/) - AST解析
- [NetworkX](https://networkx.org/) - グラフアルゴリズム
- [Microsoft GraphRAG](https://github.com/microsoft/graphrag) - GraphRAGコンセプト

## 関連リンク

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
