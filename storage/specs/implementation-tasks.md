# 実装タスク仕様書

**Project**: CodeGraph MCP Server
**Version**: 1.0.0
**Created**: 2025-11-26
**Status**: Ready for Implementation
**Based On**: project-plan.md, design-*.md, requirements-specification.md

---

## 概要

このドキュメントは、CodeGraph MCP Serverの実装タスクを詳細に定義します。
各タスクは要件ID、設計コンポーネント、受け入れ基準を明示し、Article V（トレーサビリティ）に準拠しています。

---

## Phase 1: Core Foundation (Week 1-2)

### Sprint 1.1: プロジェクト基盤 & ASTパーサー (Week 1)

#### TASK-001: プロジェクト構造セットアップ

| 項目 | 内容 |
|------|------|
| **見積り** | 4h |
| **優先度** | P0 (Blocker) |
| **依存** | なし |
| **担当** | Dev |

**説明**:
プロジェクトのディレクトリ構造を`steering/structure.md`に従って作成する。

**成果物**:
```
src/codegraph_mcp/
├── __init__.py
├── __main__.py
├── server.py
├── config.py
├── core/
│   ├── __init__.py
│   ├── parser.py
│   ├── graph.py
│   ├── indexer.py
│   ├── community.py
│   └── semantic.py
├── storage/
│   ├── __init__.py
│   ├── sqlite.py
│   ├── cache.py
│   └── vectors.py
├── mcp/
│   ├── __init__.py
│   ├── tools.py
│   ├── resources.py
│   └── prompts.py
├── languages/
│   ├── __init__.py
│   ├── config.py
│   ├── python.py
│   ├── typescript.py
│   └── rust.py
└── utils/
    ├── __init__.py
    ├── git.py
    └── logging.py
tests/
├── unit/
├── integration/
├── e2e/
└── fixtures/
```

**受け入れ基準**:
- [ ] ディレクトリ構造が`steering/structure.md`と一致
- [ ] 各`__init__.py`が適切なエクスポートを定義
- [ ] Article I（Library-First）準拠

---

#### TASK-002: pyproject.toml設定

| 項目 | 内容 |
|------|------|
| **見積り** | 2h |
| **優先度** | P0 |
| **依存** | TASK-001 |
| **要件ID** | REQ-CLI-004 |

**説明**:
`steering/tech.md`に記載された依存関係を含むpyproject.tomlを作成する。

**成果物**:
- `pyproject.toml`（依存関係、スクリプト、ビルド設定）

**受け入れ基準**:
- [ ] `pip install -e .` が成功
- [ ] `codegraph-mcp --help` が動作
- [ ] 依存関係が`steering/tech.md`と一致

---

#### TASK-003: CI/CDパイプライン設定

| 項目 | 内容 |
|------|------|
| **見積り** | 4h |
| **優先度** | P1 |
| **依存** | TASK-002 |

**説明**:
GitHub Actionsでテスト、lint、型チェックを自動実行する。

**成果物**:
- `.github/workflows/ci.yml`

**受け入れ基準**:
- [ ] PRで自動テスト実行
- [ ] ruff lintパス
- [ ] mypy型チェックパス
- [ ] カバレッジレポート生成

---

#### TASK-004: Python ASTパーサー実装

| 項目 | 内容 |
|------|------|
| **見積り** | 8h |
| **優先度** | P0 |
| **依存** | TASK-001 |
| **要件ID** | REQ-AST-001, REQ-AST-004 |
| **設計参照** | design-core-engine.md §2.1 |

**説明**:
Tree-sitterを使用してPythonファイルを解析し、エンティティ（関数、クラス、インポート）と関係（呼び出し、インポート、継承）を抽出する。

**インターフェース**:
```python
class ASTParser:
    def parse_file(self, file_path: Path) -> ParseResult:
        """ファイルを解析してエンティティと関係を抽出"""
        
    def detect_language(self, file_path: Path) -> str | None:
        """拡張子から言語を自動検出"""

@dataclass
class ParseResult:
    entities: list[Entity]
    relations: list[Relation]
    errors: list[ParseError]
```

