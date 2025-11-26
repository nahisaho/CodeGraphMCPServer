# CodeGraph MCP Server アーキテクチャ概要設計書

**Project**: CodeGraph MCP Server  
**Version**: 1.0.0  
**Created**: 2025-11-26  
**Status**: Draft  
**Document Type**: C4 Model - Context & Container Diagrams

---

## 1. ドキュメント概要

### 1.1 目的

本ドキュメントは、CodeGraph MCP Serverのシステムアーキテクチャを C4 Model に基づいて記述します。

### 1.2 スコープ

- システムコンテキスト（Level 1）
- コンテナ図（Level 2）
- 主要コンポーネント概要
- 外部システム連携

### 1.3 関連ドキュメント

| ドキュメント | 参照先 |
|-------------|--------|
| 要件定義書 | storage/specs/requirements-specification.md |
| コアエンジン設計書 | storage/specs/design-core-engine.md |
| MCPインターフェース設計書 | storage/specs/design-mcp-interface.md |
| ストレージ設計書 | storage/specs/design-storage.md |
| ADR | storage/specs/design-adr.md |

---

## 2. C4 Model - Level 1: システムコンテキスト図

### 2.1 コンテキスト図

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         External Systems                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │   GitHub     │  │   Claude     │  │   Cursor     │  │  Windsurf    ││
│  │   Copilot    │  │    Code      │  │    IDE       │  │    IDE       ││
│  │              │  │              │  │              │  │              ││
│  │  [MCP Client]│  │  [MCP Client]│  │  [MCP Client]│  │  [MCP Client]││
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘│
│         │                 │                 │                 │         │
│         │    MCP Protocol (stdio/SSE)       │                 │         │
│         └─────────────────┼─────────────────┴─────────────────┘         │
│                           │                                              │
│                           ▼                                              │
│         ┌─────────────────────────────────────┐                         │
│         │                                      │                         │
│         │     CodeGraph MCP Server            │                         │
│         │                                      │                         │
│         │  - ソースコードグラフ分析            │                         │
│         │  - GraphRAG機能                     │                         │
│         │  - コード構造クエリ                  │                         │
│         │                                      │                         │
│         └─────────────────┬───────────────────┘                         │
│                           │                                              │
│                           │ File System Access                          │
│                           ▼                                              │
│         ┌─────────────────────────────────────┐                         │
│         │                                      │                         │
│         │     Source Code Repository          │                         │
│         │     (Local File System)             │                         │
│         │                                      │                         │
│         └─────────────────────────────────────┘                         │
│                                                                          │
│  ┌──────────────┐                                                       │
│  │   LLM API    │◄─── Optional: 説明生成・サマリー生成                  │
│  │  (OpenAI等)  │                                                       │
│  └──────────────┘                                                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 アクター定義

| アクター | 説明 | インタラクション |
|----------|------|-----------------|
| **AI Assistant** | GitHub Copilot, Claude Code, Cursor等 | MCP Protocol経由でツール/リソース/プロンプトを利用 |
| **Developer** | 開発者 | CLI経由でインデックス作成、サーバー起動 |
| **Source Repository** | ソースコードリポジトリ | ファイルシステム経由で読み取り |
| **LLM API** | 外部LLMサービス（オプション） | 説明生成、サマリー生成時に呼び出し |

### 2.3 システム境界

| 境界 | 内部/外部 | 説明 |
|------|----------|------|
| CodeGraph MCP Server | 内部 | 本システムのスコープ |
| MCP Clients | 外部 | AI Assistantツール |
| File System | 外部 | ソースコードリポジトリ |
| LLM API | 外部 | オプショナル外部サービス |

---

## 3. C4 Model - Level 2: コンテナ図

