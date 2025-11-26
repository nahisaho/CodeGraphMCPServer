# CodeGraph MCP Server コアエンジン詳細設計書

**Project**: CodeGraph MCP Server  
**Version**: 1.0.0  
**Created**: 2025-11-26  
**Status**: Draft  
**Document Type**: C4 Model - Component Diagram (Level 3)

---

## 1. ドキュメント概要

### 1.1 目的

本ドキュメントは、CodeGraph MCP Serverのコアエンジン層の詳細設計をC4 Component Diagramとして記述します。

### 1.2 スコープ

- ASTパーサー設計
- グラフエンジン設計
- セマンティックアナライザー設計
- インデクサー設計

### 1.3 対象要件

| 要件グループ | 要件ID | 説明 |
|-------------|--------|------|
| ASTパーサー | REQ-AST-001 ~ REQ-AST-005 | AST解析機能 |
| グラフエンジン | REQ-GRF-001 ~ REQ-GRF-006 | グラフ管理機能 |
| セマンティック | REQ-SEM-001 ~ REQ-SEM-004 | 意味解析機能 |
| インデクサー | REQ-IDX-001 ~ REQ-IDX-004 | インデックス管理 |

---

## 2. コンポーネント図

### 2.1 コアエンジン全体構成

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           Core Engine Container                               │
│                           src/codegraph_mcp/core/                            │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                              Indexer                                     │ │
│  │                           (indexer.py)                                   │ │
│  │                                                                          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │ FileCollector│  │  GitDiffer   │  │ IndexManager │                  │ │
│  │  │              │  │              │  │              │                  │ │
│  │  │ REQ-IDX-001  │  │ REQ-IDX-002  │  │ REQ-IDX-003  │                  │ │
│  │  │ REQ-IDX-004  │  │ REQ-STR-004  │  │              │                  │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │ │
│  │         │                 │                 │                           │ │
│  └─────────┼─────────────────┼─────────────────┼───────────────────────────┘ │
│            │                 │                 │                              │
│            ▼                 │                 │                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                            AST Parser                                    │ │
│  │                            (parser.py)                                   │ │
│  │                                                                          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │ TreeSitter   │  │ EntityExtrac │  │LanguageConf │                  │ │
│  │  │    Core      │  │    tor       │  │    ig        │                  │ │
│  │  │              │  │              │  │              │                  │ │
│  │  │ REQ-AST-001  │  │ REQ-AST-001  │  │ REQ-AST-004  │                  │ │
│  │  │ REQ-AST-002  │  │ REQ-AST-002  │  │              │                  │ │
│  │  │ REQ-AST-003  │  │ REQ-AST-003  │  │              │                  │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────────┘                  │ │
│  │         │                 │                                             │ │
│  └─────────┼─────────────────┼─────────────────────────────────────────────┘ │
│            │                 │                                               │
│            ▼                 ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                           Graph Engine                                   │ │
│  │                            (graph.py)                                    │ │
│  │                                                                          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │ EntityStore  │  │RelationStore │  │ QueryEngine  │                  │ │
│  │  │              │  │              │  │              │                  │ │
│  │  │ REQ-GRF-001  │  │ REQ-GRF-002  │  │ REQ-GRF-006  │                  │ │
│  │  │ REQ-GRF-003  │  │ REQ-GRF-004  │  │              │                  │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │ │
│  │         │                 │                 │                           │ │
│  │         └─────────────────┼─────────────────┘                           │ │
│  │                           │                                             │ │
│  └───────────────────────────┼─────────────────────────────────────────────┘ │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        Semantic Analyzer                                 │ │
│  │                         (semantic.py)                                    │ │
│  │                                                                          │ │
│  │  ┌──────────────┐  ┌──────────────┐                                    │ │
│  │  │ Description  │  │ Community    │                                    │ │
│  │  │ Generator    │  │ Detector     │                                    │ │
│  │  │              │  │              │                                    │ │
│  │  │ REQ-SEM-001  │  │ REQ-SEM-003  │                                    │ │
│  │  │ REQ-SEM-002  │  │ REQ-SEM-004  │                                    │ │
│  │  └──────────────┘  └──────────────┘                                    │ │
│  │                                                                          │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. ASTパーサー詳細設計

