# CodeGraphMCPServer 設定ガイド

このドキュメントでは、CodeGraphMCPServerの設定方法と各MCPクライアントでの構成例を説明します。

## 目次

- [環境変数](#環境変数)
- [設定ファイル](#設定ファイル)
- [MCPクライアント設定](#mcpクライアント設定)
  - [Claude Desktop](#claude-desktop)
  - [VS Code (GitHub Copilot)](#vs-code-github-copilot)
  - [Cursor](#cursor)
  - [Windsurf](#windsurf)
- [トランスポート設定](#トランスポート設定)
- [LLM設定](#llm設定)
- [パフォーマンスチューニング](#パフォーマンスチューニング)

---

## 環境変数

CodeGraphMCPServerは以下の環境変数をサポートしています：

### 基本設定

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `CODEGRAPH_REPO_PATH` | カレントディレクトリ | 分析対象リポジトリのパス |
| `CODEGRAPH_DB_PATH` | `~/.codegraph/db` | データベース保存先 |
| `CODEGRAPH_LOG_LEVEL` | `INFO` | ログレベル (DEBUG, INFO, WARNING, ERROR) |

### LLM設定

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `OPENAI_API_KEY` | なし | OpenAI APIキー |
| `ANTHROPIC_API_KEY` | なし | Anthropic APIキー |
| `CODEGRAPH_LLM_PROVIDER` | `rule_based` | LLMプロバイダー (openai, anthropic, local, rule_based) |
| `CODEGRAPH_LLM_MODEL` | プロバイダー依存 | 使用するモデル名 |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama APIエンドポイント |

### キャッシュ設定

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `CODEGRAPH_CACHE_DIR` | `~/.codegraph/cache` | キャッシュディレクトリ |
| `CODEGRAPH_CACHE_TTL` | `3600` | キャッシュ有効期限（秒） |

### インデックス設定

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `CODEGRAPH_LANGUAGES` | `python,typescript,javascript,rust` | 対象言語（カンマ区切り） |
| `CODEGRAPH_EXCLUDE_PATTERNS` | `node_modules,__pycache__,.git` | 除外パターン |

---

## 設定ファイル

### `codegraph.toml`

プロジェクトルートに`codegraph.toml`を配置することで、プロジェクト固有の設定が可能です：

```toml
[codegraph]
# 基本設定
repo_path = "."
db_path = ".codegraph/db"
log_level = "INFO"

[index]
# インデックス設定
languages = ["python", "typescript", "rust"]
exclude_patterns = [
    "node_modules",
    "__pycache__",
    ".git",
    ".venv",
    "dist",
    "build",
]
max_file_size = 1048576  # 1MB

[semantic]
# セマンティック分析設定
llm_enabled = true
llm_provider = "openai"
llm_model = "gpt-4o-mini"
embedding_model = "text-embedding-3-small"

[community]
# コミュニティ検出設定
algorithm = "louvain"
resolution = 1.0
min_community_size = 3

[cache]
# キャッシュ設定
enabled = true
ttl = 3600
max_size = 104857600  # 100MB

[performance]
# パフォーマンス設定
max_workers = 4
batch_size = 100
timeout = 300
```

---

## MCPクライアント設定

### Claude Desktop

#### macOS

設定ファイル: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "codegraph": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "/path/to/your/project"],
      "env": {
        "CODEGRAPH_LOG_LEVEL": "INFO",
        "OPENAI_API_KEY": "your-api-key"
      }
    }
  }
}
```

#### Windows

設定ファイル: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "codegraph": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "C:\\path\\to\\your\\project"],
      "env": {
        "CODEGRAPH_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### Linux

設定ファイル: `~/.config/claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "codegraph": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "/home/user/projects/my-project"],
      "env": {
        "CODEGRAPH_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### VS Code (GitHub Copilot)

#### ワークスペース設定

`.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "codegraph": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "${workspaceFolder}"],
      "env": {
        "CODEGRAPH_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### ユーザー設定（グローバル）

VS Code設定:

```json
{
  "mcp.servers": {
    "codegraph-global": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "${workspaceFolder}"]
    }
  }
}
```

#### 複数プロジェクト対応

```json
{
  "mcp.servers": {
    "codegraph-frontend": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "${workspaceFolder}/frontend"]
    },
    "codegraph-backend": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "${workspaceFolder}/backend"]
    }
  }
}
```

### Cursor

設定ファイル: `~/.cursor/mcp.json`

```json
{
  "mcpServers": {
    "codegraph": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "/path/to/your/project"],
      "env": {
        "CODEGRAPH_LOG_LEVEL": "INFO",
        "CODEGRAPH_LLM_PROVIDER": "openai"
      }
    }
  }
}
```

### Windsurf

設定ファイル: `~/.windsurf/mcp.json`

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

## トランスポート設定

### stdio（デフォルト）

標準入出力を使用するトランスポート。ほとんどのMCPクライアントで使用されます。

```bash
codegraph-mcp serve --repo /path/to/project --transport stdio
```

クライアント設定:

```json
{
  "mcpServers": {
    "codegraph": {
      "command": "codegraph-mcp",
      "args": ["serve", "--repo", "/path/to/project"]
    }
  }
}
```

### SSE (Server-Sent Events)

HTTPベースのトランスポート。リモートサーバーやデバッグに便利です。

```bash
codegraph-mcp serve --repo /path/to/project --transport sse --port 8080
```

#### SSEクライアント設定例

```json
{
  "mcpServers": {
    "codegraph": {
      "type": "sse",
      "url": "http://localhost:8080/sse"
    }
  }
}
```

#### Docker + SSE

```yaml
# docker-compose.yml
version: '3.8'
services:
  codegraph:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - /path/to/project:/repo:ro
    command: ["serve", "--repo", "/repo", "--transport", "sse", "--port", "8080"]