**抽出対象（Python）**:
| Tree-sitterノード | エンティティタイプ |
|-------------------|-------------------|
| function_definition | FUNCTION |
| class_definition | CLASS |
| import_statement | - (関係のみ) |
| import_from_statement | - (関係のみ) |
| call | - (関係のみ) |

**受け入れ基準**:
- [ ] Python関数定義を抽出
- [ ] Pythonクラス定義を抽出
- [ ] インポート関係を抽出
- [ ] 関数呼び出し関係を抽出
- [ ] 継承関係を抽出
- [ ] テストカバレッジ80%以上

---

#### TASK-005: TypeScript ASTパーサー実装

| 項目 | 内容 |
|------|------|
| **見積り** | 8h |
| **優先度** | P0 |
| **依存** | TASK-004 |
| **要件ID** | REQ-AST-002, REQ-AST-004 |
| **設計参照** | design-core-engine.md §2.1 |

**説明**:
Tree-sitterを使用してTypeScriptファイルを解析する。

**抽出対象（TypeScript）**:
| Tree-sitterノード | エンティティタイプ |
|-------------------|-------------------|
| function_declaration | FUNCTION |
| arrow_function | FUNCTION |
| method_definition | METHOD |
| class_declaration | CLASS |
| interface_declaration | INTERFACE |
| import_statement | - (関係のみ) |
| call_expression | - (関係のみ) |

**受け入れ基準**:
- [ ] TypeScript関数宣言・アロー関数を抽出
- [ ] クラス・インターフェース宣言を抽出
- [ ] インポート関係を抽出
- [ ] 呼び出し関係を抽出
- [ ] implements関係を抽出
- [ ] .ts, .tsx両方に対応

---

#### TASK-006: パーサーユニットテスト

| 項目 | 内容 |
|------|------|
| **見積り** | 4h |
| **優先度** | P0 |
| **依存** | TASK-004, TASK-005 |
| **要件ID** | REQ-AST-005 |
| **Article** | III (Test-First) |

**説明**:
パーサーのユニットテストを作成。構文エラーを含むファイルの処理も検証する。

**テストケース**:
1. 正常なPythonファイルのパース
2. 正常なTypeScriptファイルのパース
3. 構文エラーを含むファイル（部分パース検証）
4. 空ファイル
5. ネストしたクラス・関数
6. デコレータ付き関数

**受け入れ基準**:
- [ ] 全テストケースがパス
- [ ] 構文エラー時にログ記録
- [ ] 部分パースが動作
- [ ] カバレッジ80%以上

---

### Sprint 1.2: グラフエンジン & ストレージ (Week 2)

#### TASK-007: SQLiteスキーマ設計・実装

| 項目 | 内容 |
|------|------|
| **見積り** | 6h |
| **優先度** | P0 |
| **依存** | TASK-001 |
| **要件ID** | REQ-GRF-005, REQ-GRF-006, REQ-STR-001 |
| **設計参照** | design-storage.md §2 |

**説明**:
`design-storage.md`のスキーマを実装する。

**成果物**:
```python
class SQLiteStorage:
    async def initialize(self) -> None:
        """スキーマ作成・マイグレーション"""
        
    async def close(self) -> None:
        """接続クローズ"""
```

**スキーマ**:
```sql
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    type TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    metadata TEXT,
    FOREIGN KEY (source_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES entities(id) ON DELETE CASCADE
);

CREATE TABLE communities (
    id INTEGER PRIMARY KEY,
    level INTEGER NOT NULL,
    name TEXT,
    summary TEXT,
    member_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_entities_file ON entities(file_path);
CREATE INDEX idx_entities_community ON entities(community_id);
CREATE INDEX idx_relations_source ON relations(source_id);
CREATE INDEX idx_relations_target ON relations(target_id);
CREATE INDEX idx_relations_type ON relations(type);
```

