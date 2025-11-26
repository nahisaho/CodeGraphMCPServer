# CodeGraph MCP Server MCPインターフェース設計書

**Project**: CodeGraph MCP Server  
**Version**: 1.0.0  
**Created**: 2025-11-26  
**Status**: Draft  
**Document Type**: C4 Model - Component Diagram (Level 3)

---

## 1. ドキュメント概要

### 1.1 目的

本ドキュメントは、CodeGraph MCP ServerのMCPインターフェース層の詳細設計を記述します。

### 1.2 スコープ

- MCP Serverメイン設計
- Tools設計（14ツール）
- Resources設計（4タイプ）
- Prompts設計（6プロンプト）
- トランスポート設計

### 1.3 対象要件

| 要件グループ | 要件ID | 説明 |
|-------------|--------|------|
| トランスポート | REQ-TRP-001 ~ REQ-TRP-005 | MCP通信 |
| ツール | REQ-TLS-001 ~ REQ-TLS-014 | MCPツール |
| リソース | REQ-RSC-001 ~ REQ-RSC-004 | MCPリソース |
| プロンプト | REQ-PRM-001 ~ REQ-PRM-006 | MCPプロンプト |

---

## 2. MCPプロトコル概要

### 2.1 MCPアーキテクチャ

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           MCP Client                                     │
│                    (GitHub Copilot, Claude, Cursor)                     │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                          JSON-RPC 2.0 over Transport
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        CodeGraph MCP Server                              │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                      Transport Layer                               │ │
│  │                                                                    │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │ │
│  │  │   stdio     │  │    SSE      │  │   Streamable HTTP       │   │ │
│  │  │ REQ-TRP-001 │  │ REQ-TRP-002 │  │     REQ-TRP-003         │   │ │
│  │  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘   │ │
│  │         └────────────────┼─────────────────────┘                  │ │
│  │                          │                                        │ │
│  │                          ▼                                        │ │
│  │  ┌────────────────────────────────────────────────────────────┐  │ │
│  │  │              JSON-RPC 2.0 Handler (REQ-TRP-004)            │  │ │
│  │  └────────────────────────────────────────────────────────────┘  │ │
│  │                          │                                        │ │
│  └──────────────────────────┼────────────────────────────────────────┘ │
│                             │                                           │
│  ┌──────────────────────────▼────────────────────────────────────────┐ │
│  │                     MCP Interface Layer                            │ │
│  │                                                                    │ │
│  │  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐  │ │
│  │  │      Tools       │ │    Resources     │ │     Prompts      │  │ │
│  │  │   (14 tools)     │ │   (4 types)      │ │   (6 prompts)    │  │ │
│  │  │  REQ-TLS-001~014 │ │  REQ-RSC-001~004 │ │  REQ-PRM-001~006 │  │ │
│  │  └──────────────────┘ └──────────────────┘ └──────────────────┘  │ │
│  │                                                                    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 MCP Specification準拠

| 機能 | MCP仕様 | 対応バージョン |
|------|---------|---------------|
| Transport | stdio, SSE, HTTP | MCP 1.0 |
| Protocol | JSON-RPC 2.0 | MCP 1.0 |
| Capabilities | tools, resources, prompts | MCP 1.0 |
| Authentication | OAuth 2.1 (optional) | MCP 1.0 |

---

## 3. サーバーメイン設計

### 3.1 サーバークラス図

```
┌─────────────────────────────────────────────────────────────────┐
│                     CodeGraphServer                              │
├─────────────────────────────────────────────────────────────────┤
│ - _mcp_server: Server                                            │
│ - _graph_engine: GraphEngine                                     │
│ - _indexer: Indexer                                              │
│ - _semantic: SemanticAnalyzer                                    │
│ - _repo_path: str                                                │
│ - _config: ServerConfig                                          │
├─────────────────────────────────────────────────────────────────┤
│ + async start() -> None                                          │
│ + async stop() -> None                                           │
│ + async initialize(repo_path: str) -> None                      │
│ - _register_tools() -> None                                      │
│ - _register_resources() -> None                                  │
│ - _register_prompts() -> None                                    │
│ - _setup_handlers() -> None                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 サーバー初期化コード

```python
# server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, Resource, Prompt

class CodeGraphServer:
    """CodeGraph MCPサーバー"""
    
    def __init__(self, config: ServerConfig):
        self._config = config
        self._mcp_server = Server("codegraph-mcp")
        self._graph_engine = None
        self._indexer = None
        self._semantic = None
        self._repo_path = None
    
    async def initialize(self, repo_path: str) -> None:
        """サーバーを初期化 (REQ-IDX-001)"""
        self._repo_path = repo_path
        
        # コアエンジン初期化
        self._graph_engine = GraphEngine()
        await self._graph_engine.connect(
            self._get_db_path(repo_path)
        )
        
        self._indexer = Indexer(
            graph_engine=self._graph_engine
        )
        
        self._semantic = SemanticAnalyzer(
            graph_engine=self._graph_engine
        )
        
        # インデックス作成/読み込み
        await self._indexer.index_repository(
            repo_path, 
            incremental=True
        )
        
        # MCPハンドラー登録
        self._register_tools()
        self._register_resources()
        self._register_prompts()
    
    async def start(self) -> None:
        """サーバーを起動 (REQ-TRP-001)"""
        async with stdio_server() as (read_stream, write_stream):
            await self._mcp_server.run(
                read_stream,
                write_stream,
                self._mcp_server.create_initialization_options()
            )
    
    async def stop(self) -> None:
        """サーバーを停止"""
        if self._graph_engine:
            await self._graph_engine.close()
