```markdown
# CodeGraph MCP Server 要件定義書

**Project**: CodeGraph MCP Server
**Version**: 1.0.0
**Created**: 2025-11-26
**Status**: Draft
**Based On**: References/system-design.md

---

## 1. ドキュメント概要

### 1.1 目的

本ドキュメントは、CodeGraph MCP Serverの機能要件および非機能要件を EARS (Easy Approach to Requirements Syntax) 形式で定義します。

### 1.2 スコープ

- ソースコード分析に最適化されたMCPサーバーの開発
- GitHub Copilot、Claude Code、Cursor等のMCP対応AIツールとの統合
- GraphRAG機能によるコードベースの構造的理解の実現

### 1.3 対象読者

- システムアーキテクト
- ソフトウェア開発者
- QAエンジニア
- プロダクトオーナー

---

## 2. 製品ビジョン

### 2.1 ビジョンステートメント

Microsoft GraphRAGのコンセプトとcode-graph-ragの実装を参考に、ゼロ構成で起動可能な軽量・高速なソースコード分析MCPサーバーを提供し、AI支援開発の生産性を飛躍的に向上させる。

### 2.2 主要な差別化要素

| 要素 | CodeGraph MCP Server |
|------|---------------------|
| アーキテクチャ | MCP Native Server |
| グラフDB | SQLite + 組み込みグラフエンジン |
| デプロイ | シングルバイナリ / pip install |
| 起動時間 | 軽量 (秒単位) |
| スコープ | マルチリポジトリ対応 |
| インデックス更新 | Git差分ベース増分更新 |
| GraphRAG機能 | コミュニティ要約・グローバルクエリ |

---

## 3. 機能要件

### 3.1 コアエンジン要件

#### 3.1.1 ASTパーサー要件

| ID | 要件 | EARS パターン | 優先度 |
|----|------|---------------|--------|
| REQ-AST-001 | **WHEN** ユーザーがPythonファイルをインデックス対象として指定した場合、**THE SYSTEM SHALL** Tree-sitterを使用してAST解析を行い、関数定義、クラス定義、インポート文、関数呼び出しを抽出する | Event-driven | P0 |
| REQ-AST-002 | **WHEN** ユーザーがTypeScriptファイルをインデックス対象として指定した場合、**THE SYSTEM SHALL** 関数宣言、アロー関数、メソッド定義、クラス宣言、インターフェース宣言、インポート文、呼び出し式を抽出する | Event-driven | P0 |
| REQ-AST-003 | **WHEN** ユーザーがRustファイルをインデックス対象として指定した場合、**THE SYSTEM SHALL** 関数アイテム、構造体、列挙型、impl、use宣言、呼び出し式を抽出する | Event-driven | P1 |
| REQ-AST-004 | **THE SYSTEM SHALL** 対応言語の拡張子を自動認識し、適切なパーサーを選択する | Ubiquitous | P0 |
| REQ-AST-005 | **IF** 解析対象ファイルの構文エラーが検出された場合、**THEN THE SYSTEM SHALL** エラーをログに記録し、解析可能な部分のみを処理する | Unwanted behavior | P1 |

#### 3.1.2 グラフエンジン要件

| ID | 要件 | EARS パターン | 優先度 |
|----|------|---------------|--------|
| REQ-GRF-001 | **THE SYSTEM SHALL** コードエンティティ（File, Module, Class, Function, Method）をノードとしてグラフに格納する | Ubiquitous | P0 |
| REQ-GRF-002 | **THE SYSTEM SHALL** エンティティ間の関係（CALLS, IMPORTS, INHERITS, CONTAINS, IMPLEMENTS）をエッジとしてグラフに格納する | Ubiquitous | P0 |
| REQ-GRF-003 | **WHEN** エンティティが作成された場合、**THE SYSTEM SHALL** ID、型、名前、修飾名、ファイルパス、開始行、終了行、シグネチャ、ドキュメント文字列、ソースコード、埋め込みベクトル、コミュニティID、作成日時、更新日時を格納する | Event-driven | P0 |
| REQ-GRF-004 | **WHEN** 関係が作成された場合、**THE SYSTEM SHALL** ソースID、ターゲットID、関係タイプ、重み、メタデータを格納する | Event-driven | P0 |
| REQ-GRF-005 | **THE SYSTEM SHALL** SQLiteを使用してグラフデータを永続化する | Ubiquitous | P0 |
| REQ-GRF-006 | **THE SYSTEM SHALL** エンティティタイプ、ファイルパス、コミュニティID、関係ソース、関係ターゲット、関係タイプにインデックスを作成し、高速クエリを実現する | Ubiquitous | P0 |

#### 3.1.3 セマンティック分析要件（GraphRAG機能）

| ID | 要件 | EARS パターン | 優先度 |
|----|------|---------------|--------|
| REQ-SEM-001 | **WHEN** エンティティが新規作成された場合、**THE SYSTEM SHALL** LLMを使用してエンティティの自然言語説明を生成する | Event-driven | P1 |
| REQ-SEM-002 | **WHEN** コミュニティが検出された場合、**THE SYSTEM SHALL** LLMを使用してモジュールコミュニティの要約を生成する | Event-driven | P1 |
| REQ-SEM-003 | **THE SYSTEM SHALL** コミュニティ検出アルゴリズムを使用して関連するコードエンティティをクラスタリングする | Ubiquitous | P1 |
| REQ-SEM-004 | **THE SYSTEM SHALL** 階層レベル（0=細粒度、1=粗粒度など）でコミュニティを管理する | Ubiquitous | P1 |

---

### 3.2 MCPプロトコル要件

#### 3.2.1 トランスポート要件

| ID | 要件 | EARS パターン | 優先度 |
|----|------|---------------|--------|
| REQ-TRP-001 | **THE SYSTEM SHALL** stdio トランスポートをサポートする | Ubiquitous | P0 |
| REQ-TRP-002 | **THE SYSTEM SHALL** SSE (Server-Sent Events) トランスポートをサポートする | Ubiquitous | P1 |
| REQ-TRP-003 | **THE SYSTEM SHALL** Streamable HTTP トランスポートをサポートする | Ubiquitous | P2 |
| REQ-TRP-004 | **THE SYSTEM SHALL** JSON-RPC 2.0 メッセージハンドリングを実装する | Ubiquitous | P0 |
| REQ-TRP-005 | **WHERE** OAuth 2.1 認証が有効化されている場合、**THE SYSTEM SHALL** 認証済みクライアントのみにアクセスを許可する | Optional features | P2 |

#### 3.2.2 Tools 要件

##### グラフクエリツール

| ID | 要件 | EARS パターン | 優先度 |
|----|------|---------------|--------|
| REQ-TLS-001 | **WHEN** `query_codebase` ツールが自然言語クエリとスコープで呼び出された場合、**THE SYSTEM SHALL** 指定されたスコープ（all, functions, classes, files）内でマッチするコードエンティティを返す | Event-driven | P0 |
| REQ-TLS-002 | **WHEN** `find_dependencies` ツールがエンティティ名、方向、深さで呼び出された場合、**THE SYSTEM SHALL** 指定された方向（upstream, downstream, both）と深さで依存関係グラフを返す | Event-driven | P0 |
| REQ-TLS-003 | **WHEN** `find_callers` ツールが関数名と最大深さで呼び出された場合、**THE SYSTEM SHALL** 指定関数を呼び出しているすべての関数の呼び出しパスを返す | Event-driven | P0 |
| REQ-TLS-004 | **WHEN** `find_callees` ツールが関数名と最大深さで呼び出された場合、**THE SYSTEM SHALL** 指定関数が呼び出しているすべての関数の呼び出しパスを返す | Event-driven | P0 |
| REQ-TLS-005 | **WHEN** `find_implementations` ツールがインターフェース名で呼び出された場合、**THE SYSTEM SHALL** そのインターフェース/抽象クラスのすべての実装を返す | Event-driven | P0 |
| REQ-TLS-006 | **WHEN** `analyze_module_structure` ツールがモジュールパスで呼び出された場合、**THE SYSTEM SHALL** モジュールの構造分析（クラス、関数、依存関係の概要）を返す | Event-driven | P0 |

##### コード取得ツール

| ID | 要件 | EARS パターン | 優先度 |
|----|------|---------------|--------|
| REQ-TLS-007 | **WHEN** `get_code_snippet` ツールがエンティティ名とコンテキストフラグで呼び出された場合、**THE SYSTEM SHALL** エンティティのソースコードを返し、コンテキストフラグが真の場合は前後の指定行数も含める | Event-driven | P0 |
| REQ-TLS-008 | **WHEN** `read_file_content` ツールがファイルパスと行範囲で呼び出された場合、**THE SYSTEM SHALL** 指定されたファイルの内容を返す | Event-driven | P0 |
| REQ-TLS-009 | **WHEN** `get_file_structure` ツールがファイルパスで呼び出された場合、**THE SYSTEM SHALL** ファイル内のクラス・関数の構造情報を返す | Event-driven | P0 |

##### GraphRAG ツール

| ID | 要件 | EARS パターン | 優先度 |
|----|------|---------------|--------|
| REQ-TLS-010 | **WHEN** `global_search` ツールがクエリとコミュニティレベルで呼び出された場合、**THE SYSTEM SHALL** コミュニティサマリーを使用してコードベース全体に関するマクロレベルの回答を返す | Event-driven | P1 |
| REQ-TLS-011 | **WHEN** `local_search` ツールがクエリとコンテキストエンティティで呼び出された場合、**THE SYSTEM SHALL** グラフ構造とエンティティ情報を組み合わせて詳細な回答を返す | Event-driven | P1 |

##### 編集・管理ツール

| ID | 要件 | EARS パターン | 優先度 |
|----|------|---------------|--------|
| REQ-TLS-012 | **WHEN** `suggest_refactoring` ツールがエンティティ名とリファクタリングタイプで呼び出された場合、**THE SYSTEM SHALL** リファクタリングの提案と影響範囲の分析を返す | Event-driven | P2 |
| REQ-TLS-013 | **WHEN** `reindex_repository` ツールがパスと増分フラグで呼び出された場合、**THE SYSTEM SHALL** 指定リポジトリをインデックス（増分または完全）し、結果を返す | Event-driven | P0 |
| REQ-TLS-014 | **WHEN** `execute_shell_command` ツールがコマンド、作業ディレクトリ、タイムアウトで呼び出された場合、**THE SYSTEM SHALL** シェルコマンドを実行し結果を返す | Event-driven | P1 |

#### 3.2.3 Resources 要件

| ID | 要件 | EARS パターン | 優先度 |
|----|------|---------------|--------|
| REQ-RSC-001 | **WHEN** `codegraph://entities/{entity_id}` リソースが要求された場合、**THE SYSTEM SHALL** コードエンティティの詳細情報をJSONで返す | Event-driven | P0 |
| REQ-RSC-002 | **WHEN** `codegraph://files/{file_path}` リソースが要求された場合、**THE SYSTEM SHALL** ファイルの構造情報付きリソースを返す | Event-driven | P0 |
| REQ-RSC-003 | **WHEN** `codegraph://communities/{community_id}` リソースが要求された場合、**THE SYSTEM SHALL** コミュニティ（モジュールクラスター）のサマリーを返す | Event-driven | P1 |
| REQ-RSC-004 | **WHEN** `codegraph://stats` リソースが要求された場合、**THE SYSTEM SHALL** コードベースの統計情報（総ファイル数、関数数、クラス数、言語内訳、最終インデックス日時）を返す | Event-driven | P0 |

