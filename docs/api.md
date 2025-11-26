# CodeGraphMCPServer API リファレンス

このドキュメントでは、CodeGraphMCPServerが提供するMCP API（Tools、Resources、Prompts）の詳細を説明します。

## 目次

- [概要](#概要)
- [MCP Tools (14種)](#mcp-tools-14種)
  - [グラフクエリツール](#グラフクエリツール)
  - [コード取得ツール](#コード取得ツール)
  - [GraphRAG ツール](#graphrag-ツール)
  - [管理ツール](#管理ツール)
- [MCP Resources (4種)](#mcp-resources-4種)
- [MCP Prompts (6種)](#mcp-prompts-6種)
- [データ型](#データ型)

---

## 概要

CodeGraphMCPServer は、Model Context Protocol (MCP) を通じて以下のAPIを提供します：

| カテゴリ | 数量 | 説明 |
|---------|------|------|
| Tools | 14 | コード分析・検索・管理機能 |
| Resources | 4 | コードグラフデータへのアクセス |
| Prompts | 6 | 定型的なコード分析タスクのテンプレート |

---

## MCP Tools (14種)

### グラフクエリツール

#### `query_codebase`

自然言語でコードグラフを検索します。

**入力スキーマ:**

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "自然言語クエリ"
    },
    "max_results": {
      "type": "integer",
      "description": "最大結果数",
      "default": 20
    }
  },
  "required": ["query"]
}
```

**使用例:**

```json
{
  "name": "query_codebase",
  "arguments": {
    "query": "認証処理を行うクラス",
    "max_results": 10
  }
}
```

**レスポンス例:**

```json
{
  "entities": [
    {
      "id": "auth_service",
      "name": "AuthService",
      "type": "class",
      "file_path": "src/services/auth.py",
      "start_line": 15,
      "relevance": 0.95
    }
  ],
  "total_count": 3
}
```

---

#### `find_dependencies`

指定したエンティティの依存関係を検索します。

**入力スキーマ:**

```json
{
  "type": "object",
  "properties": {
    "entity_id": {
      "type": "string",
      "description": "エンティティID"
    },
    "depth": {
      "type": "integer",
      "description": "依存関係の探索深度",
      "default": 2
    }
  },
  "required": ["entity_id"]
}
```

**使用例:**

```json
{
  "name": "find_dependencies",
  "arguments": {
    "entity_id": "user_service",
    "depth": 3
  }
}
```

**レスポンス例:**

```json
{
  "entities": [
    {
      "id": "database_connection",
      "name": "DatabaseConnection",
      "type": "class",
      "depth": 1
    },
    {
      "id": "logger",
      "name": "Logger",
      "type": "class",
      "depth": 1
    }
  ],
  "total_dependencies": 5
}
```

---

#### `find_callers`

関数・メソッドの呼び出し元を検索します。

**入力スキーマ:**

```json
{
  "type": "object",
  "properties": {
    "entity_id": {
      "type": "string",
      "description": "関数/メソッドID"
    }
  },
  "required": ["entity_id"]
}
```

**使用例:**

```json
{
  "name": "find_callers",
  "arguments": {
    "entity_id": "authenticate"
  }
}
```

**レスポンス例:**

```json
{
  "callers": [
    {
      "id": "login_controller_login",
      "name": "login",
      "type": "method"
    },
    {
      "id": "api_middleware_verify",
      "name": "verify_token",
      "type": "method"
    }
  ]
}
```

---

#### `find_callees`

関数・メソッドの呼び出し先を検索します。

**入力スキーマ:**

```json
{
  "type": "object",
  "properties": {
    "entity_id": {
      "type": "string",
      "description": "関数/メソッドID"
    }
  },
  "required": ["entity_id"]
}
```

**使用例:**

```json
{
  "name": "find_callees",
  "arguments": {
    "entity_id": "process_request"
  }
}
```

**レスポンス例:**

```json
{
  "callees": [
    {
      "id": "validate_input",
      "name": "validate_input",
      "type": "function"
    },
    {
      "id": "save_to_db",
      "name": "save_to_db",
      "type": "method"
    }
  ]
}
```

---

#### `find_implementations`

インターフェース・抽象クラスの実装を検索します。

**入力スキーマ:**

```json
{
  "type": "object",
  "properties": {
    "entity_id": {
      "type": "string",
      "description": "インターフェース/クラスID"
    }
  },
  "required": ["entity_id"]
}
```

**使用例:**

```json
{
  "name": "find_implementations",
  "arguments": {
    "entity_id": "repository_interface"
  }
}
```

**レスポンス例:**

```json
{
  "implementations": [
    {
      "id": "user_repository",
      "name": "UserRepository",
      "type": "class"
    },
    {
      "id": "product_repository",
      "name": "ProductRepository",
      "type": "class"
    }
  ]
}
```

---

#### `analyze_module_structure`

モジュール・ファイルの構造を分析します。

**入力スキーマ:**

```json
{
  "type": "object",
  "properties": {
    "file_path": {
      "type": "string",
      "description": "ファイルパス"
    }
  },
  "required": ["file_path"]
}
```

**使用例:**

```json
{
  "name": "analyze_module_structure",
  "arguments": {
    "file_path": "src/services/user_service.py"
  }
}
```

**レスポンス例:**

```json
{
  "file": "src/services/user_service.py",
  "entities": [
    {
      "type": "class",
      "name": "UserService",
      "lines": "10-150"
    },
    {
      "type": "method",
      "name": "create_user",
      "lines": "25-45"
    },
    {
      "type": "method",
      "name": "update_user",
      "lines": "47-70"
    }
  ]
}
```

---

### コード取得ツール

#### `get_code_snippet`

エンティティのソースコードを取得します。

**入力スキーマ:**

```json
{
  "type": "object",
  "properties": {
    "entity_id": {
      "type": "string",
      "description": "エンティティID"
    },
    "include_context": {
      "type": "boolean",
      "description": "周辺コンテキストを含める",
      "default": true
    }
  },
  "required": ["entity_id"]
}
```

**使用例:**

```json
{
  "name": "get_code_snippet",
  "arguments": {
    "entity_id": "calculate_total",
    "include_context": true
  }
}
```

**レスポンス例:**

```json
{
  "entity_id": "calculate_total",
  "name": "calculate_total",
  "source": "def calculate_total(items: list[Item]) -> float:\n    \"\"\"Calculate the total price of items.\"\"\"\n    return sum(item.price * item.quantity for item in items)"
}
```

---

#### `read_file_content`

ファイル内容を取得します（行範囲指定可能）。

**入力スキーマ:**

```json
{
  "type": "object",
  "properties": {
    "file_path": {
      "type": "string",
      "description": "ファイルパス"
    },
    "start_line": {
      "type": "integer",
      "description": "開始行番号"
    },
    "end_line": {
      "type": "integer",
      "description": "終了行番号"
    }
  },
  "required": ["file_path"]
}
```

**使用例:**

```json
{
  "name": "read_file_content",
  "arguments": {
    "file_path": "src/models/user.py",
    "start_line": 1,
    "end_line": 50
  }
}
```

**レスポンス例:**

```json
{
  "file": "src/models/user.py",
  "content": "from dataclasses import dataclass\n\n@dataclass\nclass User:\n    ...",
  "lines": "1-50"
}
```

---

#### `get_file_structure`

ファイルの構造概要を取得します。

**入力スキーマ:**

```json
{
  "type": "object",
  "properties": {
    "file_path": {
      "type": "string",
      "description": "ファイルパス"
    }
  },
  "required": ["file_path"]
}
```

**使用例:**

```json
{
  "name": "get_file_structure",
  "arguments": {
    "file_path": "src/core/engine.py"
  }
}
```

**レスポンス例:**

```json
{
  "file": "src/core/engine.py",
  "entities": [
    {"type": "class", "name": "Engine", "lines": "15-200"},
    {"type": "method", "name": "__init__", "lines": "20-35"},
    {"type": "method", "name": "start", "lines": "37-55"},
    {"type": "method", "name": "stop", "lines": "57-70"}
  ]
}
```

---

### GraphRAG ツール

#### `global_search`

GraphRAGを使用してコミュニティ横断のグローバル検索を実行します。

**入力スキーマ:**

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "検索クエリ"
    }
  },
  "required": ["query"]
}
```

**使用例:**

```json
{
  "name": "global_search",
  "arguments": {
    "query": "このプロジェクトの認証フローはどうなっていますか？"
  }
}
```

**レスポンス例:**

```json
{
  "query": "このプロジェクトの認証フローはどうなっていますか？",
  "answer": "このプロジェクトの認証フローは3段階で構成されています...",
  "communities_searched": 5,
  "confidence": 0.87,
  "relevant_communities": [
    {"id": 1, "name": "Authentication Module", "relevance": 0.95},
    {"id": 3, "name": "User Management", "relevance": 0.72}
  ],
  "supporting_entities": [
    {
      "id": "auth_service",
      "name": "AuthService",
      "type": "class",
      "file": "src/services/auth.py",
      "relevance": 0.95
    }
  ]
}
```

---

#### `local_search`

GraphRAGを使用してエンティティ近傍のローカル検索を実行します。

**入力スキーマ:**

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "検索クエリ"
    },
    "entity_id": {
      "type": "string",
      "description": "検索開始エンティティ"
    }
  },
  "required": ["query", "entity_id"]
}
```

**使用例:**

```json
{
  "name": "local_search",
  "arguments": {
    "query": "このクラスはどのように使用されていますか？",
    "entity_id": "user_repository"
  }
}
```

**レスポンス例:**

```json
{
  "query": "このクラスはどのように使用されていますか？",
  "answer": "UserRepositoryは主にUserServiceから利用されており...",
  "start_entity": "user_repository",
  "entities_searched": 15,
  "confidence": 0.82,
  "relevant_entities": [
    {
      "id": "user_service",
      "name": "UserService",
      "type": "class",
      "relevance": 0.90
    }
  ],
  "relationships": [
    {"source": "user_service", "target": "user_repository", "type": "calls"}
  ]
}
```

---

### 管理ツール

#### `suggest_refactoring`

リファクタリングの提案を取得します。

**入力スキーマ:**

```json
{
  "type": "object",
  "properties": {
    "entity_id": {
      "type": "string",
      "description": "分析対象エンティティ"
    },
    "type": {
      "type": "string",
      "enum": ["extract", "rename", "move", "simplify"],
      "description": "リファクタリングの種類"
    }
  },
  "required": ["entity_id"]
}
```

**使用例:**

```json
{
  "name": "suggest_refactoring",
  "arguments": {
    "entity_id": "process_order",
    "type": "extract"
  }
}
```

**レスポンス例:**

```json
{
  "entity": "process_order",
  "suggestions": [
    {
      "type": "extract",
      "reason": "Function is 85 lines, consider extraction"
    },
    {
      "type": "simplify",
      "reason": "High cyclomatic complexity (12)"
    }
  ]
}
```

---

#### `reindex_repository`

リポジトリの再インデックスをトリガーします。

**入力スキーマ:**

```json
{
  "type": "object",
  "properties": {
    "incremental": {
      "type": "boolean",
      "description": "増分更新のみ実行",
      "default": true
    }
  }
}
```

**使用例:**

```json
{
  "name": "reindex_repository",
  "arguments": {
    "incremental": false
  }
}
```

**レスポンス例:**

```json
{
  "entities": 256,
  "relations": 512,
  "files": 45,
  "duration": 2.35
}
```

---

#### `execute_shell_command`

リポジトリコンテキストでシェルコマンドを実行します。

**入力スキーマ:**

```json
{
  "type": "object",
  "properties": {
    "command": {
      "type": "string",
      "description": "実行するシェルコマンド"
    },
    "timeout": {
      "type": "integer",
      "description": "タイムアウト（秒）",
      "default": 30
    }
  },
  "required": ["command"]
}
```

**使用例:**

```json
{
  "name": "execute_shell_command",
  "arguments": {
    "command": "git status",
    "timeout": 10
  }
}
```

**レスポンス例:**

```json
{
  "exit_code": 0,
  "stdout": "On branch main\nnothing to commit, working tree clean\n",
  "stderr": ""
}
```

---

## MCP Resources (4種)

### `codegraph://entities/{entity_id}`

特定のエンティティの詳細情報を取得します。

**URI パターン:** `codegraph://entities/{entity_id}`

**レスポンス例:**

```json
{
  "entity": {
    "id": "user_service",
    "type": "class",
    "name": "UserService",
    "qualified_name": "src.services.user_service.UserService",
    "file_path": "src/services/user_service.py",
    "start_line": 10,
    "end_line": 150,
    "signature": "class UserService:",
    "docstring": "Service for managing users.",
    "source_code": "class UserService:\n    ..."
  },
  "relations": {
    "callers": [
      {"id": "api_controller", "name": "APIController"}
    ],
    "callees": [
      {"id": "user_repository", "name": "UserRepository"}
    ]
  }
}
```

---

### `codegraph://files/{file_path}`

特定ファイルのコードグラフ情報を取得します。

**URI パターン:** `codegraph://files/{file_path}`

**レスポンス例:**

```json
{
  "file_path": "src/services/auth.py",
  "entities": [
    {
      "id": "auth_service",
      "type": "class",
      "name": "AuthService",
      "start_line": 15,
      "end_line": 120,
      "signature": "class AuthService:"
    },
    {
      "id": "authenticate",
      "type": "method",
      "name": "authenticate",
      "start_line": 25,
      "end_line": 55,
      "signature": "def authenticate(self, username: str, password: str) -> bool:"
    }
  ],
  "relations": [
    {"source": "auth_service", "target": "authenticate", "type": "contains"}
  ],
  "entity_count": 8
}
```

---

### `codegraph://communities/{community_id}`

コードコミュニティの情報を取得します。

**URI パターン:** `codegraph://communities/{community_id}`

**レスポンス例:**

```json
{
  "community": {
    "id": 1,
    "level": 0,
    "name": "Authentication Module",
    "summary": "This community contains authentication-related classes and functions.",
    "member_count": 12
  },
  "members": [
    {"id": "auth_service", "type": "class", "name": "AuthService", "file": "src/services/auth.py"},
    {"id": "token_manager", "type": "class", "name": "TokenManager", "file": "src/auth/token.py"}
  ]
}
```

---

### `codegraph://stats`

コードグラフ全体の統計情報を取得します。

**URI パターン:** `codegraph://stats`

**レスポンス例:**

```json
{
  "statistics": {
    "entities": 256,
    "relations": 512,
    "communities": 8,
    "files": 45,
    "languages": ["python", "typescript"]
  },
  "entities_by_type": {
    "class": 45,
    "function": 120,
    "method": 85,
    "module": 6
  },
  "relations_by_type": {
    "calls": 280,
    "contains": 150,
    "imports": 52,
    "implements": 30
  }
}
```

---

## MCP Prompts (6種)

### `code_review`

コードレビューを実施するためのプロンプトを生成します。

**引数:**

| 名前 | 必須 | 説明 |
|------|------|------|
| `entity_id` | ✅ | レビュー対象のエンティティID |
| `focus` | ❌ | レビューの焦点（security, performance, style） |

**使用例:**

```json
{
  "name": "code_review",
  "arguments": {
    "entity_id": "process_payment",
    "focus": "security"
  }
}
```

**生成されるプロンプト（要約）:**

```
# Code Review Request

## Entity Information
- Name: process_payment
- Type: function
- File: src/payments/processor.py:45-120

## Source Code
[コードが含まれます]

## Context
- Called by: PaymentController.handle_payment, ...
- Calls: validate_card, charge_card, ...

## Review Focus
security

Please review this code for:
1. Potential bugs or errors
2. Code quality issues
3. Performance concerns
4. Security vulnerabilities
5. Suggestions for improvement
```

---

### `explain_codebase`

コードベース全体の説明を生成するプロンプトを生成します。

**引数:**

| 名前 | 必須 | 説明 |
|------|------|------|
| `depth` | ❌ | 説明の深さ（overview, detailed） |

**使用例:**

```json
{
  "name": "explain_codebase",
  "arguments": {
    "depth": "detailed"
  }
}
```

---

### `implement_feature`

新機能の実装ガイダンスを提供するプロンプトを生成します。

**引数:**

| 名前 | 必須 | 説明 |
|------|------|------|
| `description` | ✅ | 機能の説明 |
| `related_entities` | ❌ | 関連する既存エンティティ |

**使用例:**

```json
{
  "name": "implement_feature",
  "arguments": {
    "description": "ユーザー認証に2要素認証を追加する",
    "related_entities": "auth_service,user_service"
  }
}
```

---

### `debug_issue`

問題のデバッグを支援するプロンプトを生成します。

**引数:**

| 名前 | 必須 | 説明 |
|------|------|------|
| `error_message` | ✅ | エラーメッセージまたは症状 |
| `context` | ❌ | 追加コンテキスト |

**使用例:**

```json
{
  "name": "debug_issue",
  "arguments": {
    "error_message": "TypeError: 'NoneType' object is not subscriptable at line 45",
    "context": "This occurs when processing user input from the API"
  }
}
```

---

### `refactor_guidance`

リファクタリングのガイダンスを提供するプロンプトを生成します。

**引数:**

| 名前 | 必須 | 説明 |
|------|------|------|
| `entity_id` | ✅ | リファクタリング対象のエンティティ |
| `goal` | ❌ | リファクタリングの目標 |

**使用例:**

```json
{
  "name": "refactor_guidance",
  "arguments": {
    "entity_id": "data_processor",
    "goal": "improve testability"
  }
}
```

---

### `test_generation`

テストコードを生成するためのプロンプトを生成します。

**引数:**

| 名前 | 必須 | 説明 |
|------|------|------|
| `entity_id` | ✅ | テスト対象のエンティティ |
| `test_type` | ❌ | テストの種類（unit, integration） |

**使用例:**

```json
{
  "name": "test_generation",
  "arguments": {
    "entity_id": "calculate_shipping",
    "test_type": "unit"
  }
}
```

---

## データ型

### Entity

コードエンティティを表す構造体。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `id` | string | 一意識別子 |
| `type` | EntityType | エンティティ種別 |
| `name` | string | 名前 |
| `qualified_name` | string | 完全修飾名 |
| `file_path` | string | ファイルパス |
| `start_line` | integer | 開始行番号 |
| `end_line` | integer | 終了行番号 |
| `signature` | string | シグネチャ |
| `docstring` | string | ドキュメント文字列 |
| `source_code` | string | ソースコード |

### EntityType

エンティティ種別の列挙型。

| 値 | 説明 |
|----|------|
| `module` | モジュール |
| `class` | クラス |
| `function` | 関数 |
| `method` | メソッド |
| `interface` | インターフェース |
| `enum` | 列挙型 |
| `struct` | 構造体 |
| `trait` | トレイト |

### RelationType

関係種別の列挙型。

| 値 | 説明 |
|----|------|
| `calls` | 呼び出し |
| `contains` | 包含 |
| `imports` | インポート |
| `implements` | 実装 |
| `extends` | 継承 |
| `uses` | 使用 |
| `defines` | 定義 |

---

## エラーハンドリング

すべてのツールは、エラー発生時に以下の形式でエラーを返します：

```json
{
  "error": "Entity not found",
  "entity_id": "unknown_entity"
}
```

一般的なエラー：

| エラー | 原因 | 対処法 |
|--------|------|--------|
| `Entity not found` | 指定されたエンティティが存在しない | entity_idを確認 |
| `File not found` | 指定されたファイルが存在しない | ファイルパスを確認 |
| `Community not found` | 指定されたコミュニティが存在しない | community_idを確認 |
| `Unknown tool` | 存在しないツールを呼び出した | ツール名を確認 |
| `Command timed out` | シェルコマンドがタイムアウト | timeoutを増やす |

---

## バージョン情報

- API バージョン: 1.0
- MCP プロトコルバージョン: 2024-11-05
- サーバーバージョン: 0.1.0