```

### 3.3 CLIエントリーポイント

```python
# __main__.py - REQ-CLI-001~004
import click
import asyncio

@click.group()
@click.version_option()
def cli():
    """CodeGraph MCP Server - ソースコードグラフ分析MCPサーバー"""
    pass

@cli.command()
@click.option('--repo', '-r', required=True, help='リポジトリパス')
@click.option('--port', '-p', default=None, type=int, help='SSEポート（オプション）')
@click.option('--verbose', '-v', is_flag=True, help='詳細ログ出力')
def serve(repo: str, port: int | None, verbose: bool):
    """MCPサーバーを起動 (REQ-CLI-001, REQ-CLI-002)"""
    config = ServerConfig(
        repo_path=repo,
        sse_port=port,
        verbose=verbose
    )
    
    server = CodeGraphServer(config)
    
    async def main():
        await server.initialize(repo)
        await server.start()
    
    asyncio.run(main())

@cli.command()
@click.argument('repo_path')
@click.option('--full', is_flag=True, help='完全再インデックス')
def index(repo_path: str, full: bool):
    """リポジトリをインデックス"""
    async def main():
        indexer = Indexer()
        result = await indexer.index_repository(
            repo_path, 
            incremental=not full
        )
        click.echo(f"Indexed {result.indexed_files} files")
        click.echo(f"Entities: {result.total_entities}")
        click.echo(f"Relations: {result.total_relations}")
    
    asyncio.run(main())

@cli.command()
def help():
    """ヘルプを表示 (REQ-CLI-003)"""
    click.echo(cli.get_help(click.Context(cli)))

if __name__ == "__main__":
    cli()
```

---

## 4. Tools設計

### 4.1 ツール一覧

| カテゴリ | ツール名 | 要件ID | Phase |
|----------|---------|--------|-------|
| グラフクエリ | query_codebase | REQ-TLS-001 | P0 |
| グラフクエリ | find_dependencies | REQ-TLS-002 | P0 |
| グラフクエリ | find_callers | REQ-TLS-003 | P0 |
| グラフクエリ | find_callees | REQ-TLS-004 | P0 |
| グラフクエリ | find_implementations | REQ-TLS-005 | P0 |
| グラフクエリ | analyze_module_structure | REQ-TLS-006 | P0 |
| コード取得 | get_code_snippet | REQ-TLS-007 | P0 |
| コード取得 | read_file_content | REQ-TLS-008 | P0 |
| コード取得 | get_file_structure | REQ-TLS-009 | P0 |
| GraphRAG | global_search | REQ-TLS-010 | P1 |
| GraphRAG | local_search | REQ-TLS-011 | P1 |
| 編集・管理 | suggest_refactoring | REQ-TLS-012 | P2 |
| 編集・管理 | reindex_repository | REQ-TLS-013 | P0 |
| 編集・管理 | execute_shell_command | REQ-TLS-014 | P1 |

### 4.2 ツールスキーマ定義

```python
# mcp/tools.py

from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field
from typing import Literal, Optional

# ====== Input Schemas ======

class QueryCodebaseInput(BaseModel):
    """query_codebase ツール入力スキーマ (REQ-TLS-001)"""
    query: str = Field(..., description="自然言語クエリ")
    scope: Literal["all", "functions", "classes", "files"] = Field(
        default="all", 
        description="検索スコープ"
    )
    limit: int = Field(default=20, ge=1, le=100, description="結果数上限")

class FindDependenciesInput(BaseModel):
    """find_dependencies ツール入力スキーマ (REQ-TLS-002)"""
    entity_name: str = Field(..., description="エンティティ名")
    direction: Literal["upstream", "downstream", "both"] = Field(
        default="both", 
        description="依存方向"
    )
    depth: int = Field(default=3, ge=1, le=10, description="探索深さ")

class FindCallersInput(BaseModel):
    """find_callers ツール入力スキーマ (REQ-TLS-003)"""
    function_name: str = Field(..., description="関数名")
    max_depth: int = Field(default=3, ge=1, le=10, description="最大深さ")

class FindCalleesInput(BaseModel):
    """find_callees ツール入力スキーマ (REQ-TLS-004)"""
    function_name: str = Field(..., description="関数名")
    max_depth: int = Field(default=3, ge=1, le=10, description="最大深さ")

class FindImplementationsInput(BaseModel):
    """find_implementations ツール入力スキーマ (REQ-TLS-005)"""
    interface_name: str = Field(..., description="インターフェース/抽象クラス名")