### 3.1 クラス図

```
┌─────────────────────────────────────────────────────────────────┐
│                         ASTParser                                │
├─────────────────────────────────────────────────────────────────┤
│ - _parsers: dict[str, Parser]                                   │
│ - _language_configs: dict[str, LanguageConfig]                  │
├─────────────────────────────────────────────────────────────────┤
│ + parse_file(path: str, lang: str) -> ParseResult              │
│ + extract_entities(tree: Tree) -> list[Entity]                 │
│ + extract_relations(tree: Tree, entities: list) -> list[Rel]   │
│ + detect_language(path: str) -> str | None                     │
│ - _get_parser(lang: str) -> Parser                             │
│ - _extract_functions(node: Node) -> list[Entity]               │
│ - _extract_classes(node: Node) -> list[Entity]                 │
│ - _extract_imports(node: Node) -> list[Entity]                 │
│ - _extract_calls(node: Node) -> list[Relation]                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ uses
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LanguageConfig                              │
├─────────────────────────────────────────────────────────────────┤
│ + name: str                                                      │
│ + extensions: list[str]                                          │
│ + parser_name: str                                               │
│ + node_types: NodeTypeConfig                                     │
├─────────────────────────────────────────────────────────────────┤
│ + get_function_nodes() -> list[str]                             │
│ + get_class_nodes() -> list[str]                                │
│ + get_import_nodes() -> list[str]                               │
│ + get_call_nodes() -> list[str]                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 データモデル

```python
# models.py
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class EntityType(Enum):
    FILE = "file"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    INTERFACE = "interface"
    IMPORT = "import"

class RelationType(Enum):
    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"
    CONTAINS = "contains"
    IMPLEMENTS = "implements"

@dataclass
class Entity:
    """コードエンティティ (REQ-GRF-001, REQ-GRF-003)"""
    id: str                           # UUID
    type: EntityType                  # エンティティタイプ
    name: str                         # 名前
    qualified_name: str               # 完全修飾名
    file_path: str                    # ファイルパス
    start_line: int                   # 開始行
    end_line: int                     # 終了行
    signature: Optional[str]          # シグネチャ
    docstring: Optional[str]          # ドキュメント文字列
    source_code: Optional[str]        # ソースコード
    embedding: Optional[bytes]        # ベクトル埋め込み
    community_id: Optional[int]       # コミュニティID
    
@dataclass
class Relation:
    """エンティティ間の関係 (REQ-GRF-002, REQ-GRF-004)"""
    id: int                           # 自動採番ID
    source_id: str                    # ソースエンティティID
    target_id: str                    # ターゲットエンティティID
    type: RelationType                # 関係タイプ
    weight: float = 1.0               # 重み
    metadata: Optional[dict] = None   # メタデータ

@dataclass
class ParseResult:
    """パース結果"""
    file_path: str
    language: str
    entities: list[Entity]
    relations: list[Relation]
    errors: list[str]
    parse_time_ms: float
```

### 3.3 言語設定

```python
# languages/config.py

