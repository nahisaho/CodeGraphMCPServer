# CodeGraphMCPServer ドキュメント

CodeGraphMCPServerの技術ドキュメントです。

## ドキュメント一覧

| ドキュメント | 説明 |
|-------------|------|
| [API リファレンス](./api.md) | MCP Tools, Resources, Promptsの詳細仕様 |
| [設定ガイド](./configuration.md) | 環境変数、設定ファイル、クライアント設定 |
| [使用例](./examples.md) | CLI、Python、MCPクライアントからの利用例 |

## クイックリンク

### 入門

- [README](../README.md) - プロジェクト概要とクイックスタート
- [インストール](../README.md#インストール)
- [クイックスタート](../README.md#クイックスタート)

### API

- [MCP Tools (14種)](./api.md#mcp-tools-14種)
- [MCP Resources (4種)](./api.md#mcp-resources-4種)
- [MCP Prompts (6種)](./api.md#mcp-prompts-6種)

### 設定

- [環境変数](./configuration.md#環境変数)
- [設定ファイル (codegraph.toml)](./configuration.md#設定ファイル)
- [MCPクライアント設定](./configuration.md#mcpクライアント設定)
- [LLM設定](./configuration.md#llm設定)

### 使用例

- [CLI使用例](./examples.md#cli使用例)
- [AIアシスタント連携](./examples.md#aiアシスタント連携例)
- [Pythonからの利用](./examples.md#pythonからの利用)

## サンプルコード

[`examples/`](../examples/)ディレクトリにサンプルコードがあります：

- `basic_usage.py` - コアAPIの基本的な使用方法
- `mcp_client.py` - MCPクライアント接続例

## 対応プラットフォーム

| クライアント | サポート状況 |
|-------------|-------------|
| Claude Desktop | ✅ 完全対応 |
| VS Code (GitHub Copilot) | ✅ 完全対応 |
| Cursor | ✅ 完全対応 |
| Windsurf | ✅ 完全対応 |

## 対応言語

| 言語 | AST解析 | 備考 |
|-----|--------|------|
| Python | ✅ | Tree-sitter |
| TypeScript | ✅ | Tree-sitter |
| JavaScript | ✅ | Tree-sitter |
| Rust | ✅ | Tree-sitter |

## バージョン情報

- CodeGraphMCPServer: 0.1.0
- MCP Protocol: 2024-11-05
- Python: 3.11+