**受け入れ基準**:
- [ ] スキーマ作成成功
- [ ] インデックス作成成功
- [ ] 非同期I/O対応（aiosqlite）
- [ ] マイグレーション対応

---

#### TASK-008: エンティティCRUD実装

| 項目 | 内容 |
|------|------|
| **見積り** | 4h |
| **優先度** | P0 |
| **依存** | TASK-007 |
| **要件ID** | REQ-GRF-001, REQ-GRF-003 |

**インターフェース**:
```python
class SQLiteStorage:
    async def add_entity(self, entity: Entity) -> str:
        """エンティティ追加、IDを返す"""
        
    async def get_entity(self, entity_id: str) -> Entity | None:
        """IDでエンティティ取得"""
        
    async def update_entity(self, entity: Entity) -> bool:
        """エンティティ更新"""
        
    async def delete_entity(self, entity_id: str) -> bool:
        """エンティティ削除（カスケード）"""
        
    async def find_entities(
        self,
        type: EntityType | None = None,
        file_path: str | None = None,
        name_pattern: str | None = None,
    ) -> list[Entity]:
        """条件検索"""
```

**受け入れ基準**:
- [ ] CRUD操作が動作
- [ ] バッチ挿入対応（1000件/バッチ）
- [ ] 検索クエリが動作

---

#### TASK-009: 関係CRUD実装

| 項目 | 内容 |
|------|------|
| **見積り** | 4h |
| **優先度** | P0 |
| **依存** | TASK-008 |
| **要件ID** | REQ-GRF-002, REQ-GRF-004 |

**インターフェース**:
```python
class SQLiteStorage:
    async def add_relation(self, relation: Relation) -> int:
        """関係追加、IDを返す"""
        
    async def get_relations(
        self,
        source_id: str | None = None,
        target_id: str | None = None,
        type: RelationType | None = None,
    ) -> list[Relation]:
        """条件検索"""
        
    async def delete_relations(
        self,
        source_id: str | None = None,
        target_id: str | None = None,
    ) -> int:
        """関係削除、削除件数を返す"""
```

**受け入れ基準**:
- [ ] 関係の追加・取得・削除が動作
- [ ] エンティティ削除時のカスケード削除

---

#### TASK-010: グラフクエリ実装

| 項目 | 内容 |
|------|------|
| **見積り** | 6h |
| **優先度** | P0 |
| **依存** | TASK-009 |
| **要件ID** | REQ-GRF-006 |
| **設計参照** | design-core-engine.md §2.2 |

**説明**:
NetworkXを使用してグラフ操作を実装する。

**インターフェース**:
```python
class GraphEngine:
    def __init__(self, storage: SQLiteStorage):
        self._storage = storage
        self._graph: nx.DiGraph | None = None
        
    async def load_graph(self) -> None:
        """DBからグラフをメモリにロード"""
        
    def find_callers(
        self,
        entity_id: str,
        max_depth: int = 3,
    ) -> list[CallPath]:
        """呼び出し元を検索"""
        
    def find_callees(
        self,
        entity_id: str,
        max_depth: int = 3,
    ) -> list[CallPath]:
        """呼び出し先を検索"""
        
    def find_dependencies(
        self,
        entity_id: str,
        direction: Literal["upstream", "downstream", "both"],
        depth: int = 3,
    ) -> DependencyGraph:
        """依存関係グラフを取得"""
        
    def get_shortest_path(
        self,
        source_id: str,
        target_id: str,
    ) -> list[str] | None:
        """最短パスを取得"""
```

**受け入れ基準**:
- [ ] 呼び出し元/先の検索が動作
- [ ] 依存関係グラフ取得が動作
- [ ] 深さ制限が機能
- [ ] 循環参照を適切に処理

---

#### TASK-011: ファイルキャッシュ実装

| 項目 | 内容 |
|------|------|
| **見積り** | 4h |
| **優先度** | P1 |
| **依存** | TASK-007 |
| **要件ID** | REQ-STR-002 |
| **設計参照** | design-storage.md §3 |