LANGUAGE_CONFIGS = {
    # Python (REQ-AST-001)
    "python": {
        "extensions": [".py"],
        "parser": "tree-sitter-python",
        "node_types": {
            "function": ["function_definition"],
            "class": ["class_definition"],
            "import": ["import_statement", "import_from_statement"],
            "call": ["call"],
            "decorator": ["decorator"],
        },
        "name_field": "name",
        "body_field": "body",
    },
    
    # TypeScript (REQ-AST-002)
    "typescript": {
        "extensions": [".ts", ".tsx"],
        "parser": "tree-sitter-typescript",
        "node_types": {
            "function": ["function_declaration", "arrow_function", "method_definition"],
            "class": ["class_declaration"],
            "interface": ["interface_declaration"],
            "import": ["import_statement"],
            "call": ["call_expression"],
        },
        "name_field": "name",
        "body_field": "body",
    },
    
    # Rust (REQ-AST-003) - Phase 2
    "rust": {
        "extensions": [".rs"],
        "parser": "tree-sitter-rust",
        "node_types": {
            "function": ["function_item"],
            "struct": ["struct_item"],
            "enum": ["enum_item"],
            "impl": ["impl_item"],
            "use": ["use_declaration"],
            "call": ["call_expression"],
        },
        "name_field": "name",
        "body_field": "body",
    },
}
```

### 3.4 パース処理シーケンス

```
┌────────┐     ┌──────────┐     ┌───────────┐     ┌──────────┐
│Indexer │     │ASTParser │     │TreeSitter │     │LangConfig│
└───┬────┘     └────┬─────┘     └─────┬─────┘     └────┬─────┘
    │               │                 │                │
    │ parse_file()  │                 │                │
    │──────────────▶│                 │                │
    │               │ detect_language()                │
    │               │─────────────────────────────────▶│
    │               │◀─────────────────────────────────│
    │               │                 │                │
    │               │ get_parser()    │                │
    │               │────────────────▶│                │
    │               │◀────────────────│                │
    │               │                 │                │
    │               │ parse(source)   │                │
    │               │────────────────▶│                │
    │               │◀────────────────│ Tree          │
    │               │                 │                │
    │               │ extract_entities()               │
    │               │──────────────┐  │                │
    │               │◀─────────────┘  │                │
    │               │                 │                │
    │               │ extract_relations()              │
    │               │──────────────┐  │                │
    │               │◀─────────────┘  │                │
    │               │                 │                │
    │◀──────────────│ ParseResult     │                │
    │               │                 │                │
```

### 3.5 エラーハンドリング

```python
# parser.py - REQ-AST-005

class ParseError(Exception):
    """パースエラー"""
    def __init__(self, file_path: str, line: int, message: str):
        self.file_path = file_path
        self.line = line
        self.message = message

class ASTParser:
    def parse_file(self, file_path: str, language: str) -> ParseResult:
        errors = []
        entities = []
        relations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = self._get_parser(language).parse(source.encode())
            
            # 構文エラーがあっても解析可能な部分は処理
            if tree.root_node.has_error:
                errors.append(f"Syntax errors detected in {file_path}")
                # エラーノードを収集
                for node in self._find_error_nodes(tree.root_node):
                    errors.append(f"  Line {node.start_point[0]}: {node.type}")
            
            # 解析可能な部分を処理
            entities = self.extract_entities(tree)
            relations = self.extract_relations(tree, entities)
            
        except Exception as e:
            errors.append(f"Failed to parse {file_path}: {str(e)}")
        
        return ParseResult(
            file_path=file_path,
            language=language,
            entities=entities,
            relations=relations,
            errors=errors,
            parse_time_ms=...
        )
```

---

## 4. グラフエンジン詳細設計

### 4.1 クラス図

```
┌─────────────────────────────────────────────────────────────────┐
│                        GraphEngine                               │
├─────────────────────────────────────────────────────────────────┤
│ - _db: aiosqlite.Connection                                      │
│ - _entity_store: EntityStore                                     │
│ - _relation_store: RelationStore                                 │
│ - _query_engine: QueryEngine                                     │
├─────────────────────────────────────────────────────────────────┤
│ + async connect(db_path: str) -> None                           │
│ + async close() -> None                                          │
│ + async add_entity(entity: Entity) -> str                       │
│ + async add_relation(relation: Relation) -> int                 │
│ + async get_entity(id: str) -> Entity | None                    │
│ + async query(query: GraphQuery) -> QueryResult                 │
│ + async find_callers(func: str, depth: int) -> list[CallPath]   │
│ + async find_callees(func: str, depth: int) -> list[CallPath]   │
│ + async find_dependencies(name: str, dir: str) -> list[Dep]     │
│ + async get_stats() -> GraphStats                               │
└─────────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   EntityStore   │  │  RelationStore  │  │   QueryEngine   │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ + add()         │  │ + add()         │  │ + execute()     │
│ + get()         │  │ + get()         │  │ + traverse()    │
│ + update()      │  │ + find_by_src() │  │ + search()      │
│ + delete()      │  │ + find_by_tgt() │  │ + aggregate()   │
│ + search()      │  │ + find_by_type()│  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 4.2 SQLiteスキーマ