#### 3.2.4 Prompts 要件

| ID | 要件 | EARS パターン | 優先度 |
|----|------|---------------|--------|
| REQ-PRM-001 | **WHEN** `code_review` プロンプトがファイルパスと重点領域で呼び出された場合、**THE SYSTEM SHALL** コードレビュー実施のためのプロンプトテンプレートを返す | Event-driven | P1 |
| REQ-PRM-002 | **WHEN** `explain_codebase` プロンプトが呼び出された場合、**THE SYSTEM SHALL** コードベース全体の説明を生成するためのプロンプトテンプレートを返す | Event-driven | P1 |
| REQ-PRM-003 | **WHEN** `implement_feature` プロンプトが機能説明で呼び出された場合、**THE SYSTEM SHALL** 新機能実装のガイダンスプロンプトを返す | Event-driven | P1 |
| REQ-PRM-004 | **WHEN** `debug_issue` プロンプトがエラーメッセージで呼び出された場合、**THE SYSTEM SHALL** デバッグ支援プロンプトを返す | Event-driven | P1 |
| REQ-PRM-005 | **WHEN** `refactor_guidance` プロンプトがターゲットエンティティで呼び出された場合、**THE SYSTEM SHALL** リファクタリングガイダンスプロンプトを返す | Event-driven | P2 |
| REQ-PRM-006 | **WHEN** `test_generation` プロンプトが関数名で呼び出された場合、**THE SYSTEM SHALL** テストコード生成支援プロンプトを返す | Event-driven | P1 |

