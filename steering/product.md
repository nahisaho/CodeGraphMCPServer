# Product Context

**Project**: CodeGraph MCP Server
**Last Updated**: 2025-12-11
**Version**: 2.7
**Synced With**: requirements-specification.md, design-*.md, CHANGELOG.md (v0.7.1)

---

## Product Vision

**Vision Statement**: 

Microsoft GraphRAGのコンセプトとcode-graph-ragの実装を参考に、ゼロ構成で起動可能な軽量・高速なソースコード分析MCPサーバーを提供し、AI支援開発の生産性を飛躍的に向上させる。

**Mission**: 

外部データベース不要の自己完結型アーキテクチャで、MCP対応AIツール（GitHub Copilot、Claude Code、Cursor等）からコードベースの構造的理解と効率的なコード補完を実現する。

---

## Product Overview

### What is CodeGraph MCP Server?

CodeGraph MCP Serverは、ソースコード分析に最適化されたMCP（Model Context Protocol）サーバーです。Tree-sitterによるAST解析とGraphRAG技術を組み合わせ、コードベースの構造的理解をAIアシスタントに提供します。

従来のcode-graph-ragと異なり、外部のグラフデータベース（Memgraph等）を必要とせず、SQLiteによる組み込みグラフエンジンで動作します。これにより、`pip install codegraph-mcp && codegraph-mcp serve` の一コマンドで即座に利用開始できます。

### Problem Statement

**Problem**: 

現在のAIコーディングアシスタントは、大規模コードベースの全体像を把握することが困難です。ファイル単位での理解に留まり、モジュール間の依存関係、呼び出しグラフ、アーキテクチャパターンを認識できません。また、既存のcode-graph-ragソリューションは外部データベースの設定が必要で、導入障壁が高いという課題があります。

### Solution

**Solution**: 

CodeGraph MCP Serverは以下のアプローチでこれらの問題を解決します：

1. **ゼロ構成起動**: 外部依存なしで即座に利用可能
2. **グラフベースの理解**: コードエンティティと関係をグラフとして管理
3. **GraphRAG統合**: コミュニティ検出とLLM要約によるマクロレベルの理解
4. **MCP Native**: Tools, Resources, Promptsを活用した包括的なMCP実装
5. **増分更新**: Git差分を活用した効率的なインデックス更新

---

## Target Users

### Primary Users

#### User Persona 1: AIアシスタント活用開発者

**Demographics**:

- **Role**: ソフトウェア開発者
- **Organization Size**: 小〜大規模
- **Technical Level**: 中〜上級

**Goals**:

- AI支援でコーディング効率を向上させたい
- 大規模コードベースを素早く理解したい
- 既存コードへの影響範囲を正確に把握したい

**Pain Points**:

- AIアシスタントがコードベース全体を理解できない
- 関数の呼び出し元・呼び出し先を追跡するのが面倒
- 外部ツールの設定が複雑で導入を諦める

**Use Cases**:

- コードベース全体のアーキテクチャ理解 (REQ-TLS-010)
- 関数変更時の影響範囲分析 (REQ-TLS-002, REQ-TLS-003)
- 新機能実装時の既存コード調査 (REQ-TLS-001)

---

#### User Persona 2: チームリード・アーキテクト

**Demographics**:

- **Role**: テックリード / ソフトウェアアーキテクト
- **Organization Size**: 中〜大規模
- **Technical Level**: 上級

**Goals**:

- コードベースの品質を維持・向上させたい
- 新メンバーのオンボーディングを効率化したい
- 技術的負債を可視化・管理したい

**Pain Points**:

- コードベースの全体像を説明するのが大変
- リファクタリングの影響範囲把握に時間がかかる
- モジュール間の依存関係が複雑化している

**Use Cases**:

- コードベース説明の自動生成 (REQ-PRM-002)
- リファクタリング影響分析 (REQ-TLS-012)
- モジュール構造の分析 (REQ-TLS-006)

---

### Secondary Users

- **QAエンジニア**: テスト対象の特定、影響範囲の把握
- **新規参画メンバー**: コードベースの学習、ナビゲーション

---

## Competitive Landscape

### code-graph-rag との差別化