### 3.1 コンテナ図

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CodeGraph MCP Server                                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        MCP Server Container                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   stdio      │  │     SSE      │  │  Streamable  │              │   │
│  │  │  Transport   │  │  Transport   │  │    HTTP      │              │   │
│  │  │  [REQ-TRP-001]│ │  [REQ-TRP-002]│ │  [REQ-TRP-003]│             │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │   │
│  │         └─────────────────┼─────────────────┘                       │   │
│  │                           ▼                                          │   │
│  │  ┌────────────────────────────────────────────────────────────┐    │   │
│  │  │                 MCP Interface Layer                         │    │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │    │   │
│  │  │  │   Tools     │  │  Resources  │  │   Prompts   │         │    │   │
│  │  │  │ (14 tools)  │  │ (4 types)   │  │ (6 prompts) │         │    │   │
│  │  │  │[REQ-TLS-*]  │  │[REQ-RSC-*]  │  │[REQ-PRM-*]  │         │    │   │
│  │  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │    │   │
│  │  │         └────────────────┼────────────────┘                 │    │   │
│  │  └──────────────────────────┼─────────────────────────────────┘    │   │
│  │                             │                                       │   │
│  └─────────────────────────────┼───────────────────────────────────────┘   │
│                                │                                            │
│  ┌─────────────────────────────▼───────────────────────────────────────┐   │
│  │                      Core Engine Container                           │   │
│  │                                                                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │ AST Parser  │  │   Graph     │  │  Semantic   │  │  Indexer   │ │   │
│  │  │             │  │   Engine    │  │  Analyzer   │  │            │ │   │
│  │  │[REQ-AST-*]  │  │[REQ-GRF-*]  │  │[REQ-SEM-*]  │  │[REQ-IDX-*] │ │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘ │   │
│  │         │                │                │                │        │   │
│  └─────────┼────────────────┼────────────────┼────────────────┼────────┘   │
│            │                │                │                │             │
│  ┌─────────▼────────────────▼────────────────▼────────────────▼────────┐   │
│  │                      Storage Container                               │   │
│  │                                                                      │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │   │
│  │  │   SQLite DB     │  │   File Cache    │  │  Vector Store   │     │   │
│  │  │  (Graph Data)   │  │  (AST Cache)    │  │  (Embeddings)   │     │   │
│  │  │  [REQ-STR-001]  │  │  [REQ-STR-002]  │  │  [REQ-STR-003]  │     │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 コンテナ定義

| コンテナ | 技術 | 責務 | 要件ID |
|----------|------|------|--------|
| **MCP Server** | Python, mcp-sdk | MCPプロトコル処理、トランスポート管理 | REQ-TRP-001~005 |
| **MCP Interface** | Python | Tools/Resources/Prompts提供 | REQ-TLS/RSC/PRM-* |
| **Core Engine** | Python, Tree-sitter, NetworkX | AST解析、グラフ構築、セマンティック分析 | REQ-AST/GRF/SEM/IDX-* |
| **Storage** | SQLite, aiosqlite | データ永続化、キャッシュ管理 | REQ-STR-001~004 |

### 3.3 コンテナ間通信

| ソース | ターゲット | プロトコル | 説明 |
|--------|----------|----------|------|
| MCP Client | MCP Server | stdio/SSE/HTTP | MCP Protocol JSON-RPC 2.0 |
| MCP Interface | Core Engine | Python API | 同期/非同期関数呼び出し |
| Core Engine | Storage | SQL/File I/O | データ読み書き |
| Semantic Analyzer | LLM API | HTTPS | 説明/サマリー生成（オプション）|

---

## 4. アーキテクチャ原則

### 4.1 設計原則

| 原則 | 説明 | Constitutional Article |
|------|------|----------------------|
| **Library-First** | すべての機能を独立ライブラリとして実装 | Article I |
| **CLI Interface** | すべてのライブラリはCLI経由でアクセス可能 | Article II |
| **Self-Contained** | 外部DB不要、SQLite埋め込み | - |
| **Zero-Config** | `pip install && serve` で即座に利用可能 | - |
| **Incremental** | Git差分ベースの増分インデックス | - |

### 4.2 品質属性

| 属性 | 目標 | 測定方法 |
|------|------|---------|
| **Performance** | 10万行30秒以内 | ベンチマークテスト |
| **Latency** | クエリ500ms以内 | レスポンスタイム計測 |
| **Memory** | 500MB以下 | メモリプロファイリング |
| **Startup** | 2秒以内 | 起動時間計測 |