class AnalyzeModuleInput(BaseModel):
    """analyze_module_structure ツール入力スキーマ (REQ-TLS-006)"""
    module_path: str = Field(..., description="モジュールパス")

class GetCodeSnippetInput(BaseModel):
    """get_code_snippet ツール入力スキーマ (REQ-TLS-007)"""
    entity_name: str = Field(..., description="エンティティ名")
    include_context: bool = Field(default=False, description="前後のコンテキストを含める")
    context_lines: int = Field(default=5, ge=0, le=20, description="コンテキスト行数")

class ReadFileContentInput(BaseModel):
    """read_file_content ツール入力スキーマ (REQ-TLS-008)"""
    file_path: str = Field(..., description="ファイルパス")
    start_line: Optional[int] = Field(None, ge=1, description="開始行")
    end_line: Optional[int] = Field(None, ge=1, description="終了行")

class GetFileStructureInput(BaseModel):
    """get_file_structure ツール入力スキーマ (REQ-TLS-009)"""
    file_path: str = Field(..., description="ファイルパス")

class GlobalSearchInput(BaseModel):
    """global_search ツール入力スキーマ (REQ-TLS-010)"""
    query: str = Field(..., description="検索クエリ")
    community_level: int = Field(default=0, ge=0, le=2, description="コミュニティレベル")

class LocalSearchInput(BaseModel):
    """local_search ツール入力スキーマ (REQ-TLS-011)"""
    query: str = Field(..., description="検索クエリ")
    context_entities: list[str] = Field(default=[], description="コンテキストエンティティ")

class SuggestRefactoringInput(BaseModel):
    """suggest_refactoring ツール入力スキーマ (REQ-TLS-012)"""
    entity_name: str = Field(..., description="対象エンティティ名")
    refactoring_type: Literal[
        "extract_method", "rename", "move", "inline", "general"
    ] = Field(default="general", description="リファクタリングタイプ")

class ReindexRepositoryInput(BaseModel):
    """reindex_repository ツール入力スキーマ (REQ-TLS-013)"""
    path: Optional[str] = Field(None, description="リポジトリパス（省略時は現在のリポジトリ）")
    incremental: bool = Field(default=True, description="増分インデックス")

class ExecuteShellCommandInput(BaseModel):
    """execute_shell_command ツール入力スキーマ (REQ-TLS-014)"""
    command: str = Field(..., description="実行コマンド")
    working_directory: Optional[str] = Field(None, description="作業ディレクトリ")
    timeout: int = Field(default=30, ge=1, le=300, description="タイムアウト秒数")
```

### 4.3 ツール実装

```python
# mcp/tools.py