```sql
-- storage/schema.sql (REQ-STR-001, REQ-GRF-003~006)

-- エンティティテーブル
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    qualified_name TEXT,
    file_path TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    signature TEXT,
    docstring TEXT,
    source_code TEXT,
    embedding BLOB,
    community_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 関係テーブル
CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    type TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    metadata TEXT,  -- JSON形式
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES entities(id) ON DELETE CASCADE
);

-- コミュニティテーブル (REQ-SEM-003)
CREATE TABLE IF NOT EXISTS communities (
    id INTEGER PRIMARY KEY,
    level INTEGER NOT NULL DEFAULT 0,
    name TEXT,
    summary TEXT,
    member_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス情報テーブル
CREATE TABLE IF NOT EXISTS index_info (
    id INTEGER PRIMARY KEY,
    repo_path TEXT NOT NULL,
    last_commit TEXT,
    last_indexed_at TIMESTAMP,
    total_files INTEGER DEFAULT 0,
    total_entities INTEGER DEFAULT 0
);

-- パフォーマンスインデックス (REQ-GRF-006)
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_file ON entities(file_path);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_qualified ON entities(qualified_name);
CREATE INDEX IF NOT EXISTS idx_entities_community ON entities(community_id);

CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id);
CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id);
CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(type);

-- 複合インデックス
CREATE INDEX IF NOT EXISTS idx_relations_src_type ON relations(source_id, type);
CREATE INDEX IF NOT EXISTS idx_relations_tgt_type ON relations(target_id, type);
```

### 4.3 グラフクエリAPI

```python
# graph.py

@dataclass
class GraphQuery:
    """グラフクエリ定義"""
    type: str                         # query_type: search, traverse, aggregate
    entity_types: list[str] = None    # フィルタ対象エンティティタイプ
    relation_types: list[str] = None  # フィルタ対象関係タイプ
    start_entity: str = None          # 開始エンティティ
    direction: str = "both"           # upstream, downstream, both
    max_depth: int = 3                # 最大深さ
    limit: int = 100                  # 結果制限数
    search_text: str = None           # テキスト検索
    file_pattern: str = None          # ファイルパターン

@dataclass
class QueryResult:
    """クエリ結果"""
    entities: list[Entity]
    relations: list[Relation]
    paths: list[list[str]] = None     # パス情報（traverse時）
    stats: dict = None                # 統計情報
    query_time_ms: float = 0

class GraphEngine:
    async def query(self, query: GraphQuery) -> QueryResult:
        """汎用グラフクエリ実行"""
        if query.type == "search":
            return await self._execute_search(query)
        elif query.type == "traverse":
            return await self._execute_traverse(query)
        elif query.type == "aggregate":
            return await self._execute_aggregate(query)
        else:
            raise ValueError(f"Unknown query type: {query.type}")
    
    async def find_callers(
        self, 
        function_name: str, 
        max_depth: int = 3
    ) -> list[CallPath]:
        """関数の呼び出し元を検索 (REQ-TLS-003)"""
        query = GraphQuery(
            type="traverse",
            start_entity=function_name,
            relation_types=["calls"],
            direction="upstream",
            max_depth=max_depth
        )
        result = await self.query(query)
        return self._build_call_paths(result)
    
    async def find_callees(
        self, 
        function_name: str, 
        max_depth: int = 3
    ) -> list[CallPath]:
        """関数の呼び出し先を検索 (REQ-TLS-004)"""
        query = GraphQuery(
            type="traverse",
            start_entity=function_name,
            relation_types=["calls"],
            direction="downstream",
            max_depth=max_depth
        )
        result = await self.query(query)
        return self._build_call_paths(result)
```

### 4.4 グラフ走査アルゴリズム

