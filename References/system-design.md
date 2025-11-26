# CodeGraph MCP Server 設計書

## 1. エグゼクティブサマリー

### 1.1 プロジェクト概要

**CodeGraph MCP Server** は、Microsoft GraphRAG のコンセプトとcode-graph-ragの実装を参考に、ソースコード分析に最適化されたMCP (Model Context Protocol) サーバーです。GitHub Copilot、Claude Code、その他のMCP対応AIツールからコードベースの構造的理解と効率的なコード補完を実現します。

### 1.2 code-graph-rag との差別化

| 観点 | code-graph-rag | CodeGraph MCP Server |
|------|----------------|---------------------|
| アーキテクチャ | CLI + Interactive Mode | MCP Native Server |
| グラフDB | Memgraph (外部依存) | **SQLite + 組み込みグラフエンジン** |
| デプロイ | Docker必須 | **シングルバイナリ / pip install** |
| 起動時間 | 重い (DB起動含む) | **軽量 (秒単位)** |
| MCP統合 | 後付け対応 | **ネイティブ設計** |
| スコープ | 単一リポジトリ | **マルチリポジトリ対応** |
| インデックス更新 | 手動 / ファイル監視 | **Git差分ベース増分更新** |
| GraphRAG機能 | なし | **コミュニティ要約・グローバルクエリ** |

### 1.3 主要な設計目標

1. **ゼロ構成起動**: `pip install codegraph-mcp && codegraph-mcp serve` で即座に利用可能
2. **軽量・高速**: 外部DB不要、10万行規模のコードベースを10秒以内でインデックス
3. **MCP First**: Tools, Resources, Prompts のすべてを活用した包括的なMCP実装
4. **増分更新**: Git差分を活用し、変更ファイルのみを再インデックス
5. **GraphRAG統合**: コードのセマンティクス理解にLLMを活用したコミュニティ要約

---

## 2. システムアーキテクチャ

### 2.1 全体構成

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MCP Clients                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │GitHub Copilot│  │ Claude Code │  │   Cursor    │  │   Windsurf  │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
└─────────┼────────────────┼────────────────┼────────────────┼───────────┘
          │                │                │                │
          └────────────────┴────────────────┴────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CodeGraph MCP Server                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      MCP Protocol Layer                          │   │
│  │  • stdio / SSE / Streamable HTTP Transport                       │   │
│  │  • JSON-RPC 2.0 Message Handling                                 │   │
│  │  • OAuth 2.1 Authentication (optional)                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                   │                                     │
│  ┌────────────────┬───────────────┼───────────────┬────────────────┐   │
│  │    Tools       │   Resources   │    Prompts    │   Sampling     │   │
│  │  (14 tools)    │ (4 resource   │  (6 prompts)  │  (LLM calls)   │   │
│  │                │   types)      │               │                │   │
│  └───────┬────────┴───────┬───────┴───────┬───────┴────────┬───────┘   │
│          │                │               │                │           │
│  ┌───────┴────────────────┴───────────────┴────────────────┴───────┐   │
│  │                      Core Engine                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │   │
│  │  │  AST Parser  │  │ Graph Engine │  │   Semantic Analyzer  │   │   │
│  │  │ (Tree-sitter)│  │  (In-memory  │  │   (LLM-powered)      │   │   │
│  │  │              │  │   + SQLite)  │  │                      │   │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │   │
│  │         │                 │                     │               │   │
│  │  ┌──────┴─────────────────┴─────────────────────┴───────────┐   │   │
│  │  │                   Knowledge Graph                         │   │   │
│  │  │  • Entities: File, Module, Class, Function, Method       │   │   │
│  │  │  • Relations: CALLS, IMPORTS, INHERITS, CONTAINS         │   │   │
│  │  │  • Communities: Module clusters with summaries           │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                   │                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Storage Layer                                 │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │   │
│  │  │   SQLite    │  │  File Cache │  │   Vector Store          │  │   │
│  │  │ (Graph DB)  │  │  (AST cache)│  │   (Embeddings)          │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 コンポーネント詳細

#### 2.2.1 AST Parser (Tree-sitter ベース)

