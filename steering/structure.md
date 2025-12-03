# Project Structure

**Project**: CodeGraphMCPServer
**Last Updated**: 2025-12-04
**Version**: 1.1

---

## Architecture Pattern

**Primary Pattern**: Library-First MCP Server

> Python ベースの MCP (Model Context Protocol) サーバー。
> Tree-sitter による AST 解析、NetworkX によるグラフ分析、SQLite によるストレージを組み合わせた
> コードグラフ分析エンジンを提供。

---

## Directory Organization

### Root Structure

```
CodeGraphMCPServer/
├── src/codegraph_mcp/       # メインパッケージ (Library-First)
│   ├── core/                # コアロジック層
│   ├── storage/             # ストレージ層
│   ├── mcp/                 # MCP インターフェース層
│   ├── languages/           # 言語サポート (12言語)
│   └── utils/               # ユーティリティ
├── tests/                   # テストスイート
│   ├── unit/                # ユニットテスト (260件)
│   ├── integration/         # 結合テスト (39件)
│   └── fixtures/            # テストデータ
├── examples/                # 使用例
├── storage/                 # SDD アーティファクト
│   ├── specs/               # 仕様書 (requirements, design, tasks)
│   ├── changes/             # 変更仕様 (brownfield)
│   └── features/            # 機能追跡
├── steering/                # プロジェクトメモリ
│   ├── structure.md         # このファイル
│   ├── tech.md              # 技術スタック
│   ├── product.md           # プロダクトコンテキスト
│   └── rules/               # 憲法的ガバナンス
├── References/              # 設計リファレンス
├── templates/               # ドキュメントテンプレート
├── .github/workflows/       # CI/CD (GitHub Actions)
├── pyproject.toml           # パッケージ設定
└── README.md                # プロジェクト説明
```

---

## Core Package Structure

### src/codegraph_mcp/ (メインパッケージ)

```
src/codegraph_mcp/
├── __init__.py              # パッケージ初期化、バージョン管理
├── __main__.py              # CLI エントリーポイント (codegraph-mcp)
├── server.py                # MCP サーバー実装
├── config.py                # Pydantic Settings 設定管理
│
├── core/                    # コアロジック層
│   ├── parser.py            # Tree-sitter AST パーサー
│   ├── graph.py             # NetworkX グラフエンジン
│   ├── indexer.py           # リポジトリインデクサー
│   ├── community.py         # コミュニティ検出 (Louvain)
│   ├── semantic.py          # セマンティック分析
│   ├── graphrag.py          # GraphRAG 検索エンジン
│   ├── llm.py               # LLM 統合 (OpenAI/Anthropic)
│   └── types.py             # 共通型定義
│
├── storage/                 # ストレージ層
│   ├── sqlite.py            # SQLite 永続化
│   ├── cache.py             # ファイルキャッシュ
│   └── vectors.py           # ベクトルストア
│
├── mcp/                     # MCP インターフェース層
│   ├── tools.py             # 14 MCP ツール
│   ├── resources.py         # 4 MCP リソース
│   └── prompts.py           # 6 MCP プロンプト
│
├── languages/               # 言語サポート (12言語)
│   ├── config.py            # 言語設定、BaseExtractor
│   ├── python.py            # Python
│   ├── typescript.py        # TypeScript
│   ├── javascript.py        # JavaScript
│   ├── rust.py              # Rust
│   ├── go.py                # Go
│   ├── java.py              # Java
│   ├── php.py               # PHP
│   ├── csharp.py            # C#
│   ├── cpp.py               # C/C++
│   ├── hcl.py               # HCL (Terraform)
│   └── ruby.py              # Ruby
│
└── utils/                   # ユーティリティ
    ├── git.py               # Git 操作
    └── logging.py           # ロギング設定
```

---

## Layer Architecture

