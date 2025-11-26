# CodeGraphMCPServer 使用例

このドキュメントでは、CodeGraphMCPServerの実践的な使用例を紹介します。

## 目次

- [クイックスタート](#クイックスタート)
- [CLI使用例](#cli使用例)
- [AIアシスタント連携例](#aiアシスタント連携例)
- [Pythonからの利用](#pythonからの利用)
- [MCPクライアントからの利用](#mcpクライアントからの利用)
- [実践的なユースケース](#実践的なユースケース)

---

## クイックスタート

### 1. インストール

```bash
pip install codegraph-mcp
```

### 2. リポジトリをインデックス

```bash
codegraph-mcp index /path/to/your/project --full
```

### 3. MCPサーバーを起動

```bash
codegraph-mcp serve --repo /path/to/your/project
```

### 4. Claude DesktopまたはVS Codeで接続

設定ファイルに以下を追加：

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

---

## CLI使用例

### インデックス作成

```bash
# フルインデックス
codegraph-mcp index /path/to/project --full

# 増分インデックス（変更ファイルのみ）
codegraph-mcp index /path/to/project

# 言語を指定
codegraph-mcp index /path/to/project --languages python,typescript
```

**出力例:**
```
Indexing /path/to/project...
Processing: src/services/auth.py
Processing: src/services/user.py
Processing: src/models/user.py
...

Indexed 256 entities, 512 relations in 2.35s
```

### 統計情報の確認

```bash
codegraph-mcp stats /path/to/project
```

**出力例:**
```
Repository Statistics
=====================
Repository: /path/to/project

Entities: 256
Relations: 512
Communities: 8
Files: 45

Entities by type:
  - class: 45
  - function: 120
  - method: 85
  - module: 6

Relations by type:
  - calls: 280
  - contains: 150
  - imports: 52
  - implements: 30
```

### コード検索

```bash
# 自然言語検索
codegraph-mcp query "認証処理" --repo /path/to/project

# エンティティ名で検索
codegraph-mcp query "UserService" --repo /path/to/project --max-results 5
```

**出力例:**
```
Search Results for "UserService"
================================

1. class UserService (src/services/user.py:10-150)
   Service for managing user operations

2. method UserService.create_user (src/services/user.py:25-45)
   Create a new user account

3. method UserService.update_user (src/services/user.py:47-70)
   Update existing user information
```

### サーバー起動

```bash
# stdio トランスポート（デフォルト）
codegraph-mcp serve --repo /path/to/project

# SSE トランスポート（HTTPベース）
codegraph-mcp serve --repo /path/to/project --transport sse --port 8080

# デバッグモード
CODEGRAPH_LOG_LEVEL=DEBUG codegraph-mcp serve --repo /path/to/project
```

---

## AIアシスタント連携例

### 依存関係の調査

**ユーザー:**
> UserServiceクラスの依存関係を教えて

**AI（find_dependenciesツールを使用）:**
> UserServiceは以下のクラス/モジュールに依存しています：
> 
> 1. **DatabaseConnection** (src/database/connection.py)
>    - データベース接続管理
> 2. **UserRepository** (src/repositories/user.py)
>    - ユーザーデータのCRUD操作
> 3. **Logger** (src/utils/logging.py)
>    - ログ出力
> 4. **PasswordHasher** (src/auth/password.py)
>    - パスワードハッシュ化

### 影響範囲の分析

**ユーザー:**
> authenticateメソッドを変更した場合の影響範囲は？

**AI（find_callersツールを使用）:**
> `authenticate`メソッドは以下から呼び出されています：
> 
> | 呼び出し元 | ファイル | 行番号 |
> |-----------|---------|--------|
> | `LoginController.login` | controllers/auth.py | 45 |
> | `APIMiddleware.verify_token` | middleware/api.py | 23 |
> | `TestAuth.test_authenticate` | tests/test_auth.py | 78 |
> 
> 変更時は上記3箇所への影響を確認してください。

### コードベースの理解

**ユーザー:**
> このプロジェクトの主要コンポーネントを説明して

**AI（global_search + explain_codebaseプロンプトを使用）:**
> このプロジェクトは3層アーキテクチャで構成されています：
> 
> ## 1. Controllers層
> HTTPリクエストの処理を担当
> - `AuthController`: 認証関連エンドポイント
> - `UserController`: ユーザー管理エンドポイント
> - `APIController`: API共通処理
> 
> ## 2. Services層
> ビジネスロジックを実装
> - `AuthService`: 認証・認可処理
> - `UserService`: ユーザー管理処理
> - `NotificationService`: 通知処理
> 
> ## 3. Repositories層
> データアクセスを抽象化
> - `UserRepository`: ユーザーデータアクセス
> - `TokenRepository`: トークン管理

### コードレビュー

**ユーザー:**
> process_paymentメソッドをレビューして

**AI（code_reviewプロンプトを使用）:**
> ## コードレビュー: `process_payment`
> 
> ### セキュリティ
> ⚠️ **問題**: カード情報がログに出力される可能性
> ```python
> logger.info(f"Processing payment: {card_data}")  # 行 35
> ```
> **推奨**: センシティブデータはマスク処理を行う
> 
> ### パフォーマンス
> ⚠️ **問題**: 同期的なDB呼び出しが複数回
> **推奨**: バッチ処理またはasync化を検討
> 
> ### コード品質
> ✅ エラーハンドリングは適切
> ✅ 関数の責務は明確
> ⚠️ 関数が長い（85行）→ 抽出を検討

### 機能実装のガイダンス

**ユーザー:**
> 2要素認証機能を追加したい

**AI（implement_featureプロンプトを使用）:**
> ## 2要素認証の実装ガイド
> 
> ### 1. 変更が必要なファイル
> - `src/services/auth.py` - 認証ロジックの拡張
> - `src/models/user.py` - 2FA設定の追加
> - `src/controllers/auth.py` - 新規エンドポイント
> 
> ### 2. 新規作成するファイル
> - `src/services/totp.py` - TOTP生成/検証
> - `src/models/totp_secret.py` - シークレット管理
> 
> ### 3. 実装手順
> 1. `User`モデルに`totp_enabled`と`totp_secret`を追加
> 2. `TOTPService`クラスを作成
> 3. `AuthService.authenticate`を拡張
> 4. 新規エンドポイントを追加

---

## Pythonからの利用

### 基本的な使用例

```python
import asyncio
from pathlib import Path
from codegraph_mcp.core.parser import ASTParser
from codegraph_mcp.core.graph import GraphEngine, GraphQuery
from codegraph_mcp.core.indexer import Indexer

async def main():
    repo_path = Path("/path/to/project")
    
    # 1. リポジトリをインデックス
    indexer = Indexer()
    result = await indexer.index_repository(repo_path)
    print(f"Indexed {result.entities_count} entities")
    
    # 2. グラフエンジンを初期化
    engine = GraphEngine(repo_path)
    await engine.initialize()
    
    try:
        # 3. エンティティを検索
        query = GraphQuery(query="UserService", max_results=10)
        result = await engine.query(query)
        
        for entity in result.entities:
            print(f"{entity.name} ({entity.type.value})")
        
        # 4. 依存関係を分析
        if result.entities:
            deps = await engine.find_dependencies(result.entities[0].id)
            print(f"\nDependencies: {len(deps.entities)}")
            
        # 5. 統計を取得
        stats = await engine.get_statistics()
        print(f"\nTotal entities: {stats.entity_count}")
        
    finally:
        await engine.close()

asyncio.run(main())
```

### パーサーを直接使用

```python
from codegraph_mcp.core.parser import ASTParser

# コードを解析
parser = ASTParser()
code = '''
class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b
    
    def multiply(self, a: int, b: int) -> int:
        return a * b
'''

entities, relations = parser.parse_code(
    code=code,
    language="python",
    file_path="calculator.py"
)

print(f"Found {len(entities)} entities:")
for entity in entities:
    print(f"  - {entity.name} ({entity.type.value})")

print(f"\nFound {len(relations)} relations:")
for rel in relations:
    print(f"  - {rel.source_id} --[{rel.type.value}]--> {rel.target_id}")
```

### GraphRAG検索

```python
import asyncio
from pathlib import Path
from codegraph_mcp.core.graph import GraphEngine
from codegraph_mcp.core.graphrag import GraphRAGSearch

async def graphrag_example():
    repo_path = Path("/path/to/project")
    
    engine = GraphEngine(repo_path)
    await engine.initialize()
    
    try:
        # GraphRAG検索を初期化
        search = GraphRAGSearch(engine, use_llm=True)
        
        # グローバル検索
        result = await search.global_search(
            query="このプロジェクトの認証フローを説明して"
        )
        
        print(f"Answer: {result.answer}")
        print(f"Confidence: {result.confidence}")
        print(f"Communities searched: {result.communities_searched}")
        
        # ローカル検索
        result = await search.local_search(
            query="このクラスの使い方は？",
            entity_id="user_service"
        )
        
        print(f"\nLocal search answer: {result.answer}")
        
    finally:
        await engine.close()

asyncio.run(graphrag_example())
```

---

## MCPクライアントからの利用

### MCP SDKを使用した接続

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def mcp_client_example():
    # サーバーパラメータを設定
    server_params = StdioServerParameters(
        command="codegraph-mcp",
        args=["serve", "--repo", "/path/to/project"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # ツール一覧を取得
            tools = await session.list_tools()
            print(f"Available tools: {len(tools.tools)}")
            
            # ツールを呼び出し
            result = await session.call_tool(
                "query_codebase",
                arguments={"query": "UserService", "max_results": 5}
            )
            print(f"Result: {result.content[0].text}")
            
            # リソースを読み取り
            stats = await session.read_resource("codegraph://stats")
            print(f"Stats: {stats.contents[0].text}")
            
            # プロンプトを取得
            prompt = await session.get_prompt(
                "code_review",
                arguments={"entity_id": "user_service"}
            )
            print(f"Prompt: {prompt.messages[0].content.text[:200]}...")

asyncio.run(mcp_client_example())
```

---

## 実践的なユースケース

### 1. レガシーコードの理解

大規模なレガシープロジェクトを引き継いだ場合：

```
# 1. インデックスを作成
codegraph-mcp index ./legacy-project --full

# 2. 統計で全体像を把握
codegraph-mcp stats ./legacy-project

# 3. AIアシスタントで質問
"このプロジェクトの主要なコンポーネントを説明して"
"データベースとのやり取りはどこで行われている？"
"認証フローを追跡して"
```

### 2. リファクタリング影響分析

メソッドを変更する前に影響範囲を確認：

```
"processOrderメソッドの呼び出し元を全て教えて"
"このメソッドが依存しているクラスは？"
"変更した場合に影響を受けるテストは？"
```

### 3. 新機能の実装計画

新機能を追加する際のガイダンス：

```
"通知機能を追加したい。既存のコードとどう統合すべき？"
"同様の機能がすでに実装されているか調べて"
"この機能を実装するのに最適な場所は？"
```

### 4. コードレビュー支援

プルリクエストのレビュー時：

```
"AuthServiceクラスをセキュリティの観点でレビューして"
"このPRで変更されたファイルの影響範囲は？"
"新しく追加されたメソッドのテストケースを提案して"
```

### 5. オンボーディング

新しいチームメンバーの教育：

```
"プロジェクトのアーキテクチャを説明して"
"開発を始めるにはどのファイルから見ればいい？"
"テストの実行方法と構造を説明して"
```

---

## サンプルスクリプト

プロジェクトの`examples/`ディレクトリに以下のサンプルがあります：

- `basic_usage.py` - 基本的な使用例
- `mcp_client.py` - MCPクライアント接続例

実行方法：

```bash
cd /path/to/CodeGraphMCPServer
source .venv/bin/activate
python examples/basic_usage.py
```

---

## 関連ドキュメント

- [API リファレンス](./api.md)
- [設定ガイド](./configuration.md)
- [README](../README.md)