```python
# 対応言語と抽出対象
LANGUAGE_CONFIG = {
    "python": {
        "extensions": [".py"],
        "function_nodes": ["function_definition"],
        "class_nodes": ["class_definition"],
        "import_nodes": ["import_statement", "import_from_statement"],
        "call_nodes": ["call"],
    },
    "typescript": {
        "extensions": [".ts", ".tsx"],
        "function_nodes": ["function_declaration", "arrow_function", "method_definition"],
        "class_nodes": ["class_declaration", "interface_declaration"],
        "import_nodes": ["import_statement"],
        "call_nodes": ["call_expression"],
    },
    "rust": {
        "extensions": [".rs"],
        "function_nodes": ["function_item"],
        "class_nodes": ["struct_item", "enum_item", "impl_item"],
        "import_nodes": ["use_declaration"],
        "call_nodes": ["call_expression"],
    },
    # ... 他の言語
}
```

#### 2.2.2 Graph Engine

**スキーマ設計:**

```sql
-- Nodes
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- 'file', 'module', 'class', 'function', 'method'
    name TEXT NOT NULL,
    qualified_name TEXT,
    file_path TEXT,
    start_line INTEGER,
    end_line INTEGER,
    signature TEXT,
    docstring TEXT,
    source_code TEXT,
    embedding BLOB,      -- Vector embedding for semantic search
    community_id INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Edges
CREATE TABLE relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'CALLS', 'IMPORTS', 'INHERITS', 'CONTAINS', 'IMPLEMENTS'
    weight REAL DEFAULT 1.0,
    metadata TEXT,       -- JSON for additional properties
    FOREIGN KEY (source_id) REFERENCES entities(id),
    FOREIGN KEY (target_id) REFERENCES entities(id)
);

-- Community summaries (GraphRAG feature)
CREATE TABLE communities (
    id INTEGER PRIMARY KEY,
    level INTEGER NOT NULL,  -- Hierarchy level (0=fine, 1=coarse, ...)
    name TEXT,
    summary TEXT,            -- LLM-generated summary
    member_count INTEGER,
    created_at TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_entities_file ON entities(file_path);
CREATE INDEX idx_entities_community ON entities(community_id);
CREATE INDEX idx_relations_source ON relations(source_id);
CREATE INDEX idx_relations_target ON relations(target_id);
CREATE INDEX idx_relations_type ON relations(type);
```

#### 2.2.3 Semantic Analyzer (GraphRAG 機能)

```python
class SemanticAnalyzer:
    """LLMを使用したコードのセマンティクス分析"""
    
    async def generate_entity_description(self, entity: Entity) -> str:
        """エンティティの自然言語説明を生成"""
        prompt = f"""
        以下のコードエンティティについて、その目的と機能を1-2文で説明してください。
        
        Type: {entity.type}
        Name: {entity.name}
        Signature: {entity.signature}
        Docstring: {entity.docstring}
        Code:
        ```
        {entity.source_code[:500]}
        ```
        """
        return await self.llm.complete(prompt)
    
    async def generate_community_summary(self, community: Community) -> str:
        """モジュールコミュニティの要約を生成"""
        members = self.graph.get_community_members(community.id)
        prompt = f"""
        以下のコードモジュール群は関連するコンポーネントのクラスターです。
        このクラスターの主要な責務と機能を要約してください。
        
        メンバー:
        {self._format_members(members)}
        
        関係性:
        {self._format_relations(members)}
        """
        return await self.llm.complete(prompt)
```

---

## 3. MCP インターフェース設計

### 3.1 Tools (14 tools)

#### 3.1.1 グラフクエリツール

```python
@mcp.tool()
async def query_codebase(
    query: str,
    scope: Literal["all", "functions", "classes", "files"] = "all",
    limit: int = 10
) -> list[CodeEntity]:
    """
    自然言語でコードベースを検索します。
    
    Examples:
    - "ユーザー認証に関連するクラスを探して"
    - "データベース接続を行う関数"
    - "APIエンドポイントの定義"
    """

@mcp.tool()
async def find_dependencies(
    entity_name: str,
    direction: Literal["upstream", "downstream", "both"] = "both",
    depth: int = 2
) -> DependencyGraph:
    """
    指定エンティティの依存関係を取得します。
    
    - upstream: このエンティティが依存しているもの
    - downstream: このエンティティに依存しているもの
    """

@mcp.tool()
async def find_callers(function_name: str, max_depth: int = 3) -> list[CallPath]:
    """指定関数を呼び出しているすべての関数を取得"""

@mcp.tool()
async def find_callees(function_name: str, max_depth: int = 3) -> list[CallPath]:
    """指定関数が呼び出しているすべての関数を取得"""

@mcp.tool()
async def find_implementations(interface_name: str) -> list[CodeEntity]:
    """インターフェース/抽象クラスの実装を検索"""

@mcp.tool()
async def analyze_module_structure(module_path: str) -> ModuleAnalysis:
    """モジュールの構造分析（クラス、関数、依存関係の概要）"""
```