---

### 3.3 ストレージ要件

| ID | 要件 | EARS パターン | 優先度 |
|----|------|---------------|--------|
| REQ-STR-001 | **THE SYSTEM SHALL** SQLiteを使用してグラフデータベースを管理する | Ubiquitous | P0 |
| REQ-STR-002 | **THE SYSTEM SHALL** ASTキャッシュをファイルキャッシュとして管理する | Ubiquitous | P0 |
| REQ-STR-003 | **THE SYSTEM SHALL** エンベディング（ベクトル）をベクトルストアとして管理する | Ubiquitous | P1 |
| REQ-STR-004 | **WHEN** ファイルが変更された場合、**THE SYSTEM SHALL** Git差分を使用して変更ファイルのみを再インデックスする | Event-driven | P0 |

---

### 3.4 インデックス管理要件

| ID | 要件 | EARS パターン | 優先度 |
|----|------|---------------|--------|
| REQ-IDX-001 | **WHEN** ユーザーが `codegraph-mcp serve` コマンドを実行した場合、**THE SYSTEM SHALL** 指定リポジトリのインデックスを作成または読み込む | Event-driven | P0 |
| REQ-IDX-002 | **WHEN** 増分インデックスが要求された場合、**THE SYSTEM SHALL** Git差分を解析し、変更されたファイルのみを再処理する | Event-driven | P0 |
| REQ-IDX-003 | **WHEN** 完全インデックスが要求された場合、**THE SYSTEM SHALL** すべてのファイルを再解析してインデックスを再構築する | Event-driven | P0 |
| REQ-IDX-004 | **THE SYSTEM SHALL** .gitignore パターンに従ってファイルをフィルタリングする | Ubiquitous | P0 |