**説明**:
ASTパース結果をキャッシュし、ファイル変更時のみ再パースする。

**インターフェース**:
```python
class CacheManager:
    def __init__(self, max_size: int = 500):
        self._ast_cache: dict[str, ParseResult] = {}
        
    def get_cached_ast(self, file_path: Path) -> ParseResult | None:
        """キャッシュからAST取得（ファイルハッシュ検証）"""
        
    def cache_ast(self, file_path: Path, result: ParseResult) -> None:
        """ASTをキャッシュに保存"""
        
    def invalidate(self, file_path: Path) -> None:
        """キャッシュ無効化"""
        
    def clear(self) -> None:
        """全キャッシュクリア"""
```

**受け入れ基準**:
- [ ] ファイルハッシュベースのキャッシュ検証
- [ ] LRU eviction（500件上限）
- [ ] キャッシュヒット時の再パース回避

---

#### TASK-012: インデクサー基盤実装

| 項目 | 内容 |
|------|------|
| **見積り** | 6h |
| **優先度** | P0 |
| **依存** | TASK-004, TASK-010, TASK-011 |
| **要件ID** | REQ-IDX-001, REQ-IDX-004 |
| **設計参照** | design-core-engine.md §2.3 |

**説明**:
リポジトリ全体をスキャンし、インデックスを構築する。

**インターフェース**:
```python
class Indexer:
    def __init__(
        self,
        parser: ASTParser,
        storage: SQLiteStorage,
        graph: GraphEngine,
        cache: CacheManager,
    ):
        ...
        
    async def index_repository(
        self,
        repo_path: Path,
        incremental: bool = True,
    ) -> IndexResult:
        """リポジトリをインデックス"""
        
    def list_indexable_files(self, repo_path: Path) -> list[Path]:
        """.gitignore準拠でファイル一覧取得"""

@dataclass
class IndexResult:
    total_files: int
    indexed_files: int
    skipped_files: int
    entities_count: int
    relations_count: int
    errors: list[IndexError]
    duration_seconds: float
```

**受け入れ基準**:
- [ ] リポジトリ全体のインデックスが動作
- [ ] .gitignore準拠
- [ ] 進捗ログ出力
- [ ] エラー時も継続処理

---

#### TASK-013: 増分インデックス実装

| 項目 | 内容 |
|------|------|
| **見積り** | 6h |
| **優先度** | P0 |
| **依存** | TASK-012 |
| **要件ID** | REQ-IDX-002, REQ-STR-004 |

**説明**:
Git差分を使用して変更ファイルのみを再インデックスする。

**インターフェース**:
```python
class Indexer:
    async def get_changed_files(self, repo_path: Path) -> list[Path]:
        """Git差分から変更ファイルを取得"""
        
    async def index_incremental(self, repo_path: Path) -> IndexResult:
        """増分インデックス"""
```

**受け入れ基準**:
- [ ] Git差分検出が動作
- [ ] 変更ファイルのみ再インデックス
- [ ] 削除ファイルのエンティティ削除
- [ ] 2秒以内で完了（目標）

---

#### TASK-014: グラフエンジンテスト

| 項目 | 内容 |
|------|------|
| **見積り** | 4h |
| **優先度** | P0 |
| **依存** | TASK-010, TASK-013 |
| **Article** | III, IX |

**説明**:
グラフエンジンとストレージの統合テスト。実際のSQLiteを使用する（Article IX準拠）。

**テストケース**:
1. エンティティCRUD
2. 関係CRUD
3. 呼び出し元/先検索
4. 依存関係グラフ
5. 増分インデックス
6. パフォーマンステスト（1000エンティティ）

**受け入れ基準**:
- [ ] 全テストパス
- [ ] 実DB使用（モックなし）
- [ ] カバレッジ80%以上

---

## Phase 2: MCP Integration (Week 3-4)

### Sprint 2.1: MCPサーバー基盤 & 基本ツール (Week 3)