class ToolHandlers:
    """MCPツールハンドラー"""
    
    def __init__(
        self, 
        graph_engine: GraphEngine,
        indexer: Indexer,
        semantic: SemanticAnalyzer,
        repo_path: str
    ):
        self._graph = graph_engine
        self._indexer = indexer
        self._semantic = semantic
        self._repo_path = repo_path
    
    def register(self, server: Server) -> None:
        """ツールを登録"""
        
        # ====== グラフクエリツール ======
        
        @server.tool()
        async def query_codebase(
            query: str,
            scope: str = "all",
            limit: int = 20
        ) -> list[TextContent]:
            """
            コードベースを自然言語でクエリ (REQ-TLS-001)
            
            Args:
                query: 検索クエリ（例: "認証を処理する関数"）
                scope: 検索スコープ（all, functions, classes, files）
                limit: 結果数上限
            
            Returns:
                マッチしたコードエンティティのリスト
            """
            result = await self._graph.query(GraphQuery(
                type="search",
                search_text=query,
                entity_types=[scope] if scope != "all" else None,
                limit=limit
            ))
            
            return [TextContent(
                type="text",
                text=self._format_entities(result.entities)
            )]
        
        @server.tool()
        async def find_dependencies(
            entity_name: str,
            direction: str = "both",
            depth: int = 3
        ) -> list[TextContent]:
            """
            依存関係を検索 (REQ-TLS-002)
            
            Args:
                entity_name: エンティティ名
                direction: 依存方向（upstream, downstream, both）
                depth: 探索深さ
            
            Returns:
                依存関係グラフ
            """
            deps = await self._graph.find_dependencies(
                entity_name, direction, depth
            )
            
            return [TextContent(
                type="text",
                text=self._format_dependencies(deps)
            )]
        
        @server.tool()
        async def find_callers(
            function_name: str,
            max_depth: int = 3
        ) -> list[TextContent]:
            """
            関数の呼び出し元を検索 (REQ-TLS-003)
            
            Args:
                function_name: 関数名
                max_depth: 最大探索深さ
            
            Returns:
                呼び出し元の関数リストと呼び出しパス
            """
            callers = await self._graph.find_callers(
                function_name, max_depth
            )
            
            return [TextContent(
                type="text",
                text=self._format_call_paths(callers, "callers")
            )]
        
        @server.tool()
        async def find_callees(
            function_name: str,
            max_depth: int = 3
        ) -> list[TextContent]:
            """
            関数の呼び出し先を検索 (REQ-TLS-004)
            
            Args:
                function_name: 関数名
                max_depth: 最大探索深さ
            
            Returns:
                呼び出し先の関数リストと呼び出しパス
            """
            callees = await self._graph.find_callees(
                function_name, max_depth
            )
            
            return [TextContent(
                type="text",
                text=self._format_call_paths(callees, "callees")
            )]
        
        @server.tool()
        async def find_implementations(
            interface_name: str
        ) -> list[TextContent]:
            """
            インターフェースの実装を検索 (REQ-TLS-005)
            
            Args:
                interface_name: インターフェース/抽象クラス名
            
            Returns:
                実装クラスのリスト
            """
            impls = await self._graph.find_implementations(interface_name)
            
            return [TextContent(
                type="text",
                text=self._format_implementations(impls)
            )]
        
        @server.tool()
        async def analyze_module_structure(
            module_path: str
        ) -> list[TextContent]:
            """
            モジュール構造を分析 (REQ-TLS-006)
            
            Args:
                module_path: モジュールパス
            
            Returns:
                モジュールの構造分析結果
            """
            analysis = await self._graph.analyze_module(module_path)
            
            return [TextContent(
                type="text",
                text=self._format_module_analysis(analysis)
            )]
        
        # ====== コード取得ツール ======
        
        @server.tool()
        async def get_code_snippet(
            entity_name: str,
            include_context: bool = False,
            context_lines: int = 5
        ) -> list[TextContent]:
            """
            コードスニペットを取得 (REQ-TLS-007)
            
            Args:
                entity_name: エンティティ名
                include_context: 前後のコンテキストを含める
                context_lines: コンテキスト行数
            
            Returns:
                ソースコード
            """
            entity = await self._graph.get_entity_by_name(entity_name)
            if not entity:
                return [TextContent(
                    type="text",
                    text=f"Entity not found: {entity_name}"
                )]
            
            code = entity.source_code
            if include_context:
                code = await self._get_code_with_context(
                    entity, context_lines
                )
            
            return [TextContent(
                type="text",
                text=f"```{self._detect_lang(entity.file_path)}\n{code}\n```"
            )]
        
        @server.tool()
        async def read_file_content(
            file_path: str,
            start_line: int | None = None,
            end_line: int | None = None
        ) -> list[TextContent]:
            """
            ファイル内容を読み取り (REQ-TLS-008)
            
            Args:
                file_path: ファイルパス
                start_line: 開始行（オプション）
                end_line: 終了行（オプション）
            
            Returns:
                ファイル内容
            """
            # セキュリティチェック (REQ-NFR-013)
            if not self._is_allowed_path(file_path):
                return [TextContent(
                    type="text",
                    text=f"Access denied: {file_path}"
                )]
            
            content = await self._read_file(
                file_path, start_line, end_line
            )
            
            return [TextContent(
                type="text",
                text=content
            )]
        
        @server.tool()
        async def get_file_structure(
            file_path: str
        ) -> list[TextContent]:
            """
            ファイル構造を取得 (REQ-TLS-009)
            
            Args:
                file_path: ファイルパス
            
            Returns:
                ファイル内のクラス・関数の構造情報
            """
            entities = await self._graph.get_entities_by_file(file_path)
            
            return [TextContent(
                type="text",
                text=self._format_file_structure(entities)
            )]
        
        # ====== GraphRAGツール (Phase 2) ======
        
        @server.tool()
        async def global_search(
            query: str,
            community_level: int = 0
        ) -> list[TextContent]:
            """
            グローバル検索（コミュニティサマリー使用）(REQ-TLS-010)
            
            Args:
                query: 検索クエリ
                community_level: コミュニティレベル（0=細粒度、1=粗粒度）
            
            Returns:
                コードベース全体に関するマクロレベルの回答
            """
            result = await self._semantic.global_search(
                query, community_level
            )
            
            return [TextContent(
                type="text",
                text=result
            )]
        
        @server.tool()
        async def local_search(
            query: str,
            context_entities: list[str] = []
        ) -> list[TextContent]:
            """
            ローカル検索（グラフ構造使用）(REQ-TLS-011)
            
            Args:
                query: 検索クエリ
                context_entities: コンテキストエンティティ名のリスト
            
            Returns:
                詳細な回答
            """
            result = await self._semantic.local_search(
                query, context_entities
            )
            
            return [TextContent(
                type="text",
                text=result
            )]
        
        # ====== 編集・管理ツール ======
        
        @server.tool()
        async def suggest_refactoring(
            entity_name: str,
            refactoring_type: str = "general"
        ) -> list[TextContent]:
            """
            リファクタリング提案 (REQ-TLS-012)
            
            Args:
                entity_name: 対象エンティティ名
                refactoring_type: リファクタリングタイプ
            
            Returns:
                リファクタリング提案と影響範囲分析
            """
            suggestion = await self._semantic.suggest_refactoring(
                entity_name, refactoring_type
            )
            
            return [TextContent(
                type="text",
                text=suggestion
            )]
        
        @server.tool()
        async def reindex_repository(
            path: str | None = None,
            incremental: bool = True
        ) -> list[TextContent]:
            """
            リポジトリを再インデックス (REQ-TLS-013)
            
            Args:
                path: リポジトリパス（省略時は現在のリポジトリ）
                incremental: 増分インデックス
            
            Returns:
                インデックス結果
            """
            repo_path = path or self._repo_path
            result = await self._indexer.index_repository(
                repo_path, incremental
            )
            
            return [TextContent(
                type="text",
                text=self._format_index_result(result)
            )]
        
        @server.tool()
        async def execute_shell_command(
            command: str,
            working_directory: str | None = None,
            timeout: int = 30
        ) -> list[TextContent]:
            """
            シェルコマンドを実行 (REQ-TLS-014)
            
            Args:
                command: 実行コマンド
                working_directory: 作業ディレクトリ
                timeout: タイムアウト秒数
            
            Returns:
                コマンド実行結果
            """
            # セキュリティチェック (REQ-NFR-012)
            cwd = working_directory or self._repo_path
            if not self._is_allowed_path(cwd):
                return [TextContent(
                    type="text",
                    text=f"Access denied: {cwd}"
                )]
            
            try:
                result = await asyncio.wait_for(
                    self._execute_command(command, cwd),
                    timeout=timeout
                )
                return [TextContent(type="text", text=result)]
            except asyncio.TimeoutError:
                return [TextContent(
                    type="text",
                    text=f"Command timed out after {timeout}s"
                )]