```python
# graph.py - BFS/DFS走査

class QueryEngine:
    async def traverse_bfs(
        self,
        start_id: str,
        direction: str,
        relation_types: list[str],
        max_depth: int
    ) -> TraverseResult:
        """幅優先探索によるグラフ走査"""
        visited = set()
        paths = []
        queue = deque([(start_id, [start_id], 0)])
        
        while queue:
            current_id, path, depth = queue.popleft()
            
            if current_id in visited:
                continue
            visited.add(current_id)
            
            if depth > 0:  # 開始ノード以外をパスに追加
                paths.append(path)
            
            if depth >= max_depth:
                continue
            
            # 隣接ノードを取得
            neighbors = await self._get_neighbors(
                current_id, direction, relation_types
            )
            
            for neighbor_id in neighbors:
                if neighbor_id not in visited:
                    queue.append((
                        neighbor_id, 
                        path + [neighbor_id], 
                        depth + 1
                    ))
        
        return TraverseResult(visited=visited, paths=paths)
    
    async def _get_neighbors(
        self,
        entity_id: str,
        direction: str,
        relation_types: list[str]
    ) -> list[str]:
        """隣接ノードを取得"""
        if direction == "downstream":
            sql = """
                SELECT target_id FROM relations 
                WHERE source_id = ? AND type IN ({})
            """.format(','.join('?' * len(relation_types)))
            params = [entity_id] + relation_types
        elif direction == "upstream":
            sql = """
                SELECT source_id FROM relations 
                WHERE target_id = ? AND type IN ({})
            """.format(','.join('?' * len(relation_types)))
            params = [entity_id] + relation_types
        else:  # both
            sql = """
                SELECT target_id FROM relations 
                WHERE source_id = ? AND type IN ({})
                UNION
                SELECT source_id FROM relations 
                WHERE target_id = ? AND type IN ({})
            """.format(
                ','.join('?' * len(relation_types)),
                ','.join('?' * len(relation_types))
            )
            params = [entity_id] + relation_types + [entity_id] + relation_types
        
        async with self._db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
```

---

## 5. セマンティックアナライザー詳細設計

### 5.1 クラス図

```
┌─────────────────────────────────────────────────────────────────┐
│                     SemanticAnalyzer                             │
├─────────────────────────────────────────────────────────────────┤
│ - _llm_client: LLMClient | None                                  │
│ - _community_detector: CommunityDetector                         │
│ - _graph_engine: GraphEngine                                     │
├─────────────────────────────────────────────────────────────────┤
│ + async generate_description(entity: Entity) -> str             │
│ + async generate_community_summary(comm: Community) -> str      │
│ + async detect_communities(level: int) -> list[Community]       │
│ + async assign_communities() -> None                             │
│ + async get_community_hierarchy() -> CommunityHierarchy         │
└─────────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   LLMClient     │  │CommunityDetector│  │DescriptionGen  │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ + generate()    │  │ + detect()      │  │ + generate()    │
│ + embed()       │  │ + hierarchical()│  │ + batch()       │
│                 │  │ + modularity()  │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 5.2 コミュニティ検出

```python
# semantic.py - REQ-SEM-003, REQ-SEM-004
import networkx as nx
from networkx.algorithms import community as nx_community

class CommunityDetector:
    """コミュニティ検出器（Louvainアルゴリズム使用）"""
    
    def __init__(self, graph_engine: GraphEngine):
        self._graph_engine = graph_engine
    
    async def detect_communities(
        self, 
        level: int = 0
    ) -> list[Community]:
        """コミュニティを検出"""
        # グラフをNetworkX形式に変換
        nx_graph = await self._build_networkx_graph()
        
        # Louvainアルゴリズムでコミュニティ検出
        communities = nx_community.louvain_communities(
            nx_graph,
            resolution=1.0 + level * 0.5  # レベルに応じて解像度調整
        )
        
        result = []
        for i, members in enumerate(communities):
            community = Community(
                id=i,
                level=level,
                member_ids=list(members),
                member_count=len(members)
            )
            result.append(community)
        
        return result
    
    async def detect_hierarchical(
        self, 
        max_level: int = 2
    ) -> CommunityHierarchy:
        """階層的コミュニティ検出"""
        hierarchy = CommunityHierarchy()
        
        for level in range(max_level + 1):
            communities = await self.detect_communities(level)
            hierarchy.add_level(level, communities)
        
        return hierarchy
    
    async def _build_networkx_graph(self) -> nx.Graph:
        """SQLiteからNetworkXグラフを構築"""
        G = nx.Graph()
        
        # エンティティをノードとして追加
        entities = await self._graph_engine.get_all_entities()
        for entity in entities:
            G.add_node(entity.id, **entity.__dict__)
        
        # 関係をエッジとして追加
        relations = await self._graph_engine.get_all_relations()
        for rel in relations:
            G.add_edge(
                rel.source_id, 
                rel.target_id, 
                type=rel.type,
                weight=rel.weight
            )
        
        return G