---

### 3.5 CLI 要件

| ID | 要件 | EARS パターン | 優先度 |
|----|------|---------------|--------|
| REQ-CLI-001 | **WHEN** ユーザーが `codegraph-mcp serve` コマンドを実行した場合、**THE SYSTEM SHALL** MCPサーバーを起動する | Event-driven | P0 |
| REQ-CLI-002 | **WHEN** ユーザーが `--repo` オプションを指定した場合、**THE SYSTEM SHALL** 指定されたリポジトリパスをインデックス対象とする | Event-driven | P0 |
| REQ-CLI-003 | **WHEN** ユーザーが `--help` オプションを指定した場合、**THE SYSTEM SHALL** 使用方法とオプションのヘルプテキストを表示する | Event-driven | P0 |
| REQ-CLI-004 | **THE SYSTEM SHALL** `pip install codegraph-mcp` でインストール可能なパッケージとして提供する | Ubiquitous | P0 |

---

## 4. 非機能要件

### 4.1 パフォーマンス要件

| ID | 要件 | EARS パターン | 目標値 | 優先度 |
|----|------|---------------|--------|--------|
| REQ-NFR-001 | **THE SYSTEM SHALL** 10万行規模のコードベースを30秒以内にインデックスする | Ubiquitous | < 30秒 | P0 |
| REQ-NFR-002 | **THE SYSTEM SHALL** 増分インデックスを2秒以内に完了する | Ubiquitous | < 2秒 | P0 |
| REQ-NFR-003 | **THE SYSTEM SHALL** クエリを500ミリ秒以内に応答する | Ubiquitous | < 500ms | P0 |
| REQ-NFR-004 | **THE SYSTEM SHALL** 起動を2秒以内に完了する | Ubiquitous | < 2秒 | P0 |

### 4.2 リソース要件

| ID | 要件 | EARS パターン | 目標値 | 優先度 |
|----|------|---------------|--------|--------|
| REQ-NFR-005 | **WHILE** サーバーが稼働中の場合、**THE SYSTEM SHALL** メモリ使用量を500MB以下に維持する | State-driven | < 500MB | P0 |
| REQ-NFR-006 | **THE SYSTEM SHALL** 10万行あたりのディスク使用量を100MB以下に維持する | Ubiquitous | < 100MB/10万行 | P1 |

### 4.3 可用性要件

| ID | 要件 | EARS パターン | 優先度 |
|----|------|---------------|--------|
| REQ-NFR-007 | **THE SYSTEM SHALL** 外部データベースサービスなしで動作する（自己完結型） | Ubiquitous | P0 |
| REQ-NFR-008 | **IF** サーバーが予期せずクラッシュした場合、**THEN THE SYSTEM SHALL** 次回起動時に既存のインデックスを復元する | Unwanted behavior | P0 |

### 4.4 互換性要件

| ID | 要件 | EARS パターン | 優先度 |
|----|------|---------------|--------|
| REQ-NFR-009 | **THE SYSTEM SHALL** Python 3.11以上で動作する | Ubiquitous | P0 |
| REQ-NFR-010 | **THE SYSTEM SHALL** MCP Specification 1.0に準拠する | Ubiquitous | P0 |
| REQ-NFR-011 | **THE SYSTEM SHALL** GitHub Copilot、Claude Code、Cursor、Windsurfと互換性を持つ | Ubiquitous | P0 |

### 4.5 セキュリティ要件