#### TASK-015: MCPサーバー基盤実装

| 項目 | 内容 |
|------|------|
| **見積り** | 8h |
| **優先度** | P0 |
| **依存** | TASK-012 |
| **要件ID** | REQ-TRP-001, REQ-TRP-004 |
| **設計参照** | design-mcp-interface.md §1 |

**説明**:
MCP SDKを使用してサーバー基盤を実装する。

**インターフェース**:
```python
class CodeGraphServer:
    def __init__(self, config: ServerConfig):
        self._server = Server("codegraph")
        self._indexer: Indexer | None = None
        self._graph: GraphEngine | None = None
        
    async def initialize(self, repo_path: Path) -> None:
        """サーバー初期化、インデックス読み込み"""
        
    async def run(self) -> None:
        """サーバー起動"""
```

**受け入れ基準**:
- [ ] stdio トランスポート動作
- [ ] 初期化時にインデックス読み込み
- [ ] 正常終了処理

---

#### TASK-016〜021: グラフクエリツール実装

各ツールの詳細は `design-mcp-interface.md §2.1` を参照。

| タスクID | ツール名 | 要件ID | 見積り |
|----------|----------|--------|--------|
| TASK-016 | query_codebase | REQ-TLS-001 | 4h |
| TASK-017 | find_dependencies | REQ-TLS-002 | 4h |
| TASK-018 | find_callers | REQ-TLS-003 | 4h |
| TASK-019 | find_callees | REQ-TLS-004 | 4h |
| TASK-020 | find_implementations | REQ-TLS-005 | 4h |
| TASK-021 | analyze_module_structure | REQ-TLS-006 | 4h |

**共通受け入れ基準**:
- [ ] MCP Tool仕様準拠
- [ ] エラーハンドリング
- [ ] ユニットテスト

---

#### TASK-022: グラフクエリツールテスト

| 項目 | 内容 |
|------|------|
| **見積り** | 4h |
| **優先度** | P0 |
| **依存** | TASK-016〜021 |

**受け入れ基準**:
- [ ] 全ツールの動作確認
- [ ] エッジケース（存在しないエンティティ等）
- [ ] カバレッジ80%以上

---

### Sprint 2.2: コード取得ツール & リソース & CLI (Week 4)

#### TASK-023〜026: 追加ツール実装

| タスクID | ツール名 | 要件ID | 見積り |
|----------|----------|--------|--------|
| TASK-023 | get_code_snippet | REQ-TLS-007 | 3h |
| TASK-024 | read_file_content | REQ-TLS-008 | 2h |
| TASK-025 | get_file_structure | REQ-TLS-009 | 3h |
| TASK-026 | reindex_repository | REQ-TLS-013 | 3h |

---

#### TASK-027〜029: リソース実装

| タスクID | リソース | 要件ID | 見積り |
|----------|----------|--------|--------|
| TASK-027 | codegraph://entities/{id} | REQ-RSC-001 | 2h |
| TASK-028 | codegraph://files/{path} | REQ-RSC-002 | 2h |
| TASK-029 | codegraph://stats | REQ-RSC-004 | 2h |

---

#### TASK-030: CLI serveコマンド

| 項目 | 内容 |
|------|------|
| **見積り** | 4h |
| **優先度** | P0 |
| **依存** | TASK-015 |
| **要件ID** | REQ-CLI-001, REQ-CLI-002 |

**コマンド仕様**:
```bash
codegraph-mcp serve [OPTIONS]

Options:
  --repo PATH      リポジトリパス（デフォルト: カレントディレクトリ）
  --port INT       ポート番号（SSE用、デフォルト: 3000）
  --transport STR  トランスポート（stdio|sse、デフォルト: stdio）
  --verbose        詳細ログ出力
```

**受け入れ基準**:
- [ ] `codegraph-mcp serve` で起動
- [ ] `--repo` オプション動作
- [ ] Ctrl+Cで正常終了

---

#### TASK-031: CLI helpコマンド