```

### 5.3 説明生成

```python
# semantic.py - REQ-SEM-001, REQ-SEM-002

class DescriptionGenerator:
    """LLMを使用した説明生成器"""
    
    ENTITY_PROMPT = """
以下のコードエンティティについて、簡潔な説明を生成してください。

タイプ: {type}
名前: {name}
シグネチャ: {signature}
ソースコード:
```
{source_code}
```

説明（1-2文で）:
"""

    COMMUNITY_PROMPT = """
以下のコードモジュール/コンポーネントについて、簡潔な要約を生成してください。

メンバー関数/クラス:
{members}

関係:
{relations}

このコンポーネントの目的と責務を1段落で説明してください:
"""

    async def generate_entity_description(
        self, 
        entity: Entity,
        llm_client: LLMClient
    ) -> str:
        """エンティティの説明を生成 (REQ-SEM-001)"""
        prompt = self.ENTITY_PROMPT.format(
            type=entity.type.value,
            name=entity.name,
            signature=entity.signature or "N/A",
            source_code=entity.source_code[:1000] if entity.source_code else "N/A"
        )
        
        return await llm_client.generate(prompt, max_tokens=100)
    
    async def generate_community_summary(
        self, 
        community: Community,
        entities: list[Entity],
        relations: list[Relation],
        llm_client: LLMClient
    ) -> str:
        """コミュニティの要約を生成 (REQ-SEM-002)"""
        members_text = "\n".join([
            f"- {e.type.value}: {e.name}" for e in entities[:20]
        ])
        relations_text = "\n".join([
            f"- {r.source_id} --{r.type}--> {r.target_id}" 
            for r in relations[:20]
        ])
        
        prompt = self.COMMUNITY_PROMPT.format(
            members=members_text,
            relations=relations_text
        )
        
        return await llm_client.generate(prompt, max_tokens=200)
```

---

## 6. インデクサー詳細設計

### 6.1 クラス図

```
┌─────────────────────────────────────────────────────────────────┐
│                          Indexer                                 │
├─────────────────────────────────────────────────────────────────┤
│ - _parser: ASTParser                                             │
│ - _graph_engine: GraphEngine                                     │
│ - _git_differ: GitDiffer                                         │
│ - _file_collector: FileCollector                                 │
├─────────────────────────────────────────────────────────────────┤
│ + async index_repository(path: str, incr: bool) -> IndexResult  │
│ + async reindex_file(path: str) -> IndexResult                  │
│ + async get_index_status(path: str) -> IndexStatus              │
│ + async clear_index(path: str) -> None                          │
└─────────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  FileCollector  │  │   GitDiffer     │  │  IndexManager   │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ + collect()     │  │ + get_changed() │  │ + save_status() │
│ + filter()      │  │ + get_commit()  │  │ + load_status() │
│ + get_lang()    │  │ + is_git_repo() │  │ + update()      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 6.2 インデックス処理フロー