```

---

## 5. Resources設計

### 5.1 リソース一覧

| URI パターン | 要件ID | 説明 | Phase |
|-------------|--------|------|-------|
| codegraph://entities/{entity_id} | REQ-RSC-001 | エンティティ詳細 | P0 |
| codegraph://files/{file_path} | REQ-RSC-002 | ファイル情報 | P0 |
| codegraph://communities/{community_id} | REQ-RSC-003 | コミュニティ情報 | P1 |
| codegraph://stats | REQ-RSC-004 | 統計情報 | P0 |

### 5.2 リソーススキーマ

```python
# mcp/resources.py

from mcp.types import Resource, TextResourceContents
from typing import Optional

# ====== Response Schemas ======

class EntityResource(BaseModel):
    """エンティティリソース (REQ-RSC-001)"""
    id: str
    type: str
    name: str
    qualified_name: str
    file_path: str
    start_line: int
    end_line: int
    signature: Optional[str]
    docstring: Optional[str]
    source_code: Optional[str]
    community_id: Optional[int]
    relations: list[dict]  # {type, target_id, target_name}

class FileResource(BaseModel):
    """ファイルリソース (REQ-RSC-002)"""
    path: str
    language: str
    size_bytes: int
    line_count: int
    entities: list[dict]  # {type, name, start_line, end_line}
    imports: list[str]

class CommunityResource(BaseModel):
    """コミュニティリソース (REQ-RSC-003)"""
    id: int
    level: int
    name: Optional[str]
    summary: Optional[str]
    member_count: int
    members: list[dict]  # {id, type, name}
    top_entities: list[dict]

class StatsResource(BaseModel):
    """統計リソース (REQ-RSC-004)"""
    total_files: int
    total_entities: int
    total_relations: int
    entity_breakdown: dict[str, int]  # {type: count}
    language_breakdown: dict[str, int]  # {lang: count}
    last_indexed_at: str
    index_duration_ms: float
```

### 5.3 リソース実装

```python
# mcp/resources.py