| 項目 | 内容 |
|------|------|
| **見積り** | 2h |
| **要件ID** | REQ-CLI-003 |

**受け入れ基準**:
- [ ] `codegraph-mcp --help` で使用方法表示
- [ ] 各コマンドの `--help` 対応

---

#### TASK-032: パッケージング設定

| 項目 | 内容 |
|------|------|
| **見積り** | 2h |
| **要件ID** | REQ-CLI-004 |

**受け入れ基準**:
- [ ] `pip install codegraph-mcp` が動作
- [ ] 必要な依存関係が含まれる
- [ ] エントリーポイント設定正確

---

#### TASK-033: E2Eテスト（Claude Desktop）

| 項目 | 内容 |
|------|------|
| **見積り** | 4h |
| **依存** | TASK-030 |
| **要件ID** | REQ-NFR-011 |

**テスト内容**:
1. Claude Desktop設定ファイル作成
2. サーバー起動確認
3. ツール呼び出し確認
4. リソースアクセス確認

**受け入れ基準**:
- [ ] Claude Desktopで動作確認
- [ ] 設定例ドキュメント作成

---

#### TASK-034: パフォーマンステスト

| 項目 | 内容 |
|------|------|
| **見積り** | 4h |
| **依存** | TASK-032 |
| **要件ID** | REQ-NFR-001〜004 |

**テスト対象**:
| メトリクス | 目標 | テスト方法 |
|-----------|------|-----------|
| 初回インデックス | <30秒/10万行 | サンプルリポジトリ |
| 増分インデックス | <2秒 | 1ファイル変更 |
| クエリ応答 | <500ms | 各ツール |
| 起動時間 | <2秒 | サーバー起動 |

**受け入れ基準**:
- [ ] 全パフォーマンス目標達成
- [ ] ベンチマーク結果記録

---

## Phase 3: GraphRAG Features (Week 5-6)

### Sprint 3.1: コミュニティ検出 & セマンティック分析 (Week 5)

#### TASK-035: コミュニティ検出アルゴリズム

| 項目 | 内容 |
|------|------|
| **見積り** | 8h |
| **優先度** | P1 |
| **要件ID** | REQ-SEM-003, REQ-SEM-004 |
| **設計参照** | design-core-engine.md §2.4 |

**説明**:
NetworkXのLouvainアルゴリズムでコミュニティ検出を実装する。

**インターフェース**:
```python
class CommunityDetector:
    def detect_communities(
        self,
        graph: nx.DiGraph,
        resolution: float = 1.0,
    ) -> dict[int, list[str]]:
        """コミュニティ検出、{community_id: [entity_ids]}を返す"""
        
    def build_hierarchy(
        self,
        communities: dict[int, list[str]],
        levels: int = 2,
    ) -> list[Community]:
        """階層コミュニティ構築"""
```

**受け入れ基準**:
- [ ] Louvain法でコミュニティ検出
- [ ] 階層レベル対応（0=細粒度、1=粗粒度）
- [ ] コミュニティIDをエンティティに割り当て

---

#### TASK-036〜038: LLM統合 & サマリー生成

| タスクID | 内容 | 要件ID | 見積り |
|----------|------|--------|--------|
| TASK-036 | LLM統合基盤 | REQ-SEM-001 | 6h |
| TASK-037 | エンティティ説明生成 | REQ-SEM-001 | 4h |
| TASK-038 | コミュニティサマリー生成 | REQ-SEM-002 | 4h |

---

#### TASK-039: ベクトルストア実装

| 項目 | 内容 |
|------|------|
| **見積り** | 6h |
| **要件ID** | REQ-STR-003 |
| **設計参照** | design-storage.md §4 |

**受け入れ基準**:
- [ ] エンベディング格納
- [ ] コサイン類似度検索
- [ ] numpy使用（外部DB不要）

---

### Sprint 3.2: GraphRAGツール & プロンプト (Week 6)

#### TASK-042〜043: GraphRAGツール