```python
# indexer.py - REQ-IDX-001~004

@dataclass
class IndexResult:
    """インデックス結果"""
    repo_path: str
    total_files: int
    indexed_files: int
    skipped_files: int
    total_entities: int
    total_relations: int
    errors: list[str]
    duration_ms: float
    incremental: bool

class Indexer:
    async def index_repository(
        self, 
        repo_path: str, 
        incremental: bool = True
    ) -> IndexResult:
        """リポジトリをインデックス (REQ-IDX-001)"""
        start_time = time.time()
        errors = []
        
        # ファイル収集
        if incremental and self._git_differ.is_git_repo(repo_path):
            # Git差分から変更ファイルを取得 (REQ-IDX-002)
            files = await self._git_differ.get_changed_files(repo_path)
        else:
            # 全ファイル収集 (REQ-IDX-003)
            files = await self._file_collector.collect(repo_path)
        
        # .gitignoreフィルタ (REQ-IDX-004)
        files = await self._file_collector.filter_gitignore(files, repo_path)
        
        indexed_count = 0
        skipped_count = 0
        total_entities = 0
        total_relations = 0
        
        for file_path in files:
            try:
                # 言語検出
                language = self._parser.detect_language(file_path)
                if language is None:
                    skipped_count += 1
                    continue
                
                # パース
                result = await self._parser.parse_file(file_path, language)
                
                if result.errors:
                    errors.extend(result.errors)
                
                # グラフに追加
                for entity in result.entities:
                    await self._graph_engine.add_entity(entity)
                    total_entities += 1
                
                for relation in result.relations:
                    await self._graph_engine.add_relation(relation)
                    total_relations += 1
                
                indexed_count += 1
                
            except Exception as e:
                errors.append(f"Error indexing {file_path}: {str(e)}")
                skipped_count += 1
        
        # インデックス状態を保存
        await self._save_index_status(repo_path)
        
        duration = (time.time() - start_time) * 1000
        
        return IndexResult(
            repo_path=repo_path,
            total_files=len(files),
            indexed_files=indexed_count,
            skipped_files=skipped_count,
            total_entities=total_entities,
            total_relations=total_relations,
            errors=errors,
            duration_ms=duration,
            incremental=incremental
        )
```

### 6.3 Git差分検出

```python
# utils/git.py - REQ-STR-004

import subprocess
from pathlib import Path

class GitDiffer:
    """Git差分検出器"""
    
    def is_git_repo(self, path: str) -> bool:
        """Gitリポジトリかどうかを判定"""
        git_dir = Path(path) / ".git"
        return git_dir.exists()
    
    async def get_current_commit(self, repo_path: str) -> str:
        """現在のコミットハッシュを取得"""
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    
    async def get_changed_files(
        self, 
        repo_path: str,
        since_commit: str = None
    ) -> list[str]:
        """変更されたファイルを取得 (REQ-IDX-002)"""
        if since_commit:
            # 指定コミット以降の変更
            cmd = ["git", "diff", "--name-only", since_commit, "HEAD"]
        else:
            # 直近のコミットとの差分
            cmd = ["git", "diff", "--name-only", "HEAD~1", "HEAD"]
        
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        files = result.stdout.strip().split('\n')
        return [
            str(Path(repo_path) / f) 
            for f in files if f
        ]
    
    async def get_staged_files(self, repo_path: str) -> list[str]:
        """ステージングされたファイルを取得"""
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        files = result.stdout.strip().split('\n')
        return [
            str(Path(repo_path) / f) 
            for f in files if f
        ]
```

### 6.4 ファイルコレクター

```python
# indexer.py

class FileCollector:
    """ファイル収集器"""
    
    SUPPORTED_EXTENSIONS = {
        ".py", ".ts", ".tsx", ".js", ".jsx",  # Phase 1
        ".rs",  # Phase 2
        ".go", ".java", ".cs"  # Phase 3
    }
    
    async def collect(
        self, 
        repo_path: str,
        extensions: set[str] = None
    ) -> list[str]:
        """対象ファイルを収集"""
        extensions = extensions or self.SUPPORTED_EXTENSIONS
        files = []
        
        for path in Path(repo_path).rglob("*"):
            if path.is_file() and path.suffix in extensions:
                files.append(str(path))
        
        return files
    
    async def filter_gitignore(
        self, 
        files: list[str],
        repo_path: str
    ) -> list[str]:
        """gitignoreパターンでフィルタ (REQ-IDX-004)"""
        gitignore_path = Path(repo_path) / ".gitignore"
        
        if not gitignore_path.exists():
            return files
        
        # gitignoreパターンを読み込み
        patterns = self._parse_gitignore(gitignore_path)
        
        # フィルタリング
        return [
            f for f in files 
            if not self._matches_gitignore(f, patterns, repo_path)
        ]
```

