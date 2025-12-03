# Product Context

**Project**: CodeGraphMCPServer
**Last Updated**: 2025-12-04
**Version**: 1.1

---

## Product Vision

**Vision Statement**: 
AI アシスタントがコードベースを深く理解し、より正確で文脈に沿った支援を提供できるようにする。

> MCP (Model Context Protocol) を通じて、コードの構造・依存関係・意味的なつながりを
> グラフとして表現し、AI ツール（GitHub Copilot、Claude Desktop、Cursor 等）に
> 高品質なコンテキストを提供する。

**Mission**: 
ゼロ設定で始められる、軽量かつ高性能なコードグラフ分析 MCP サーバーを提供する。

---

## Product Overview

### What is CodeGraphMCPServer?

CodeGraphMCPServer は、コードベースの構造を理解し GraphRAG 
(Graph Retrieval-Augmented Generation) 機能を提供する MCP サーバーです。

外部データベース不要の自己完結型アーキテクチャにより、
`pip install && serve` で即座に利用開始できます。

### Problem Statement

**Problem**: 
AI コーディングアシスタントは、コードベース全体の構造や依存関係を把握することが難しく、
局所的なコード補完に留まりがちである。

**具体的な課題**:
- 関数間の呼び出し関係が把握できない
- モジュール間の依存構造が見えない
- リファクタリングの影響範囲が特定できない
- 大規模コードベースでの文脈理解が困難

### Solution

**Solution**: 
Tree-sitter による正確な AST 解析と NetworkX によるグラフ分析を組み合わせ、
MCP プロトコル経由で AI ツールにコード構造情報を提供する。

**独自性**:
- **ゼロ設定**: 外部 DB 不要、インストール即利用可能
- **高速**: 100K 行を 30 秒以下でインデックス
- **多言語**: 12 言語をネイティブサポート
- **GraphRAG**: コミュニティ検出による大域的理解

---

## Target Users

### Primary Users

#### User Persona 1: AI アシステッド開発者

**Demographics**:
- **Role**: ソフトウェアエンジニア
- **Organization Size**: 個人〜大企業
- **Technical Level**: 中級〜上級

**Goals**:
- コードベース全体を把握した AI 支援を受けたい
- リファクタリングの影響範囲を事前に知りたい
- 効率的なコードナビゲーションをしたい

**Pain Points**:
- AI が局所的なコンテキストしか理解しない
- 依存関係の調査に時間がかかる
- 大規模プロジェクトでの迷子状態

**Use Cases**:
- 「この関数を呼び出している箇所をすべて教えて」
- 「このクラスの依存関係を可視化して」
- 「このモジュールの責務を説明して」

---

#### User Persona 2: コードレビュアー

**Demographics**:
- **Role**: シニアエンジニア / テックリード
- **Organization Size**: チーム開発
- **Technical Level**: 上級

**Goals**:
- PR の影響範囲を素早く把握したい
- アーキテクチャ違反を検出したい
- コードベースの健全性を維持したい

**Pain Points**:
- 変更の影響範囲が見えにくい
- 循環依存の検出が困難
- モジュール境界の曖昧さ

**Use Cases**:
- 「この変更が影響する他のモジュールは？」
- 「循環依存はある？」
- 「このコンポーネントのコミュニティを表示して」

---

## Core Product Capabilities

### MCP Tools (14)

| Priority | Tool | Description |
|----------|------|-------------|
| P0 | `query_codebase` | 自然言語でコードグラフを検索 |
| P0 | `find_dependencies` | エンティティの依存関係を取得 |
| P0 | `find_callers` | 関数/メソッドの呼び出し元を検索 |
| P0 | `find_callees` | 関数/メソッドの呼び出し先を検索 |
| P1 | `find_implementations` | インターフェース実装を検索 |
| P1 | `analyze_module_structure` | モジュール構造を分析 |
| P1 | `get_code_snippet` | エンティティのソースコードを取得 |
| P1 | `read_file_content` | ファイル内容を取得 |
| P1 | `get_file_structure` | ファイル構造の概要を取得 |
| P1 | `global_search` | GraphRAG グローバル検索 |
| P1 | `local_search` | GraphRAG ローカル検索 |
| P2 | `suggest_refactoring` | リファクタリング提案 |
| P2 | `reindex_repository` | リポジトリ再インデックス |
| P2 | `execute_shell_command` | シェルコマンド実行 |

