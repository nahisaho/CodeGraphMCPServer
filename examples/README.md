# Examples

CodeGraphMCPServerの使用例を格納するディレクトリです。

## ファイル一覧

| ファイル | 説明 |
|----------|------|
| `basic_usage.py` | CLIとコアAPIの基本的な使用方法 |
| `mcp_client.py` | MCPクライアントからの利用例 |

## 実行方法

### 事前準備

```bash
# リポジトリのルートディレクトリで実行
cd /path/to/CodeGraphMCPServer

# 仮想環境をアクティベート
source .venv/bin/activate

# 開発用インストール
pip install -e ".[dev]"
```

### basic_usage.py

コアAPIを直接使用する例:

```bash
python examples/basic_usage.py
```

**機能:**
- リポジトリのインデックス作成
- エンティティの検索
- 依存関係の分析
- 統計情報の取得

### mcp_client.py

MCPプロトコル経由でサーバーに接続する例:

```bash
# まずサーバーを起動（別ターミナル）
codegraph-mcp serve --repo /path/to/project

# クライアントを実行
python examples/mcp_client.py
```

**機能:**
- MCPサーバーへの接続
- ツールの呼び出し
- リソースの読み取り
- プロンプトの取得

## CLI使用例

### インデックス作成

```bash
# フルインデックス
codegraph-mcp index /path/to/repository --full

# 増分インデックス
codegraph-mcp index /path/to/repository
```

### 統計情報の取得

```bash
codegraph-mcp stats /path/to/repository
```

### コードの検索

```bash
# 名前で検索
codegraph-mcp query "UserService" --repo /path/to/repository

# 型で検索
codegraph-mcp query "class" --repo /path/to/repository --type class
```

### MCPサーバーの起動

```bash
# stdioトランスポート（デフォルト）
codegraph-mcp serve --repo /path/to/repository

# SSEトランスポート
codegraph-mcp serve --repo /path/to/repository --transport sse --port 8080
```

## MCPクライアント設定例

### Claude Desktop

`~/.config/claude/claude_desktop_config.json`:

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

### VS Code (GitHub Copilot)

`.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "codegraph": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "${workspaceFolder}"]
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json`:

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

## AIアシスタントとの対話例

### 依存関係の分析

```
You: Calculatorクラスの依存関係を教えて

AI: [find_dependencies ツールを使用]
    Calculatorは以下に依存しています:
    - mathモジュール
    - Validatorクラス
```

### 呼び出し元の検索

```
You: addメソッドを変更した場合の影響範囲は？

AI: [find_callers ツールを使用]
    addの呼び出し元:
    - Calculator.sum_all() (calculator.py:25)
    - test_calculator.test_add() (test_calculator.py:10)
```

### コードベースの説明

```
You: このプロジェクトの構造を説明して

AI: [explain_codebase プロンプトを使用]
    
    このプロジェクトは以下の構造で構成されています:
    1. core/ - コアロジック
    2. mcp/ - MCPインターフェース
    3. storage/ - データ永続化
```