class ResourceHandlers:
    """MCPリソースハンドラー"""
    
    def __init__(
        self,
        graph_engine: GraphEngine,
        repo_path: str
    ):
        self._graph = graph_engine
        self._repo_path = repo_path
    
    def register(self, server: Server) -> None:
        """リソースを登録"""
        
        @server.list_resources()
        async def list_resources() -> list[Resource]:
            """利用可能なリソースをリスト"""
            return [
                Resource(
                    uri="codegraph://stats",
                    name="Codebase Statistics",
                    mimeType="application/json",
                    description="コードベースの統計情報"
                ),
                # 動的リソースはテンプレートとして提供
                Resource(
                    uri="codegraph://entities/{entity_id}",
                    name="Entity Details",
                    mimeType="application/json",
                    description="エンティティの詳細情報"
                ),
                Resource(
                    uri="codegraph://files/{file_path}",
                    name="File Information",
                    mimeType="application/json",
                    description="ファイルの構造情報"
                ),
                Resource(
                    uri="codegraph://communities/{community_id}",
                    name="Community Summary",
                    mimeType="application/json",
                    description="コミュニティの要約"
                ),
            ]
        
        @server.read_resource()
        async def read_resource(uri: str) -> TextResourceContents:
            """リソースを読み取り"""
            
            # codegraph://stats (REQ-RSC-004)
            if uri == "codegraph://stats":
                stats = await self._graph.get_stats()
                return TextResourceContents(
                    uri=uri,
                    mimeType="application/json",
                    text=stats.model_dump_json(indent=2)
                )
            
            # codegraph://entities/{entity_id} (REQ-RSC-001)
            if uri.startswith("codegraph://entities/"):
                entity_id = uri.split("/")[-1]
                entity = await self._graph.get_entity(entity_id)
                if not entity:
                    raise ValueError(f"Entity not found: {entity_id}")
                
                relations = await self._graph.get_entity_relations(entity_id)
                resource = EntityResource(
                    **entity.__dict__,
                    relations=[r.__dict__ for r in relations]
                )
                return TextResourceContents(
                    uri=uri,
                    mimeType="application/json",
                    text=resource.model_dump_json(indent=2)
                )
            
            # codegraph://files/{file_path} (REQ-RSC-002)
            if uri.startswith("codegraph://files/"):
                file_path = uri.replace("codegraph://files/", "")
                entities = await self._graph.get_entities_by_file(file_path)
                
                resource = FileResource(
                    path=file_path,
                    language=self._detect_language(file_path),
                    size_bytes=os.path.getsize(file_path),
                    line_count=self._count_lines(file_path),
                    entities=[{
                        "type": e.type.value,
                        "name": e.name,
                        "start_line": e.start_line,
                        "end_line": e.end_line
                    } for e in entities],
                    imports=self._extract_imports(entities)
                )
                return TextResourceContents(
                    uri=uri,
                    mimeType="application/json",
                    text=resource.model_dump_json(indent=2)
                )
            
            # codegraph://communities/{community_id} (REQ-RSC-003)
            if uri.startswith("codegraph://communities/"):
                community_id = int(uri.split("/")[-1])
                community = await self._graph.get_community(community_id)
                if not community:
                    raise ValueError(f"Community not found: {community_id}")
                
                members = await self._graph.get_community_members(community_id)
                resource = CommunityResource(
                    **community.__dict__,
                    members=[{
                        "id": m.id,
                        "type": m.type.value,
                        "name": m.name
                    } for m in members],
                    top_entities=members[:10]
                )
                return TextResourceContents(
                    uri=uri,
                    mimeType="application/json",
                    text=resource.model_dump_json(indent=2)
                )
            
            raise ValueError(f"Unknown resource: {uri}")
```

---

## 6. Prompts設計

### 6.1 プロンプト一覧

| プロンプト名 | 要件ID | 説明 | Phase |
|-------------|--------|------|-------|
| code_review | REQ-PRM-001 | コードレビュー支援 | P1 |
| explain_codebase | REQ-PRM-002 | コードベース説明 | P1 |
| implement_feature | REQ-PRM-003 | 機能実装ガイダンス | P1 |
| debug_issue | REQ-PRM-004 | デバッグ支援 | P1 |
| refactor_guidance | REQ-PRM-005 | リファクタリングガイダンス | P2 |
| test_generation | REQ-PRM-006 | テスト生成支援 | P1 |

### 6.2 プロンプト実装

```python
# mcp/prompts.py

from mcp.types import Prompt, PromptMessage, PromptArgument
from mcp.types import TextContent