| タスクID | ツール | 要件ID | 見積り |
|----------|--------|--------|--------|
| TASK-042 | global_search | REQ-TLS-010 | 6h |
| TASK-043 | local_search | REQ-TLS-011 | 6h |

---

#### TASK-045〜049: プロンプトテンプレート

| タスクID | プロンプト | 要件ID | 見積り |
|----------|-----------|--------|--------|
| TASK-045 | code_review | REQ-PRM-001 | 2h |
| TASK-046 | explain_codebase | REQ-PRM-002 | 2h |
| TASK-047 | implement_feature | REQ-PRM-003 | 2h |
| TASK-048 | debug_issue | REQ-PRM-004 | 2h |
| TASK-049 | test_generation | REQ-PRM-006 | 2h |

---

## Phase 4: Polish & Extensions (Week 7-8)

### Sprint 4.1: 追加言語 & 拡張機能 (Week 7)

| タスクID | 内容 | 要件ID | 見積り |
|----------|------|--------|--------|
| TASK-051 | Rust ASTパーサー | REQ-AST-003 | 8h |
| TASK-052 | JavaScript ASTパーサー | - | 6h |
| TASK-053 | SSEトランスポート | REQ-TRP-002 | 6h |
| TASK-054 | suggest_refactoring | REQ-TLS-012 | 6h |

### Sprint 4.2: ドキュメント & リリース (Week 8)

| タスクID | 内容 | 見積り |
|----------|------|--------|
| TASK-057 | README.md | 4h |
| TASK-058 | APIドキュメント | 4h |
| TASK-059 | 使用例ドキュメント | 4h |
| TASK-060 | Claude Desktop設定例 | 2h |
| TASK-061 | パフォーマンス最適化 | 8h |
| TASK-062 | 最終統合テスト | 4h |
| TASK-063 | PyPIリリース準備 | 4h |
| TASK-064 | リリースノート | 2h |

---

## タスク依存関係図

```
TASK-001 ─┬─ TASK-002 ─ TASK-003
          │
          ├─ TASK-004 ─┬─ TASK-005 ─ TASK-006
          │            │
          │            └─ TASK-012 ─ TASK-013 ─ TASK-014
          │                   │
          └─ TASK-007 ─ TASK-008 ─ TASK-009 ─ TASK-010 ─┘
                                                          │
                                                          └─ TASK-015 ─┬─ TASK-016~021 ─ TASK-022
                                                                       │
                                                                       ├─ TASK-023~029
                                                                       │
                                                                       └─ TASK-030~034 (MVP)
                                                                                │
                                                                                └─ TASK-035~050 (GraphRAG)
                                                                                        │
                                                                                        └─ TASK-051~064 (Polish)
```

---

## トレーサビリティマトリクス

| タスクID | 要件ID | 設計参照 | テスト |
|----------|--------|----------|--------|
| TASK-004 | REQ-AST-001, 004 | design-core-engine §2.1 | TASK-006 |
| TASK-005 | REQ-AST-002, 004 | design-core-engine §2.1 | TASK-006 |
| TASK-007 | REQ-GRF-005, 006, STR-001 | design-storage §2 | TASK-014 |
| TASK-010 | REQ-GRF-006 | design-core-engine §2.2 | TASK-014 |
| TASK-012 | REQ-IDX-001, 004 | design-core-engine §2.3 | TASK-014 |
| TASK-015 | REQ-TRP-001, 004 | design-mcp-interface §1 | TASK-033 |
| TASK-016 | REQ-TLS-001 | design-mcp-interface §2.1 | TASK-022 |
| TASK-035 | REQ-SEM-003, 004 | design-core-engine §2.4 | TASK-041 |

---

## 変更履歴

| バージョン | 日付 | 変更内容 |
|-----------|------|----------|
| 1.0.0 | 2025-11-26 | 初版作成 |

---

**Document Status**: Ready for Implementation
**Constitutional Compliance**: Article III (Test-First) ✓, Article V (Traceability) ✓