```

---

## LLM設定

### OpenAI

```bash
export OPENAI_API_KEY="sk-..."
export CODEGRAPH_LLM_PROVIDER="openai"
export CODEGRAPH_LLM_MODEL="gpt-4o-mini"
```

または`codegraph.toml`:

```toml
[semantic]
llm_enabled = true
llm_provider = "openai"
llm_model = "gpt-4o-mini"
```

### Anthropic

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export CODEGRAPH_LLM_PROVIDER="anthropic"
export CODEGRAPH_LLM_MODEL="claude-3-haiku-20240307"
```

または`codegraph.toml`:

```toml
[semantic]
llm_enabled = true
llm_provider = "anthropic"
llm_model = "claude-3-haiku-20240307"
```

### ローカルLLM (Ollama)

```bash
# Ollamaを起動
ollama serve

# モデルをダウンロード
ollama pull llama3.2

# 環境変数を設定
export CODEGRAPH_LLM_PROVIDER="local"
export CODEGRAPH_LLM_MODEL="llama3.2"
export OLLAMA_BASE_URL="http://localhost:11434"
```

または`codegraph.toml`:

```toml
[semantic]
llm_enabled = true
llm_provider = "local"
llm_model = "llama3.2"
ollama_url = "http://localhost:11434"
```

### ルールベース（デフォルト）

LLMを使用せず、ルールベースの分析を行います：

```toml
[semantic]
llm_enabled = false
llm_provider = "rule_based"
```

---

## パフォーマンスチューニング

### 大規模リポジトリ向け

```toml
[index]
# 大きなファイルをスキップ
max_file_size = 524288  # 512KB

# 並列処理を増やす
[performance]
max_workers = 8
batch_size = 200

# キャッシュを有効活用
[cache]
enabled = true
max_size = 524288000  # 500MB
ttl = 86400  # 24時間
```

### メモリ制限環境向け

```toml
[performance]
max_workers = 2
batch_size = 50

[cache]
enabled = true
max_size = 52428800  # 50MB

[index]
max_file_size = 262144  # 256KB
```

### 除外パターンの最適化

```toml
[index]
exclude_patterns = [
    # 依存関係
    "node_modules",
    ".venv",
    "vendor",
    
    # ビルド成果物
    "dist",
    "build",
    "target",
    "__pycache__",
    "*.pyc",
    
    # テストデータ
    "fixtures",
    "testdata",
    
    # ドキュメント
    "docs/api",
    
    # 生成ファイル
    "*.generated.*",
    "*.min.js",
    "*.bundle.js",
]
```

---

## トラブルシューティング

### サーバーが起動しない

1. Pythonバージョンを確認:
   ```bash
   python --version  # 3.11以上が必要
   ```

2. インストールを確認:
   ```bash
   pip show codegraph-mcp
   ```

3. 詳細ログを有効化:
   ```bash
   CODEGRAPH_LOG_LEVEL=DEBUG codegraph-mcp serve --repo .
   ```

### インデックスが遅い

1. 除外パターンを確認
2. `max_file_size`を調整
3. `max_workers`を増やす

### メモリ使用量が多い

1. `batch_size`を減らす
2. `max_workers`を減らす
3. `cache.max_size`を減らす

### LLMエラー

1. APIキーを確認
2. モデル名を確認
3. ネットワーク接続を確認

---

## 関連ドキュメント

- [API リファレンス](./api.md)
- [使用例](./examples.md)
- [README](../README.md)