class PromptHandlers:
    """MCPプロンプトハンドラー"""
    
    def __init__(
        self,
        graph_engine: GraphEngine,
        repo_path: str
    ):
        self._graph = graph_engine
        self._repo_path = repo_path
    
    def register(self, server: Server) -> None:
        """プロンプトを登録"""
        
        @server.list_prompts()
        async def list_prompts() -> list[Prompt]:
            """利用可能なプロンプトをリスト"""
            return [
                Prompt(
                    name="code_review",
                    description="指定ファイルのコードレビューを実施",
                    arguments=[
                        PromptArgument(
                            name="file_path",
                            description="レビュー対象ファイルパス",
                            required=True
                        ),
                        PromptArgument(
                            name="focus_areas",
                            description="重点領域（security, performance, readability）",
                            required=False
                        )
                    ]
                ),
                Prompt(
                    name="explain_codebase",
                    description="コードベース全体の説明を生成",
                    arguments=[]
                ),
                Prompt(
                    name="implement_feature",
                    description="新機能実装のガイダンスを提供",
                    arguments=[
                        PromptArgument(
                            name="feature_description",
                            description="実装したい機能の説明",
                            required=True
                        )
                    ]
                ),
                Prompt(
                    name="debug_issue",
                    description="デバッグ支援プロンプト",
                    arguments=[
                        PromptArgument(
                            name="error_message",
                            description="エラーメッセージ",
                            required=True
                        ),
                        PromptArgument(
                            name="context",
                            description="追加コンテキスト",
                            required=False
                        )
                    ]
                ),
                Prompt(
                    name="refactor_guidance",
                    description="リファクタリングガイダンス",
                    arguments=[
                        PromptArgument(
                            name="target_entity",
                            description="リファクタリング対象",
                            required=True
                        )
                    ]
                ),
                Prompt(
                    name="test_generation",
                    description="テストコード生成支援",
                    arguments=[
                        PromptArgument(
                            name="function_name",
                            description="テスト対象関数名",
                            required=True
                        )
                    ]
                ),
            ]
        
        @server.get_prompt()
        async def get_prompt(
            name: str, 
            arguments: dict[str, str] | None = None
        ) -> list[PromptMessage]:
            """プロンプトを取得"""
            arguments = arguments or {}
            
            # code_review (REQ-PRM-001)
            if name == "code_review":
                return await self._get_code_review_prompt(
                    arguments.get("file_path", ""),
                    arguments.get("focus_areas", "")
                )
            
            # explain_codebase (REQ-PRM-002)
            elif name == "explain_codebase":
                return await self._get_explain_codebase_prompt()
            
            # implement_feature (REQ-PRM-003)
            elif name == "implement_feature":
                return await self._get_implement_feature_prompt(
                    arguments.get("feature_description", "")
                )
            
            # debug_issue (REQ-PRM-004)
            elif name == "debug_issue":
                return await self._get_debug_issue_prompt(
                    arguments.get("error_message", ""),
                    arguments.get("context", "")
                )
            
            # refactor_guidance (REQ-PRM-005)
            elif name == "refactor_guidance":
                return await self._get_refactor_guidance_prompt(
                    arguments.get("target_entity", "")
                )
            
            # test_generation (REQ-PRM-006)
            elif name == "test_generation":
                return await self._get_test_generation_prompt(
                    arguments.get("function_name", "")
                )
            
            else:
                raise ValueError(f"Unknown prompt: {name}")
    
    # ====== プロンプトテンプレート ======
    
    async def _get_code_review_prompt(
        self, 
        file_path: str,
        focus_areas: str
    ) -> list[PromptMessage]:
        """コードレビュープロンプト (REQ-PRM-001)"""
        # ファイル情報を取得
        entities = await self._graph.get_entities_by_file(file_path)
        file_content = self._read_file(file_path)
        
        structure_info = "\n".join([
            f"- {e.type.value}: {e.name} (lines {e.start_line}-{e.end_line})"
            for e in entities
        ])
        
        focus = focus_areas or "general quality, bugs, and improvements"
        
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"""以下のファイルのコードレビューを実施してください。

## 対象ファイル
**パス**: {file_path}

## ファイル構造
{structure_info}

## レビュー重点領域
{focus}

## ソースコード
```
{file_content}
```

## レビュー観点
1. バグや潜在的な問題
2. コード品質（可読性、保守性）
3. パフォーマンス
4. セキュリティ
5. ベストプラクティス

詳細なレビューコメントを提供してください。各指摘には行番号と改善提案を含めてください。
"""
                )
            )
        ]
    
    async def _get_explain_codebase_prompt(self) -> list[PromptMessage]:
        """コードベース説明プロンプト (REQ-PRM-002)"""
        stats = await self._graph.get_stats()
        
        # 主要コンポーネントを取得
        top_modules = await self._graph.get_top_modules(limit=10)
        module_info = "\n".join([
            f"- {m.name}: {m.description or 'No description'}"
            for m in top_modules
        ])
        
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"""このコードベースについて説明してください。

## 統計情報
- 総ファイル数: {stats.total_files}
- 総エンティティ数: {stats.total_entities}
- 言語内訳: {stats.language_breakdown}

## 主要モジュール
{module_info}

## 説明してほしいこと
1. このプロジェクトの目的と主要機能
2. アーキテクチャの概要
3. 主要なコンポーネントとその役割
4. データフローの概要
5. 重要な依存関係

初めて見る開発者にも理解できるよう、構造化された説明を提供してください。
"""
                )
            )
        ]
    
    async def _get_implement_feature_prompt(
        self, 
        feature_description: str
    ) -> list[PromptMessage]:
        """機能実装ガイダンスプロンプト (REQ-PRM-003)"""
        # 関連しそうなエンティティを検索
        related = await self._graph.query(GraphQuery(
            type="search",
            search_text=feature_description,
            limit=10
        ))
        
        related_info = "\n".join([
            f"- {e.type.value}: {e.qualified_name} ({e.file_path})"
            for e in related.entities
        ])
        
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"""以下の機能を実装するためのガイダンスを提供してください。

## 機能説明
{feature_description}

## 関連する既存コード
{related_info}

## 提供してほしい情報
1. 実装アプローチの提案
2. 変更が必要なファイル
3. 新規作成が必要なファイル
4. 影響を受ける既存機能
5. テスト戦略
6. 実装の優先順位と手順

コードベースのアーキテクチャに沿った実装方法を提案してください。
"""
                )
            )
        ]
    
    async def _get_debug_issue_prompt(
        self, 
        error_message: str,
        context: str
    ) -> list[PromptMessage]:
        """デバッグ支援プロンプト (REQ-PRM-004)"""
        # エラーメッセージから関連ファイル/関数を抽出
        related = await self._extract_error_context(error_message)
        
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"""以下のエラーのデバッグを支援してください。

## エラーメッセージ
```
{error_message}
```

## 追加コンテキスト
{context or "なし"}

## 関連コード
{related}

## 支援してほしいこと
1. エラーの原因分析
2. 調査すべきファイル/関数
3. デバッグ手順の提案
4. 修正案
5. 再発防止策

ステップバイステップでデバッグを進められるよう支援してください。
"""
                )
            )
        ]
    
    async def _get_test_generation_prompt(
        self, 
        function_name: str
    ) -> list[PromptMessage]:
        """テスト生成支援プロンプト (REQ-PRM-006)"""
        # 関数情報を取得
        entity = await self._graph.get_entity_by_name(function_name)
        if not entity:
            return [PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"Function not found: {function_name}"
                )
            )]
        
        # 依存関係を取得
        deps = await self._graph.find_callees(function_name, max_depth=1)
        
        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"""以下の関数のテストコードを生成してください。

## 対象関数
**名前**: {entity.name}
**ファイル**: {entity.file_path}
**シグネチャ**: {entity.signature or "N/A"}

## ソースコード
```
{entity.source_code}
```

## 依存関係（呼び出している関数）
{self._format_deps(deps)}

## 生成してほしいテスト
1. 正常系テスト
2. 異常系テスト（境界値、エラー処理）
3. モックが必要な場合はモックの設定
4. テストケースの説明コメント

pytest形式でテストコードを生成してください。
"""
                )
            )
        ]