| ID | 要件 | EARS パターン | 優先度 |
|----|------|---------------|--------|
| REQ-NFR-012 | **WHILE** シェルコマンド実行ツールが使用される場合、**THE SYSTEM SHALL** サンドボックス環境またはタイムアウト制限を適用する | State-driven | P1 |
| REQ-NFR-013 | **THE SYSTEM SHALL** ローカルファイルシステムへのアクセスを指定されたリポジトリパスに制限する | Ubiquitous | P0 |

---

## 5. 対応言語

### 5.1 Phase 1（P0 - MVP）

| 言語 | 拡張子 | 対応スコープ |
|------|--------|--------------|
| Python | .py | 関数、クラス、インポート、呼び出し |
| TypeScript | .ts, .tsx | 関数、クラス、インターフェース、インポート、呼び出し |

### 5.2 Phase 2（P1）

| 言語 | 拡張子 | 対応スコープ |
|------|--------|--------------|
| Rust | .rs | 関数、構造体、列挙型、impl、use、呼び出し |
| JavaScript | .js, .jsx | 関数、クラス、インポート、呼び出し |

### 5.3 Phase 3（P2）

| 言語 | 拡張子 |
|------|--------|
| Go | .go |
| Java | .java |
| C# | .cs |

---

## 6. トレーサビリティマトリクス

### 6.1 設計コンポーネントへのマッピング

| 要件 ID | 設計コンポーネント | ソースファイル（予定） |
|---------|-------------------|----------------------|
| REQ-AST-* | AST Parser | src/codegraph_mcp/core/parser.py |
| REQ-GRF-* | Graph Engine | src/codegraph_mcp/core/graph.py |
| REQ-SEM-* | Semantic Analyzer | src/codegraph_mcp/core/semantic.py |
| REQ-TRP-* | MCP Protocol Layer | src/codegraph_mcp/server.py |
| REQ-TLS-* | MCP Tools | src/codegraph_mcp/mcp/tools.py |
| REQ-RSC-* | MCP Resources | src/codegraph_mcp/mcp/resources.py |
| REQ-PRM-* | MCP Prompts | src/codegraph_mcp/mcp/prompts.py |
| REQ-STR-* | Storage Layer | src/codegraph_mcp/storage/*.py |
| REQ-IDX-* | Indexer | src/codegraph_mcp/core/indexer.py |
| REQ-CLI-* | CLI | src/codegraph_mcp/__main__.py |
| REQ-NFR-* | 全コンポーネント | - |

---

## 7. 受け入れ基準

### 7.1 MVP 受け入れ基準

- [ ] `pip install codegraph-mcp` でインストール可能
- [ ] `codegraph-mcp serve --repo <path>` で起動可能
- [ ] Python/TypeScript のAST解析が動作
- [ ] 基本6ツール（query_codebase, find_dependencies, find_callers, find_callees, get_code_snippet, read_file_content）が動作
- [ ] 4リソースタイプすべてがアクセス可能
- [ ] 10万行規模のコードベースで30秒以内にインデックス完了
- [ ] Claude Desktop / GitHub Copilot での動作確認

### 7.2 Phase 2 受け入れ基準

- [ ] GraphRAG機能（global_search, local_search）が動作
- [ ] コミュニティ検出とサマリー生成が動作
- [ ] 6 Promptsすべてが利用可能
- [ ] Rust言語サポート

### 7.3 Phase 3 受け入れ基準

- [ ] 追加言語サポート（Go, Java, C#）
- [ ] ベクトル検索によるセマンティック検索
- [ ] リファクタリング提案ツール

---

## 8. 用語集

| 用語 | 定義 |
|------|------|
| MCP | Model Context Protocol - AIモデルが外部ツールやリソースにアクセスするためのプロトコル |
| GraphRAG | Graph-based Retrieval Augmented Generation - グラフ構造を活用したRAG |
| AST | Abstract Syntax Tree - ソースコードの抽象構文木 |
| Tree-sitter | 高速な増分パーサー生成ライブラリ |
| EARS | Easy Approach to Requirements Syntax - 要件記述のための構造化形式 |
| エンティティ | コードグラフのノード（File, Module, Class, Function, Method） |
| リレーション | コードグラフのエッジ（CALLS, IMPORTS, INHERITS, CONTAINS, IMPLEMENTS） |
| コミュニティ | 関連するエンティティのクラスター |

---

## 9. 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|------------|------|----------|--------|
| 1.0.0 | 2025-11-26 | 初版作成 | System |

---

## 10. 承認

| 役割 | 名前 | 署名 | 日付 |
|------|------|------|------|
| プロダクトオーナー | | | |
| テックリード | | | |
| QAリード | | | |

---

**Document Status**: Draft
**Constitutional Compliance**: Article IV (EARS Format) ✓
```
