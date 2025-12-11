# 変更履歴

[🇺🇸 English Version](CHANGELOG.md)

このプロジェクトの注目すべき変更はすべてこのファイルに記録されます。

フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に基づいており、
このプロジェクトは [セマンティックバージョニング](https://semver.org/lang/ja/) に準拠しています。

## [0.8.0] - 2025-12-11

### 追加

#### 新言語サポート（4言語）
- **Kotlin** (`kotlin.py`): クラス、インターフェース、オブジェクト、関数、プロパティ
  - 対応拡張子: `.kt`, `.kts`
  - tree-sitter-kotlin >= 1.0.0
- **Swift** (`swift.py`): クラス、構造体、プロトコル、関数、エクステンション
  - 対応拡張子: `.swift`
  - tree-sitter-swift >= 0.0.1
- **Scala** (`scala.py`): クラス、トレイト、オブジェクト、関数
  - 対応拡張子: `.scala`, `.sc`
  - tree-sitter-scala >= 0.20.0
- **Lua** (`lua.py`): 関数、ローカル関数、テーブル代入
  - 対応拡張子: `.lua`
  - tree-sitter-lua >= 0.1.0

### 変更
- 対応言語数: **16言語**（12言語から増加）
- parser.pyに新言語のLANGUAGE_EXTENSIONSを追加
- `__init__.py`に新エクストラクタ登録を追加

### テスト
- Kotlin、Swift、Scala、Lua エクストラクタ用に26件の新規テストを追加
- 合計: **334 passed**, 1 skipped

---

## [0.7.1] - 2025-11-27

### 追加

#### C言語サポート
- `.c` ファイル拡張子のサポートを追加（純粋なC言語）
- CファイルはTree-sitter C++パーサーで解析
- 対応拡張子: `.c`, `.cpp`, `.cc`, `.cxx`, `.h`, `.hpp`, `.hxx`
- 対応言語数: **12言語**（11言語から増加）

#### Qiita記事メタデータ
- Qiitaフロントマター（タグ、非公開設定、更新日時など）を追加

### 変更
- cpp.pyエクストラクタのdocstringを「C/C++固有」に更新
- parser.pyのLANGUAGE_EXTENSIONSにC/C++マッピングを追加

---

## [0.7.0] - 2025-11-27

### 追加

#### ファイル監視（`watch`コマンド）
- **`codegraph-mcp watch`**: リポジトリを監視し、ファイル変更時に自動再インデックス
  - 設定可能なデバウンスによるリアルタイムファイル監視
  - `--debounce` オプションで変更間の遅延を設定（デフォルト: 1.0秒）
  - `--community` フラグで再インデックス後にコミュニティ検出を実行
  - 対応言語ファイルのみをフィルタリング
  - Ctrl+Cでの正常シャットダウン

#### GitHub Actions CI/CD
- **CIワークフロー** (`.github/workflows/ci.yml`):
  - mainブランチへのpush/PRで実行
  - Python 3.11と3.12でテスト
  - ruffによるリンティング、mypyによる型チェック
  - Codecovへのカバレッジレポート
  - ビルド検証
- **リリースワークフロー** (`.github/workflows/release.yml`):
  - バージョンタグ（v*）でトリガー
  - リリース前にテストを実行
  - アーティファクト付きでGitHubリリースを作成
  - PyPIへの自動公開

### テスト
- watchコマンド用に8つの新しいCLIテストを追加
- 合計: 308 passed, 1 skipped

---

## [0.6.2] - 2025-11-27

### 追加

#### エンティティID部分一致
- **`resolve_entity_id()`**: 部分的なエンティティIDを完全なIDに解決
  - 完全一致、名前一致、qualified_name接尾辞一致
  - `file::name` パターンサポート（例: `linux.rs::hashmap_random_keys`）
- **`search_entities()`**: パターンベースのエンティティ検索
- `find_callers()`, `find_callees()`, `find_dependencies()` での部分IDサポート

#### 自動コミュニティ検出
- **`--community` フラグ**（デフォルト）: インデックス後に自動でコミュニティ検出
- **`--no-community` フラグ**: 大規模リポジトリ向けにコミュニティ検出をスキップ
- インデックス結果にコミュニティ数とモジュラリティを表示

#### query_codebaseの強化
- **関連性スコアリング**: 完全一致 (1.0), 前方一致 (0.8), 部分一致 (0.6)
- **`include_related`**: 関連エンティティを結果に含める
- **`include_community`**: コミュニティ情報を含める
- **`entity_types` フィルタ**: function, class, methodなどでフィルタリング
- JSON出力にscoreとcommunity_idを含める

#### 増分コミュニティ更新
- **`update_incremental()`**: 変更されたエンティティを最適なコミュニティに再割り当て
- 20%の変更閾値で完全再検出をトリガー
- 変更追跡用の `IndexResult.changed_entity_ids`

### 変更

#### コミュニティ検出パフォーマンス
- **バッチグラフ構築**: 高速化のため `add_nodes_from()` / `add_edges_from()` を使用
- **バッチDB書き込み**: コミュニティ保存に `executemany()` を使用
- **大規模グラフサンプリング**: 次数ベースサンプリングで `max_nodes=50000`
- 230K以上のエンティティを持つリポジトリの処理に成功

### テスト
- スコアリングとコミュニティ統合用に6つの新しいテストを追加
- 合計: 300 passed, 1 skipped

---

## [0.6.1] - 2025-11-27

### 修正

#### SSEトランスポート
- `/messages/` 用に `Route` の代わりに `Mount` を使用してSSEエンドポイント設定を修正
- クライアント切断時のNoneTypeエラーを回避するため適切な `Response()` を返すように修正
- 公式MCP SSE実装パターンに準拠

#### CLI Unicode互換性
- 一部のターミナルでエンコーディングエラーを引き起こすUnicode絵文字文字を削除
- サロゲートエンコーディング問題を回避するため `SpinnerColumn` を削除
- より広い互換性のためRichコンソールに `legacy_windows=True` を追加

### テスト済み
- Rustコンパイラリポジトリ（230K以上のエンティティ、34K以上のファイル）のインデックス作成に成功
- SSEトランスポート経由で14のMCPツールすべての動作を確認

---

## [0.6.0] - 2025-11-27

### 追加

#### バックグラウンドサーバー管理
- **`codegraph-mcp start`**: MCPサーバーをバックグラウンド（デーモンモード）で起動
  - デフォルトでポート8080のSSEトランスポート
  - PIDファイルは `~/.codegraph/server.pid` に保存
  - ログは `~/.codegraph/server.log` に出力
- **`codegraph-mcp stop`**: バックグラウンドMCPサーバーを正常停止
- **`codegraph-mcp status`**: 最新のログ出力とともにサーバーステータスを確認

### 変更
- `codegraph-mcp serve` をフォアグラウンドモードとして明示的にドキュメント化
- バックグラウンドモードはデフォルトでSSEトランスポートを使用（フォアグラウンドはstdio）

---

## [0.5.0] - 2025-11-27

### 変更

#### パフォーマンス最適化 - バッチデータベース書き込み
- **47倍高速なインデックス作成**: エンティティとリレーションのバッチ書き込み操作を実装
  - 変更前: 67ファイルで29.47秒（32 エンティティ/秒）
  - 変更後: 67ファイルで0.63秒（1495 エンティティ/秒）
- リポジトリあたりのデータベースコミットを約5700から3に削減
- GraphEngineに `add_entities_batch()` と `add_relations_batch()` メソッドを追加
- バッチ書き込み前にすべての解析結果を収集するようIndexerを更新

#### 技術詳細
- バルク挿入にSQLite `executemany()` を使用
- エンティティ/リレーションごとではなくバッチごとに単一コミット
- バッチファイル追跡更新

---

## [0.4.0] - 2025-11-27

### 追加

#### CLI強化
- **Richプログレス表示**: `codegraph-mcp index` コマンドにアニメーション付きプログレスバーを追加
  - リアルタイムプログレスバー付きスピナーアニメーション
  - ファイルごとの処理表示
  - エンティティ/リレーション数と所要時間を含む結果テーブル
  - 色分けされたステータスメッセージ

#### パフォーマンス測定値（実測）
- インデックス速度: **32 エンティティ/秒**
- ファイル処理: **0.44 秒/ファイル**
- 増分インデックス: **< 2秒**
- クエリレスポンス: **< 2ms**

### 変更
- CLIプログレス表示用に `rich>=13.0.0` 依存関係を追加
- `Indexer.index_repository()` にオプションの `progress_callback` パラメータを追加

---

## [0.3.0] - 2025-11-27

### 追加

#### 言語サポート - 5つの新言語
- **PHP言語サポート**: PHPソースファイルの完全なAST解析
  - クラス、インターフェース、トレイトの抽出
  - メソッドと関数の抽出
  - 名前空間処理
  - 継承とimplements関係の検出

- **C#言語サポート**: 包括的なC#解析
  - クラス、構造体、インターフェース、列挙型の抽出
  - メソッド、コンストラクタ、プロパティの抽出
  - 名前空間処理
  - 継承関係の検出
  - usingディレクティブの処理

- **C++言語サポート**: 完全なC++解析
  - クラスと構造体の抽出
  - 関数とメソッドの抽出（ヘッダー宣言を含む）
  - 名前空間処理
  - includeディレクティブの処理
  - 継承関係の検出
  - テンプレートクラスのサポート

- **HCL (Terraform) 言語サポート**: Infrastructure as Code解析
  - リソースとデータソースの抽出
  - 変数と出力の抽出
  - モジュールとlocalsブロックの抽出
  - プロバイダーブロックの抽出

- **Ruby言語サポート**: 完全なRuby解析
  - クラスとモジュールの抽出
  - メソッドとシングルトンメソッドの抽出
  - 継承関係の検出
  - require/require_relativeの処理
  - モジュールinclude/extendの検出

### 変更
- `tree-sitter-php`, `tree-sitter-c-sharp`, `tree-sitter-cpp`, `tree-sitter-hcl`, `tree-sitter-ruby` を含むように依存関係を更新
- 5つの新しいエクストラクタで言語レジストリを拡張

### テスト
- PHP、C#、C++、HCL、Rubyパーサー用に73の新しいテストを追加
- テスト合計: 286（v0.2.0の212から増加）

---

## [0.2.0] - 2025-11-27

### 追加

#### 言語サポート
- **Go言語サポート**: Goソースファイルの完全なAST解析
  - レシーバー型を含む関数とメソッドの抽出
  - 構造体とインターフェースの抽出
  - パッケージとインポートの処理
  - 呼び出し関係の検出

- **Java言語サポート**: 包括的なJava解析
  - クラス、インターフェース、列挙型の抽出
  - メソッドとコンストラクタの抽出
  - 継承（extends/implements）関係の検出
  - importステートメントの処理

### 変更
- `tree-sitter-go` と `tree-sitter-java` を含むように依存関係を更新
- GoとJavaエクストラクタで言語レジストリを拡張

### テスト
- GoとJavaパーサー用に30の新しいテストを追加
- テスト合計: 212（v0.1.0の182から増加）

---

## [0.1.0] - 2025-11-26

### 追加

#### コア機能
- **AST解析**: Tree-sitterベースの多言語コード分析
  - クラス/関数/メソッド抽出を含むPythonサポート
  - インターフェースと型エイリアス処理を含むTypeScriptサポート
  - JavaScriptサポート（ES6+、JSX、CommonJS、ESM）
  - struct/enum/trait/impl抽出を含むRustサポート

- **コードグラフエンジン**: NetworkXベースのグラフ構築
  - エンティティ抽出（クラス、関数、メソッド、モジュール）
  - 関係検出（calls、contains、imports、implements、extends）
  - 設定可能な深度での依存関係分析

- **GraphRAG統合**: グラフベースの検索拡張生成
  - Louvainアルゴリズムを使用したコミュニティ検出
  - すべてのコードコミュニティにわたるグローバル検索
  - エンティティ近傍内のローカル検索
  - LLM統合（OpenAI、Anthropic、Ollama、ルールベース）

- **ストレージ層**: SQLiteベースの永続化
  - aiosqliteによる非同期データベース操作
  - パフォーマンス向上のためのファイルベースキャッシング
  - セマンティック検索用のベクトルストレージ

#### MCPインターフェース
- **14のMCPツール**:
  - グラフクエリ: `query_codebase`, `find_dependencies`, `find_callers`, `find_callees`, `find_implementations`, `analyze_module_structure`
  - コード取得: `get_code_snippet`, `read_file_content`, `get_file_structure`
  - GraphRAG: `global_search`, `local_search`
  - 管理: `suggest_refactoring`, `reindex_repository`, `execute_shell_command`

- **4つのMCPリソース**:
  - `codegraph://entities/{id}` - エンティティ詳細
  - `codegraph://files/{path}` - ファイルグラフ情報
  - `codegraph://communities/{id}` - コミュニティデータ
  - `codegraph://stats` - グラフ統計

- **6つのMCPプロンプト**:
  - `code_review` - コードレビュー支援
  - `explain_codebase` - コードベース説明
  - `implement_feature` - 機能実装ガイド
  - `debug_issue` - デバッグ支援
  - `refactor_guidance` - リファクタリング提案
  - `test_generation` - テスト生成ヘルプ

#### トランスポートプロトコル
- 標準MCPクライアント用のstdioトランスポート（デフォルト）
- HTTPベース統合用のSSEトランスポート

#### CLIコマンド
- `codegraph-mcp serve` - MCPサーバーを起動
- `codegraph-mcp index` - リポジトリをインデックス
- `codegraph-mcp query` - コードエンティティを検索
- `codegraph-mcp stats` - グラフ統計を表示

#### ドキュメント
- 包括的なAPIリファレンス（`docs/api.md`）
- 設定ガイド（`docs/configuration.md`）
- 使用例（`docs/examples.md`）
- `examples/` ディレクトリのサンプルスクリプト

### パフォーマンス
- 初期インデックス: 21秒で約700エンティティ
- クエリレスポンス: 平均2ms未満
- 増分インデックス: 2秒未満

### テスト
- 182のユニットテストと統合テスト
- 80%以上のコードカバレッジ目標
- pytest-asyncioによる非同期テストサポート

### サポートプラットフォーム
- Python 3.11+
- Linux、macOS、Windows
- MCPクライアント: Claude Desktop、VS Code、Cursor、Windsurf

---

## [未リリース]

### 計画中
- 100k行以上のリポジトリ向けパフォーマンス最適化
- MkDocsドキュメントサイト
- グラフ可視化用Web UI

---

[0.7.1]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.7.1
[0.7.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.7.0
[0.6.2]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.6.2
[0.6.1]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.6.1
[0.6.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.6.0
[0.5.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.5.0
[0.4.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.4.0
[0.3.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.3.0
[0.2.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.2.0
[0.1.0]: https://github.com/nahisaho/CodeGraphMCPServer/releases/tag/v0.1.0
[未リリース]: https://github.com/nahisaho/CodeGraphMCPServer/compare/v0.7.1...HEAD