### 4.3 制約事項

| 制約 | 説明 | 根拠 |
|------|------|------|
| Python 3.11+ | 最小Python バージョン | 型ヒント、パフォーマンス |
| SQLite | グラフストレージ | 自己完結型、ゼロ構成 |
| MCP 1.0 | プロトコルバージョン | 仕様準拠 |
| 3プロジェクト以下 | 初期プロジェクト数 | Article VII |

---

## 5. デプロイメントアーキテクチャ

### 5.1 デプロイメント図

```
┌─────────────────────────────────────────────────────────────────┐
│                    Developer Machine                             │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   IDE / Editor                            │  │
│  │  ┌────────────────┐  ┌────────────────┐                  │  │
│  │  │ VS Code +      │  │    Cursor      │                  │  │
│  │  │ GitHub Copilot │  │                │                  │  │
│  │  └───────┬────────┘  └───────┬────────┘                  │  │
│  │          │                    │                           │  │
│  │          │     stdio          │                           │  │
│  │          ▼                    ▼                           │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │            CodeGraph MCP Server Process            │  │  │
│  │  │                                                    │  │  │
│  │  │   codegraph-mcp serve --repo /path/to/project     │  │  │
│  │  │                                                    │  │  │
│  │  └───────────────────────┬────────────────────────────┘  │  │
│  │                          │                                │  │
│  └──────────────────────────┼────────────────────────────────┘  │
│                             │                                    │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │                    Local File System                       │  │
│  │                                                            │  │
│  │  ┌─────────────────┐  ┌─────────────────────────────────┐│  │
│  │  │ ~/.codegraph/   │  │     /path/to/project/          ││  │
│  │  │                 │  │                                 ││  │
│  │  │ ├── index.db    │  │ ├── src/                       ││  │
│  │  │ ├── cache/      │  │ ├── tests/                     ││  │
│  │  │ └── vectors/    │  │ └── ...                        ││  │
│  │  │                 │  │                                 ││  │
│  │  │ [CodeGraph Data]│  │ [Source Code Repository]       ││  │
│  │  └─────────────────┘  └─────────────────────────────────┘│  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 デプロイメント構成

| 構成 | 説明 | ユースケース |
|------|------|-------------|
| **Local Process** | ローカルマシン上のプロセス | 個人開発 |
| **Docker Container** | コンテナ化された実行環境 | CI/CD統合 |
| **Remote Server** | リモートサーバー上で稼働 | チーム共有（将来）|

### 5.3 インストール方法

```bash
# PyPI経由
pip install codegraph-mcp

# GitHub経由
pip install git+https://github.com/nahisaho/CodeGraphMCPServer.git

# 開発モード
git clone https://github.com/nahisaho/CodeGraphMCPServer.git
cd CodeGraphMCPServer
pip install -e .
```

### 5.4 MCP Client 設定例

#### Claude Desktop (claude_desktop_config.json)

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

#### VS Code Settings

```json
{
  "github.copilot.chat.mcpServers": {
    "codegraph": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "${workspaceFolder}"]
    }
  }
}
```

---

## 6. データフロー

### 6.1 インデックス作成フロー

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  CLI    │────▶│   Indexer   │────▶│  AST Parser │────▶│   Graph     │
│ command │     │             │     │             │     │   Engine    │
└─────────┘     └──────┬──────┘     └─────────────┘     └──────┬──────┘
                       │                                        │
                       │ 1. Collect files                       │ 3. Store entities
                       │ 2. Check git diff                      │ 4. Store relations
                       ▼                                        ▼
               ┌───────────────┐                        ┌───────────────┐
               │  File System  │                        │    SQLite     │
               │  (Source)     │                        │   (Graph DB)  │
               └───────────────┘                        └───────────────┘
```

### 6.2 クエリ処理フロー

```
┌───────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│MCP Client │────▶│ MCP Server  │────▶│   Tools     │────▶│   Graph     │
│  (query)  │     │(JSON-RPC)   │     │ (handler)   │     │   Engine    │
└───────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                  │
      ┌───────────────────────────────────────────────────────────┘
      │
      ▼
┌───────────────┐     ┌───────────────┐
│    SQLite     │────▶│    Result     │────▶ Response to Client
│   (Query)     │     │  Formatting   │
└───────────────┘     └───────────────┘
```