#### 3.1.2 コード取得ツール

```python
@mcp.tool()
async def get_code_snippet(
    entity_name: str,
    include_context: bool = True,
    context_lines: int = 5
) -> CodeSnippet:
    """
    エンティティのソースコードを取得します。
    include_context=True の場合、前後の文脈も含めます。
    """

@mcp.tool()
async def read_file_content(
    file_path: str,
    start_line: int | None = None,
    end_line: int | None = None
) -> FileContent:
    """ファイルの内容を読み取ります"""

@mcp.tool()
async def get_file_structure(file_path: str) -> FileStructure:
    """ファイル内のクラス・関数の構造を取得"""
```

#### 3.1.3 GraphRAG ツール

```python
@mcp.tool()
async def global_search(
    query: str,
    community_level: int = 1
) -> GlobalSearchResult:
    """
    コードベース全体に関するグローバルな質問に回答します。
    コミュニティサマリーを使用してマクロレベルの理解を提供。
    
    Examples:
    - "このプロジェクトの主要なアーキテクチャコンポーネントは？"
    - "認証システムの全体的な設計は？"
    - "主要なデザインパターンは何が使われている？"
    """

@mcp.tool()
async def local_search(
    query: str,
    context_entities: list[str] | None = None
) -> LocalSearchResult:
    """
    特定のエンティティに関する詳細な質問に回答します。
    グラフ構造とエンティティ情報を組み合わせて回答。
    
    Examples:
    - "UserService クラスの主な責務は？"
    - "この関数はどのような入力を受け取る？"
    """
```

#### 3.1.4 編集・管理ツール

```python
@mcp.tool()
async def suggest_refactoring(
    entity_name: str,
    refactoring_type: Literal["extract_method", "rename", "move", "inline"]
) -> RefactoringSuggestion:
    """リファクタリングの提案と影響範囲の分析"""

@mcp.tool()
async def reindex_repository(
    path: str | None = None,
    incremental: bool = True
) -> IndexingResult:
    """リポジトリを再インデックス（増分または完全）"""

@mcp.tool()
async def execute_shell_command(
    command: str,
    working_directory: str | None = None,
    timeout: int = 30
) -> CommandResult:
    """シェルコマンドを実行（テスト実行、ビルドなど）"""
```

### 3.2 Resources (4 types)

```python
@mcp.resource("codegraph://entities/{entity_id}")
async def get_entity_resource(entity_id: str) -> Resource:
    """コードエンティティの詳細情報"""
    entity = await graph.get_entity(entity_id)
    return Resource(
        uri=f"codegraph://entities/{entity_id}",
        name=entity.qualified_name,
        mimeType="application/json",
        description=entity.docstring or f"{entity.type}: {entity.name}",
        contents=entity.to_json()
    )

@mcp.resource("codegraph://files/{file_path}")
async def get_file_resource(file_path: str) -> Resource:
    """ファイルリソース（構造情報付き）"""

@mcp.resource("codegraph://communities/{community_id}")
async def get_community_resource(community_id: int) -> Resource:
    """コミュニティ（モジュールクラスター）のサマリー"""

@mcp.resource("codegraph://stats")
async def get_stats_resource() -> Resource:
    """コードベースの統計情報"""
    return Resource(
        uri="codegraph://stats",
        name="Codebase Statistics",
        mimeType="application/json",
        contents={
            "total_files": stats.file_count,
            "total_functions": stats.function_count,
            "total_classes": stats.class_count,
            "languages": stats.language_breakdown,
            "last_indexed": stats.last_indexed.isoformat(),
        }
    )
```

### 3.3 Prompts (6 prompts)