### 3層アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                   MCP Interface Layer                    │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  14 Tools   │  │ 4 Resources  │  │   6 Prompts     │ │
│  └─────────────┘  └──────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                      Core Layer                          │
│  ┌─────────┐ ┌───────┐ ┌─────────┐ ┌─────────────────┐ │
│  │ Parser  │ │ Graph │ │ Indexer │ │ GraphRAG Engine │ │
│  └─────────┘ └───────┘ └─────────┘ └─────────────────┘ │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │  Community   │  │   Semantic    │  │     LLM      │ │
│  └──────────────┘  └───────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────┤
│                    Storage Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   SQLite    │  │    Cache    │  │   Vector Store  │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Test Organization

### テスト構造

```
tests/
├── unit/                    # ユニットテスト (260件)
│   ├── test_parser.py       # パーサーテスト
│   ├── test_graph.py        # グラフエンジンテスト
│   ├── test_indexer.py      # インデクサーテスト
│   ├── test_tools.py        # MCP ツールテスト
│   ├── test_resources.py    # MCP リソーステスト
│   ├── test_prompts.py      # MCP プロンプトテスト
│   ├── test_storage.py      # ストレージテスト
│   ├── test_cli.py          # CLI テスト
│   ├── test_graphrag.py     # GraphRAG テスト
│   ├── test_llm.py          # LLM テスト
│   └── test_<language>.py   # 各言語エクストラクタテスト
│
├── integration/             # 結合テスト (39件)
│   ├── test_server.py       # サーバー結合テスト
│   ├── test_mcp_server.py   # MCP プロトコルテスト
│   ├── test_parser_graph.py # パーサー→グラフ結合テスト
│   └── test_graphrag_integration.py
│
└── fixtures/                # テストフィクスチャ
    ├── calculator.py        # Python サンプル
    ├── calculator.cpp       # C++ サンプル
    └── user.ts              # TypeScript サンプル
```

### テスト基準

- **ユニットテスト**: 260件、コアロジックの網羅
- **結合テスト**: 39件、レイヤー間の連携検証
- **カバレッジ目標**: 60%以上 (現在 64%)
- **全テスト合格**: 299件 ✅

---

## CodeGraph Index Statistics

現在のコードベース分析結果:

| 指標 | 値 |
|------|-----|
| **エンティティ** | 1,004 |
| **リレーション** | 4,316 |
| **コミュニティ** | 32 |
| **ファイル** | 69 |

### エンティティ種別

| タイプ | 数 |
|--------|-----|
| Module | 69 |
| Class | 158 |
| Method | 665 |
| Function | 109 |
| Interface | 2 |
| Struct | 1 |

---

## Naming Conventions

### ファイル命名規則

- **Python モジュール**: `snake_case.py` (例: `graph_engine.py`)
- **テスト**: `test_*.py` (例: `test_parser.py`)
- **設定**: `*.py` または `*.toml`

### クラス・関数命名規則

- **クラス**: `PascalCase` (例: `ASTParser`, `GraphEngine`)
- **関数/メソッド**: `snake_case` (例: `parse_file`, `get_statistics`)
- **定数**: `SCREAMING_SNAKE_CASE` (例: `LANGUAGE_EXTENSIONS`)
- **プライベート**: `_` prefix (例: `_walk_tree`, `_engine`)

---

## CLI Commands

### 利用可能なコマンド

```bash
codegraph-mcp --version              # バージョン表示
codegraph-mcp index <path>           # リポジトリインデックス
codegraph-mcp index <path> --full    # フルインデックス
codegraph-mcp stats <path>           # 統計表示
codegraph-mcp query "..." --repo .   # グラフクエリ
codegraph-mcp community <path>       # コミュニティ検出
codegraph-mcp watch <path>           # ファイル監視・自動再インデックス
codegraph-mcp serve --repo <path>    # MCP サーバー起動 (stdio)
codegraph-mcp start --repo <path>    # MCP サーバー起動 (バックグラウンド)
codegraph-mcp stop                   # サーバー停止
codegraph-mcp status                 # サーバー状態確認
```

---

## Version Control

### ブランチ構成

- `main` - プロダクションブランチ
- `feature/*` - 機能ブランチ
- `fix/*` - バグ修正ブランチ

### コミットメッセージ規約

```
<type>(<scope>): <subject>

Types: feat, fix, docs, style, refactor, test, chore
```

---

**Last Updated**: 2025-12-04
**Maintained By**: GitHub Copilot / nahisaho