### MCP Resources (4)

| URI Pattern | Description |
|-------------|-------------|
| `codegraph://entities/{id}` | エンティティ詳細 |
| `codegraph://files/{path}` | ファイル内エンティティ |
| `codegraph://communities/{id}` | コミュニティ情報 |
| `codegraph://stats` | グラフ統計 |

### MCP Prompts (6)

| Prompt | Description |
|--------|-------------|
| `code_review` | コードレビュー実施 |
| `explain_codebase` | コードベース説明 |
| `implement_feature` | 機能実装ガイド |
| `debug_issue` | デバッグ支援 |
| `refactor_guidance` | リファクタリングガイド |
| `test_generation` | テスト生成 |

---

## Success Metrics

### Technical KPIs

| Metric | Target | Current |
|--------|--------|---------|
| インデックス速度 (100K行) | < 30 sec | ✅ |
| インクリメンタル更新 | < 2 sec | ✅ |
| クエリ応答 | < 500ms | ✅ < 2ms |
| テストカバレッジ | > 60% | ✅ 64% |
| テスト合格率 | 100% | ✅ 299/299 |

### Product KPIs

| Metric | Target |
|--------|--------|
| PyPI ダウンロード数 | 成長中 |
| GitHub スター | 成長中 |
| サポート言語数 | 12 ✅ |
| MCP ツール数 | 14 ✅ |

---

## Product Roadmap

### Phase 1: MVP ✅ (v0.1.0 - v0.3.0)

- ✅ 基本的な AST パーサー
- ✅ グラフエンジン
- ✅ MCP サーバー
- ✅ 5言語サポート (Python, TS, JS, Rust, Go)
- ✅ 基本的な CLI

### Phase 2: Feature Complete ✅ (v0.4.0 - v0.7.0)

- ✅ 12言語サポート
- ✅ GraphRAG (コミュニティ検出、グローバル/ローカル検索)
- ✅ LLM 統合 (OpenAI/Anthropic)
- ✅ ファイル監視 (watch コマンド)
- ✅ 14 MCP ツール
- ✅ 6 MCP プロンプト

### Phase 3: Production Ready (v0.8.0 - v1.0.0)

- [ ] パフォーマンス最適化
- [ ] ドキュメント充実
- [ ] プラグインシステム
- [ ] Web UI (オプション)

---

## Competitive Landscape

| Solution | Strengths | Weaknesses | Our Differentiation |
|----------|-----------|------------|---------------------|
| Language Servers (LSP) | 言語固有の深い理解 | 単一言語、非MCP | 多言語、MCP ネイティブ |
| Sourcegraph | 大規模対応 | 外部サービス依存 | ゼロ設定、ローカル完結 |
| GitHub Copilot (単体) | 広範な学習 | 構造理解が弱い | グラフベース構造理解 |

---

## Integration Points

### MCP Clients (対応済み)

| Client | Status | Configuration |
|--------|--------|---------------|
| Claude Desktop | ✅ | `claude_desktop_config.json` |
| Claude Code | ✅ | `claude mcp add` |
| VS Code (Copilot) | ✅ | `.vscode/settings.json` |
| Cursor | ✅ | `~/.cursor/mcp.json` |
| Windsurf | ✅ | MCP 設定 |

---

## Data & Privacy

### データ収集

- **収集するデータ**: コードの構造情報（AST）のみ
- **保存場所**: ローカル SQLite (`.codegraph/`)
- **外部送信**: なし (LLM 使用時のみ API 経由)

### プライバシー

- 完全ローカル動作可能
- OpenAI/Anthropic API 使用時のみ外部通信
- センシティブなコードは除外オプションあり

---

## Support

### ドキュメント

- README.md (英語/日本語)
- GitHub Issues

### コミュニティ

- GitHub Discussions
- Issue Tracker

---

**Last Updated**: 2025-12-04
**Maintained By**: GitHub Copilot / nahisaho