| 観点 | code-graph-rag | CodeGraph MCP Server |
|------|----------------|---------------------|
| アーキテクチャ | CLI + Interactive Mode | MCP Native Server |
| グラフDB | Memgraph (外部依存) | SQLite + 組み込みグラフエンジン |
| デプロイ | Docker必須 | シングルバイナリ / pip install |
| 起動時間 | 重い (DB起動含む) | 軽量 (秒単位) |
| MCP統合 | 後付け対応 | ネイティブ設計 |
| スコープ | 単一リポジトリ | マルチリポジトリ対応 |
| インデックス更新 | 手動 / ファイル監視 | Git差分ベース増分更新 |
| GraphRAG機能 | なし | コミュニティ要約・グローバルクエリ |

---

## Core Product Capabilities

### Must-Have Features (MVP - Phase 1)

1. **AST解析 (Python, TypeScript)**
   - **Description**: Tree-sitterによるAST解析
   - **User Value**: コード構造の正確な抽出
   - **Priority**: P0 (Critical)
   - **Requirements**: REQ-AST-001, REQ-AST-002

2. **グラフクエリツール**
   - **Description**: 6種のグラフクエリツール
   - **User Value**: 依存関係・呼び出し関係の探索
   - **Priority**: P0 (Critical)
   - **Requirements**: REQ-TLS-001 ~ REQ-TLS-006

3. **コード取得ツール**
   - **Description**: 3種のコード取得ツール
   - **User Value**: ソースコードの効率的な取得
   - **Priority**: P0 (Critical)
   - **Requirements**: REQ-TLS-007 ~ REQ-TLS-009

4. **MCPリソース**
   - **Description**: 4種のリソースタイプ
   - **User Value**: コードベース情報へのアクセス
   - **Priority**: P0 (Critical)
   - **Requirements**: REQ-RSC-001 ~ REQ-RSC-004

5. **CLIインターフェース**
   - **Description**: serve, index コマンド
   - **User Value**: 簡単な起動とインデックス作成
   - **Priority**: P0 (Critical)
   - **Requirements**: REQ-CLI-001 ~ REQ-CLI-004

### High-Priority Features (Phase 2)

6. **GraphRAG機能**
   - **Description**: global_search, local_search ツール
   - **User Value**: マクロレベルのコードベース理解
   - **Priority**: P1 (High)
   - **Requirements**: REQ-TLS-010, REQ-TLS-011

7. **コミュニティ検出**
   - **Description**: モジュールクラスタリングと要約
   - **User Value**: アーキテクチャの自動理解
   - **Priority**: P1 (High)
   - **Requirements**: REQ-SEM-001 ~ REQ-SEM-004

8. **プロンプトテンプレート**
   - **Description**: 6種のプロンプト
   - **User Value**: AIアシスタントとの効率的な対話
   - **Priority**: P1 (High)
   - **Requirements**: REQ-PRM-001 ~ REQ-PRM-006

9. **Rust言語サポート**
   - **Description**: Rust AST解析
   - **User Value**: Rustプロジェクトへの対応
   - **Priority**: P1 (High)
   - **Requirements**: REQ-AST-003

### Future Features (Phase 3)

10. **追加言語サポート**
    - **Description**: Go, Java, C#
    - **User Value**: より多くのプロジェクトへの対応
    - **Priority**: P2 (Medium)

11. **リファクタリング提案**
    - **Description**: suggest_refactoring ツール
    - **User Value**: コード品質向上の支援
    - **Priority**: P2 (Medium)
    - **Requirements**: REQ-TLS-012

12. **ベクトル検索**
    - **Description**: セマンティック検索
    - **User Value**: より高度な検索機能
    - **Priority**: P2 (Medium)
    - **Requirements**: REQ-STR-003

---

## Product Principles

### Design Principles

1. **ゼロ構成起動**
   - 外部依存を最小化し、インストール後すぐに使用可能

2. **軽量・高速**
   - 外部DB不要、起動2秒以内、10万行30秒以内のインデックス

3. **MCP First**
   - Tools, Resources, Promptsを活用した包括的なMCP実装

4. **増分更新**
   - Git差分を活用し、変更ファイルのみを再インデックス

---

## Success Metrics

### Key Performance Indicators (KPIs)

#### Technical Metrics

| Metric | Target | Actual (v0.5.0) | Requirements |
|--------|--------|-----------------|-------------|
| 初回インデックス (10万行) | < 30秒 | **0.63秒** (67 files) | REQ-NFR-001 |
| 増分インデックス | < 2秒 | < 0.5秒 | REQ-NFR-002 |
| クエリレスポンス | < 500ms | < 2ms | REQ-NFR-003 |
| 起動時間 | < 2秒 | < 1秒 | REQ-NFR-004 |
| メモリ使用量 | < 500MB | ~200MB | REQ-NFR-005 |
| エンティティ/秒 | - | **1,495** (47x improved) | - |