```

---

## 7. トランスポート設計

### 7.1 トランスポート構成

```python
# transports.py

class TransportConfig(BaseModel):
    """トランスポート設定"""
    type: Literal["stdio", "sse", "http"] = "stdio"
    host: str = "localhost"
    port: int = 8080
    ssl: bool = False

class TransportFactory:
    """トランスポートファクトリー"""
    
    @staticmethod
    async def create(
        config: TransportConfig,
        server: Server
    ) -> AsyncContextManager:
        """トランスポートを作成"""
        
        if config.type == "stdio":
            # stdio トランスポート (REQ-TRP-001)
            return stdio_server()
        
        elif config.type == "sse":
            # SSE トランスポート (REQ-TRP-002)
            return sse_server(
                host=config.host,
                port=config.port
            )
        
        elif config.type == "http":
            # Streamable HTTP トランスポート (REQ-TRP-003)
            return http_server(
                host=config.host,
                port=config.port,
                ssl=config.ssl
            )
        
        else:
            raise ValueError(f"Unknown transport type: {config.type}")
```

### 7.2 JSON-RPC 2.0ハンドリング

```python
# server.py - REQ-TRP-004

class JsonRpcHandler:
    """JSON-RPC 2.0メッセージハンドラー"""
    
    async def handle_message(
        self, 
        message: dict
    ) -> dict:
        """メッセージを処理"""
        
        # バリデーション
        if "jsonrpc" not in message or message["jsonrpc"] != "2.0":
            return self._error_response(
                None, -32600, "Invalid Request"
            )
        
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        try:
            # メソッド実行
            result = await self._dispatch(method, params)
            
            if msg_id is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": result
                }
            return None  # Notification
            
        except Exception as e:
            return self._error_response(
                msg_id, -32603, str(e)
            )
    
    def _error_response(
        self, 
        msg_id: int | None,
        code: int,
        message: str
    ) -> dict:
        """エラーレスポンスを作成"""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": code,
                "message": message
            }
        }
```

---

## 8. エラーハンドリング

### 8.1 エラーコード定義

```python
# errors.py

from enum import IntEnum

class ErrorCode(IntEnum):
    """MCPエラーコード"""
    # JSON-RPC標準エラー
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # カスタムエラー
    ENTITY_NOT_FOUND = -32001
    FILE_NOT_FOUND = -32002
    ACCESS_DENIED = -32003
    TIMEOUT = -32004
    INDEX_ERROR = -32005

class CodeGraphError(Exception):
    """CodeGraphエラー基底クラス"""
    def __init__(self, code: ErrorCode, message: str, data: dict = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)

class EntityNotFoundError(CodeGraphError):
    def __init__(self, entity_name: str):
        super().__init__(
            ErrorCode.ENTITY_NOT_FOUND,
            f"Entity not found: {entity_name}",
            {"entity_name": entity_name}
        )

class AccessDeniedError(CodeGraphError):
    def __init__(self, path: str):
        super().__init__(
            ErrorCode.ACCESS_DENIED,
            f"Access denied: {path}",
            {"path": path}
        )
```

---

## 9. 要件トレーサビリティ

### 9.1 コンポーネント → 要件マッピング

| コンポーネント | ファイル | 要件ID | Phase |
|---------------|---------|--------|-------|
| Server Main | server.py | REQ-TRP-001~005, REQ-CLI-001~004 | P0 |
| Tools: Graph Query | mcp/tools.py | REQ-TLS-001~006 | P0 |
| Tools: Code Fetch | mcp/tools.py | REQ-TLS-007~009 | P0 |
| Tools: GraphRAG | mcp/tools.py | REQ-TLS-010~011 | P1 |
| Tools: Management | mcp/tools.py | REQ-TLS-012~014 | P1/P2 |
| Resources | mcp/resources.py | REQ-RSC-001~004 | P0/P1 |
| Prompts | mcp/prompts.py | REQ-PRM-001~006 | P1/P2 |

---

## 10. 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|------------|------|----------|--------|
| 1.0.0 | 2025-11-26 | 初版作成 | System |

---

**Document Status**: Draft  
**Constitutional Compliance**: Article II (CLI Interface), Article VIII (No Abstraction) ✓