### 6.3 GraphRAG クエリフロー（Phase 2）

```
┌───────────────┐     ┌─────────────┐     ┌─────────────┐
│ global_search │────▶│  Community  │────▶│   LLM API   │
│    Tool       │     │  Summaries  │     │ (optional)  │
└───────────────┘     └─────────────┘     └──────┬──────┘
                                                  │
                                                  ▼
                                          ┌─────────────┐
                                          │  Aggregated │
                                          │   Response  │
                                          └─────────────┘
```

---

## 7. セキュリティアーキテクチャ

### 7.1 セキュリティ境界

```
┌─────────────────────────────────────────────────────────────────┐
│                      Trust Boundary                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    MCP Server                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │  │
│  │  │  Allowed    │  │  Sandboxed  │  │  Path           │   │  │
│  │  │  Repository │  │  Shell      │  │  Restriction    │   │  │
│  │  │  Paths      │  │  Execution  │  │  Enforcement    │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Restricted Access                             │  │
│  │  - File system access limited to --repo path               │  │
│  │  - Shell commands with timeout (REQ-NFR-012)               │  │
│  │  - No network access except LLM API (optional)             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 セキュリティ対策

| 脅威 | 対策 | 要件ID |
|------|------|--------|
| パストラバーサル | リポジトリパス制限 | REQ-NFR-013 |
| コマンドインジェクション | シェル実行サンドボックス | REQ-NFR-012 |
| DoS攻撃 | タイムアウト制限 | REQ-NFR-012 |
| 認証バイパス | OAuth 2.1（P2） | REQ-TRP-005 |

---

## 8. エラーハンドリング戦略

### 8.1 エラー分類

| カテゴリ | 例 | 対応 |
|----------|---|------|
| **Recoverable** | パースエラー、ファイル未発見 | ログ記録、継続処理 |
| **Transient** | ネットワークエラー | リトライ |
| **Fatal** | DB破損、メモリ不足 | 終了、復旧手順 |

### 8.2 エラー復旧

| シナリオ | 復旧方法 | 要件ID |
|----------|---------|--------|
| サーバークラッシュ | インデックス自動復元 | REQ-NFR-008 |
| パースエラー | 部分解析継続 | REQ-AST-005 |
| インデックス破損 | 完全再インデックス | REQ-IDX-003 |

---

## 9. 拡張性設計

### 9.1 言語拡張

```python
# languages/config.py - 新言語追加パターン
LANGUAGE_CONFIGS = {
    "python": {
        "extensions": [".py"],
        "parser": "tree-sitter-python",
        "node_types": {...}
    },
    # 新言語を追加
    "go": {
        "extensions": [".go"],
        "parser": "tree-sitter-go",
        "node_types": {...}
    }
}
```

### 9.2 ツール拡張

```python
# mcp/tools.py - 新ツール追加パターン
@server.tool()
async def new_tool(param: str) -> str:
    """新しいツールの説明"""
    # 実装
    pass
```

---

## 10. 要件トレーサビリティ

### 10.1 アーキテクチャ → 要件マッピング

| アーキテクチャ要素 | 要件ID | 説明 |
|-------------------|--------|------|
| MCP Server Container | REQ-TRP-001~005 | トランスポート層 |
| MCP Interface Layer | REQ-TLS/RSC/PRM-* | MCP機能 |
| Core Engine Container | REQ-AST/GRF/SEM/IDX-* | コア機能 |
| Storage Container | REQ-STR-001~004 | ストレージ |
| Security Boundary | REQ-NFR-012, 013 | セキュリティ |
| Performance Targets | REQ-NFR-001~006 | パフォーマンス |

---

## 11. 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|------------|------|----------|--------|
| 1.0.0 | 2025-11-26 | 初版作成 | System |

---

**Document Status**: Draft  
**Constitutional Compliance**: Article VI (Project Memory), Article VII (Simplicity Gate) ✓