```python
@mcp.prompt()
def code_review_prompt(file_path: str) -> Prompt:
    """コードレビューを実施するためのプロンプトテンプレート"""
    return Prompt(
        name="code_review",
        description="指定ファイルのコードレビューを実施",
        arguments=[
            PromptArgument(name="file_path", description="レビュー対象ファイル", required=True),
            PromptArgument(name="focus_areas", description="重点領域（security, performance, readability）", required=False),
        ],
        messages=[
            PromptMessage(
                role="user",
                content=f"""
以下のファイルのコードレビューを実施してください。

ファイル: {{file_path}}
重点領域: {{focus_areas}}

まず、get_file_structure ツールでファイル構造を確認し、
次に get_code_snippet で実際のコードを取得してレビューしてください。
依存関係は find_dependencies で確認できます。
"""
            )
        ]
    )

@mcp.prompt()
def explain_codebase_prompt() -> Prompt:
    """コードベース全体の説明を生成"""
    return Prompt(
        name="explain_codebase",
        description="コードベースの全体像を説明",
        messages=[
            PromptMessage(
                role="user",
                content="""
このコードベースの全体像を説明してください。

1. まず global_search ツールで主要なアーキテクチャを把握
2. codegraph://stats リソースで統計情報を確認
3. 主要なモジュールとその責務を説明
4. 重要な設計パターンを特定
"""
            )
        ]
    )

@mcp.prompt()
def implement_feature_prompt(feature_description: str) -> Prompt:
    """新機能実装のガイダンス"""

@mcp.prompt()
def debug_issue_prompt(error_message: str) -> Prompt:
    """デバッグ支援プロンプト"""

@mcp.prompt()
def refactor_guidance_prompt(target_entity: str) -> Prompt:
    """リファクタリングガイダンス"""

@mcp.prompt()
def test_generation_prompt(function_name: str) -> Prompt:
    """テストコード生成支援"""
```

---

## 4. 実装計画

### 4.1 ディレクトリ構造

```
codegraph-mcp/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── codegraph_mcp/
│       ├── __init__.py
│       ├── __main__.py           # CLI エントリーポイント
│       ├── server.py             # MCP Server メイン
│       ├── config.py             # 設定管理
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── parser.py         # Tree-sitter AST パーサー
│       │   ├── graph.py          # グラフエンジン
│       │   ├── indexer.py        # インデックス管理
│       │   ├── community.py      # コミュニティ検出
│       │   └── semantic.py       # セマンティック分析 (LLM)
│       │
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── sqlite.py         # SQLite ストレージ
│       │   ├── cache.py          # ファイルキャッシュ
│       │   └── vectors.py        # ベクトルストア
│       │
│       ├── mcp/
│       │   ├── __init__.py
│       │   ├── tools.py          # MCP Tools 定義
│       │   ├── resources.py      # MCP Resources 定義
│       │   └── prompts.py        # MCP Prompts 定義
│       │
│       ├── languages/
│       │   ├── __init__.py
│       │   ├── config.py         # 言語設定
│       │   ├── python.py
│       │   ├── typescript.py
│       │   ├── rust.py
│       │   └── ...
│       │
│       └── utils/
│           ├── __init__.py
│           ├── git.py            # Git 操作
│           └── logging.py
│
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_graph.py
│   ├── test_tools.py
│   └── fixtures/
│
└── examples/
    ├── claude_desktop_config.json
    └── sample_queries.md
```

### 4.2 依存関係

```toml
[project]
name = "codegraph-mcp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",                    # MCP SDK
    "tree-sitter>=0.21.0",           # AST parsing
    "tree-sitter-python>=0.21.0",
    "tree-sitter-javascript>=0.21.0",
    "tree-sitter-typescript>=0.21.0",
    "tree-sitter-rust>=0.21.0",
    "aiosqlite>=0.19.0",             # Async SQLite
    "pydantic>=2.0.0",               # Data validation
    "networkx>=3.0",                 # Graph algorithms
    "numpy>=1.24.0",                 # Vector operations
    "tiktoken>=0.5.0",               # Token counting
    "watchfiles>=0.21.0",            # File watching
    "gitpython>=3.1.0",              # Git operations
    "rich>=13.0.0",                  # CLI formatting
    "typer>=0.9.0",                  # CLI framework
]

[project.optional-dependencies]
embeddings = [
    "sentence-transformers>=2.2.0",  # Local embeddings
]
openai = [
    "openai>=1.0.0",                 # OpenAI API
]
```