#### Product Metrics (将来)

| Metric | Target |
|--------|--------|
| PyPIダウンロード数 | 1,000+/月 |
| GitHub Stars | 500+ |
| Active Users (推定) | 100+ |

---

## Product Roadmap

### Phase 1: MVP (Week 1-4)

**Goal**: 基本機能のリリース

**Features**:

- Python/TypeScript AST解析
- 基本ツール（query, dependencies, callers, callees, code_snippet, file_content）
- SQLiteストレージ
- CLIインターフェース
- stdio トランスポート

**Success Criteria**:

- `pip install codegraph-mcp` でインストール可能
- Claude Desktop / GitHub Copilot での動作確認
- 10万行規模のコードベースで30秒以内にインデックス完了

---

### Phase 2: GraphRAG (Week 5-6) ✅ COMPLETED

**Goal**: GraphRAG機能の実装

**Features**:

- ✅ コミュニティ検出 (`core/community.py`)
- ✅ LLM統合（サマリー生成）(`core/llm.py`, `core/semantic.py`)
- ✅ global_search, local_search (`core/graphrag.py`)
- ✅ 6 Prompts (`mcp/prompts.py`)
- ⏳ Rust言語サポート (Phase 3へ移動)

**Implementation Status**:

| Component | File | Tests |
|-----------|------|-------|
| LLM Integration | `core/llm.py` | `test_llm.py` (11 tests) |
| GraphRAG Search | `core/graphrag.py` | `test_graphrag.py` (14 tests) |
| Community Detection | `core/community.py` | `test_community.py` |
| Semantic Analysis | `core/semantic.py` | `test_semantic.py` |
| Integration Tests | - | `test_graphrag_integration.py` (13 tests) |

**Total Tests**: 173 (172 passed, 1 skipped)

**Success Criteria**:

- ✅ コードベース全体の説明が生成可能
- ✅ コミュニティサマリーが機能する

---

### Phase 3: Polish & Extensions (Week 7-8) ✅ COMPLETED

**Goal**: 品質向上と拡張

**Features**:

- ✅ Rust言語サポート (`languages/rust.py`)
- ✅ JavaScript言語サポート (`languages/javascript.py`)
- ✅ SSEトランスポート (`server.py`)
- ✅ リファクタリング提案 (`mcp/tools.py`)
- ✅ ドキュメント整備 (`docs/`)
- ✅ PyPIリリース準備

**Implementation Status**:

| Component | File | Status |
|-----------|------|--------|
| Rust Parser | `languages/rust.py` | ✅ Complete |
| JavaScript Parser | `languages/javascript.py` | ✅ Complete |
| SSE Transport | `server.py` | ✅ Complete |
| API Docs | `docs/api.md` | ✅ Complete |
| Config Guide | `docs/configuration.md` | ✅ Complete |
| Examples | `docs/examples.md` | ✅ Complete |
| CHANGELOG | `CHANGELOG.md` | ✅ Complete |
| Release Notes | `RELEASE_NOTES.md` | ✅ Complete |

**Total Tests**: 182 (182 passed, 1 skipped)

**Performance**:
- Index: 696 entities in 21 seconds
- Query: < 2ms average

**Success Criteria**:

- ✅ 追加言語でのAST解析が動作
- ✅ ドキュメント完備
- ✅ PyPIパッケージビルド成功

---

### Phase 4: Future (Planned)

**Goal**: 更なる拡張

**Planned Features**:

- 追加言語サポート（Go, Java, C#）
- ベクトル検索の最適化
- MkDocsドキュメントサイト
- GitHub Actions CI/CD
- 100k行+リポジトリの最適化

---

## User Workflows

### Primary Workflow 1: コードベース理解

**User Goal**: 新しいコードベースの全体像を理解する

**Steps**:

1. User: `codegraph-mcp serve --repo /path/to/project` を実行
2. System: インデックスを作成しMCPサーバーを起動
3. User: AIアシスタントで「このプロジェクトの主要なコンポーネントを説明して」と質問
4. System: global_search ツールでコミュニティサマリーを取得
5. System: 主要なモジュールとその責務を説明
6. User: プロジェクトの全体像を理解

**Success Criteria**:

- ワークフロー完了まで < 2分
- 主要コンポーネントが正確に特定される

---

### Primary Workflow 2: 影響範囲分析

**User Goal**: 関数変更時の影響範囲を把握する

**Steps**:

1. User: 「UserService.authenticate メソッドを変更した場合の影響範囲は？」と質問
2. System: find_callers ツールで呼び出し元を検索
3. System: 直接・間接の影響範囲をリスト表示
4. User: 影響範囲を確認し、テスト計画を立案

**Success Criteria**:

- 呼び出し元が正確に特定される
- 間接的な依存関係も表示される

---

## Domain Concepts

### Key Concepts

1. **Entity（エンティティ）**: コードグラフのノード
   - File, Module, Class, Function, Method

2. **Relation（関係）**: コードグラフのエッジ
   - CALLS, IMPORTS, INHERITS, CONTAINS, IMPLEMENTS

3. **Community（コミュニティ）**: 関連エンティティのクラスター
   - 階層レベル（0=細粒度、1=粗粒度など）

4. **MCP (Model Context Protocol)**: AIモデルが外部ツールやリソースにアクセスするためのプロトコル

5. **GraphRAG**: グラフ構造を活用したRAG（Retrieval Augmented Generation）

---

## Constraints & Requirements

### Technical Constraints

- **Python 3.11+**: REQ-NFR-009
- **MCP Specification 1.0**: REQ-NFR-010
- **外部DB不要**: 自己完結型アーキテクチャ

### Non-Functional Requirements

- **Performance**: REQ-NFR-001 ~ REQ-NFR-004
- **Resource**: REQ-NFR-005 ~ REQ-NFR-006
- **Security**: REQ-NFR-012 ~ REQ-NFR-013
- **Compatibility**: REQ-NFR-009 ~ REQ-NFR-011

---

## Future Extensions

1. **VS Code Extension**: 直接統合
2. **Web UI**: グラフ可視化ダッシュボード
3. **マルチリポジトリ**: モノレポ/マルチレポ対応
4. **リアルタイム更新**: LSP統合
5. **コード生成**: テンプレートベースのコード生成支援

---

## References

- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Microsoft GraphRAG](https://github.com/microsoft/graphrag)
- [code-graph-rag](https://github.com/vitali87/code-graph-rag)
- [Tree-sitter Documentation](https://tree-sitter.github.io/tree-sitter/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

---

## Changelog

### Version 2.6 (2025-11-27)

- v0.7.0リリース:
  - `watch`コマンド: ファイル監視・自動再インデックス
    - `--debounce`オプション（デフォルト: 1.0秒）
    - `--community`フラグで再インデックス後にコミュニティ検出
  - GitHub Actions CI/CD:
    - CI: Python 3.11/3.12テスト、ruff lint、mypy型チェック、Codecovカバレッジ
    - Release: タグプッシュで自動PyPIリリース
- テスト: 308 passed, 1 skipped

### Version 2.5 (2025-11-27)

- v0.6.2リリース:
  - 大規模リポジトリ対応（230K+エンティティ）
  - コミュニティ検出のパフォーマンス改善（サンプリング、バッチ処理）
  - Rustコンパイラリポジトリで検証済み
- テスト: 300 passed

### Version 2.4 (2025-11-27)

- v0.6.0-dev機能追加:
  - entity_id部分一致検索
  - 自動コミュニティ検出
  - query_codebase改善
- テスト: 294 passed

### Version 2.3 (2025-11-27)

- v0.5.0リリース（47xパフォーマンス改善）
- バッチDB書き込み実装
- 11言語サポート: Python, TypeScript, JavaScript, Rust, Go, Java, PHP, C#, C++, HCL, Ruby
- テスト: 285 passed
- PyPI: codegraph-mcp-server v0.5.0

### Version 2.2 (2025-11-26)

- Phase 3 (Polish & Extensions) 完了を反映
- 全タスク完了（TASK-001〜064）
- テスト: 182 passed
- ドキュメント: docs/api.md, configuration.md, examples.md
- リリース準備: CHANGELOG.md, RELEASE_NOTES.md

### Version 2.1 (2025-11-26)

- Phase 2 (GraphRAG) 完了を反映
- 実装ステータス（173テスト、172 passed）を追加
- Rust言語サポートをPhase 3へ移動

### Version 2.0 (2025-11-26)

- 設計書（design-*.md）との同期
- ADR-001〜010の決定を反映
- 要件定義書との整合性確認

### Version 1.1 (2025-11-26)

- Updated based on requirements specification
- Added competitive landscape
- Added user personas with use cases
- Added product roadmap
- Added user workflows
- Added domain concepts

### Version 1.0 (2025-11-26)

- Initial product context

---

**Last Updated**: 2025-11-27
**Maintained By**: MUSUBI SDD