---

## 7. 要件トレーサビリティ

### 7.1 コンポーネント → 要件マッピング

| コンポーネント | クラス | 要件ID | 実装状況 |
|---------------|--------|--------|---------|
| AST Parser | ASTParser | REQ-AST-001~005 | Phase 1 |
| AST Parser | LanguageConfig | REQ-AST-004 | Phase 1 |
| Graph Engine | GraphEngine | REQ-GRF-001~006 | Phase 1 |
| Graph Engine | EntityStore | REQ-GRF-001, 003 | Phase 1 |
| Graph Engine | RelationStore | REQ-GRF-002, 004 | Phase 1 |
| Graph Engine | QueryEngine | REQ-GRF-006 | Phase 1 |
| Semantic | SemanticAnalyzer | REQ-SEM-001~004 | Phase 2 |
| Semantic | CommunityDetector | REQ-SEM-003, 004 | Phase 2 |
| Semantic | DescriptionGenerator | REQ-SEM-001, 002 | Phase 2 |
| Indexer | Indexer | REQ-IDX-001~004 | Phase 1 |
| Indexer | GitDiffer | REQ-IDX-002, REQ-STR-004 | Phase 1 |
| Indexer | FileCollector | REQ-IDX-004 | Phase 1 |

---

## 8. パフォーマンス設計

### 8.1 パフォーマンス目標

| メトリクス | 目標値 | 測定方法 | 要件ID |
|-----------|--------|---------|--------|
| インデックス速度 | 10万行/30秒 | ベンチマーク | REQ-NFR-001 |
| 増分インデックス | 2秒以内 | ベンチマーク | REQ-NFR-002 |
| クエリレスポンス | 500ms以内 | レスポンスタイム | REQ-NFR-003 |

### 8.2 最適化戦略

| 戦略 | 説明 | 対象 |
|------|------|------|
| バッチ処理 | エンティティ/関係の一括挿入 | DB書き込み |
| 接続プール | SQLite接続の再利用 | DB接続 |
| インデックス | 高速検索用インデックス | クエリ |
| キャッシュ | パース結果キャッシュ | AST解析 |
| 並列処理 | ファイル単位の並列パース | インデックス |

### 8.3 ベンチマーク計画

```python
# tests/benchmarks/test_performance.py

import pytest
import time

@pytest.mark.benchmark
async def test_index_100k_lines(indexer, sample_repo_100k):
    """10万行インデックスのベンチマーク (REQ-NFR-001)"""
    start = time.time()
    result = await indexer.index_repository(sample_repo_100k)
    duration = time.time() - start
    
    assert duration < 30, f"Indexing took {duration}s, expected < 30s"
    assert result.errors == []

@pytest.mark.benchmark
async def test_incremental_index(indexer, sample_repo):
    """増分インデックスのベンチマーク (REQ-NFR-002)"""
    # 初回インデックス
    await indexer.index_repository(sample_repo)
    
    # ファイル変更をシミュレート
    modify_single_file(sample_repo)
    
    # 増分インデックス
    start = time.time()
    result = await indexer.index_repository(sample_repo, incremental=True)
    duration = time.time() - start
    
    assert duration < 2, f"Incremental indexing took {duration}s, expected < 2s"

@pytest.mark.benchmark
async def test_query_response_time(graph_engine, indexed_repo):
    """クエリレスポンスタイムのベンチマーク (REQ-NFR-003)"""
    start = time.time()
    result = await graph_engine.find_callers("main", max_depth=3)
    duration = (time.time() - start) * 1000
    
    assert duration < 500, f"Query took {duration}ms, expected < 500ms"
```

---

## 9. 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|------------|------|----------|--------|
| 1.0.0 | 2025-11-26 | 初版作成 | System |

---

**Document Status**: Draft  
**Constitutional Compliance**: Article I (Library-First), Article III (Test-First) ✓