### 4.3 開発フェーズ

#### Phase 1: Core Foundation (Week 1-2)
- [ ] プロジェクト構造セットアップ
- [ ] Tree-sitter パーサー実装（Python, TypeScript）
- [ ] SQLite グラフストレージ
- [ ] 基本的なインデックス作成

#### Phase 2: MCP Integration (Week 3-4)
- [ ] MCP Server 基盤
- [ ] 基本 Tools 実装（query, get_code, find_dependencies）
- [ ] Resources 実装
- [ ] stdio トランスポート

#### Phase 3: GraphRAG Features (Week 5-6)
- [ ] コミュニティ検出アルゴリズム
- [ ] LLM統合（サマリー生成）
- [ ] Global/Local Search 実装
- [ ] Prompts 実装

#### Phase 4: Polish & Extensions (Week 7-8)
- [ ] 増分インデックス更新
- [ ] ベクトル検索
- [ ] 追加言語サポート
- [ ] パフォーマンス最適化
- [ ] ドキュメント整備

---

## 5. 使用例

### 5.1 Claude Desktop 設定

```json
{
  "mcpServers": {
    "codegraph": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "/path/to/your/project"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### 5.2 使用シナリオ

#### シナリオ1: コードベース理解
```
User: このプロジェクトの主要なコンポーネントを説明して

Claude: [global_search ツールを使用]
このプロジェクトは以下の主要コンポーネントで構成されています：

1. **認証モジュール** (src/auth/)
   - ユーザー認証とセッション管理を担当
   - JWTトークンベースの認証を実装

2. **APIレイヤー** (src/api/)
   - RESTful APIエンドポイントを定義
   - リクエストバリデーションとレスポンス整形

3. **データアクセス層** (src/repositories/)
   - データベース操作を抽象化
   - Repository パターンを採用
...
```

#### シナリオ2: 影響範囲分析
```
User: UserService.authenticate メソッドを変更した場合の影響範囲は？

Claude: [find_callers ツールを使用]
UserService.authenticate を呼び出している箇所を分析しました：

直接呼び出し元 (5件):
- api/routes/auth.py:login_handler (L45)
- api/routes/auth.py:refresh_token (L78)
- middleware/auth.py:authenticate_request (L23)
- tests/test_auth.py:test_authenticate (L34)
- scripts/admin.py:verify_admin (L56)

間接的な影響 (3件):
- api/routes/users.py (authenticate_request middleware経由)
- api/routes/admin.py (authenticate_request middleware経由)
...
```

#### シナリオ3: 機能実装支援
```
User: パスワードリセット機能を追加したい

Claude: [query_codebase + analyze_module_structure を使用]
既存の認証システムを分析しました。以下のアプローチを提案します：

1. **新規ファイル作成**: src/auth/password_reset.py
   - 既存の UserService パターンに従う
   - EmailService (src/services/email.py) を再利用

2. **必要な変更**:
   - src/api/routes/auth.py に新エンドポイント追加
   - src/models/user.py に reset_token フィールド追加
   - src/repositories/user.py に find_by_reset_token メソッド追加

3. **関連する既存コード**:
   [get_code_snippet: UserService.change_password]
   このメソッドのパターンを参考に実装できます...
```

---

## 6. パフォーマンス目標

| 指標 | 目標値 |
|------|--------|
| 初回インデックス (10万行) | < 30秒 |
| 増分インデックス | < 2秒 |
| クエリレスポンス | < 500ms |
| メモリ使用量 | < 500MB |
| ディスク使用量 | < 100MB per 10万行 |
| 起動時間 | < 2秒 |

---

## 7. 今後の拡張計画

1. **VS Code Extension**: 直接統合
2. **Web UI**: グラフ可視化ダッシュボード
3. **マルチリポジトリ**: モノレポ/マルチレポ対応
4. **リアルタイム更新**: LSP 統合
5. **コード生成**: テンプレートベースのコード生成支援

---

## 8. 参考資料

- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Microsoft GraphRAG](https://github.com/microsoft/graphrag)
- [code-graph-rag](https://github.com/vitali87/code-graph-rag)
- [Tree-sitter Documentation](https://tree-sitter.github.io/tree-sitter/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)