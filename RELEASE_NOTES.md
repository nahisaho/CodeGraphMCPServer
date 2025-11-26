# Release Notes - v0.1.0

**Release Date**: 2025-11-26

## 🎉 Initial Release

CodeGraphMCPServer v0.1.0 は、コードベースの構造を理解し、GraphRAG機能を提供するMCPサーバーの初回リリースです。

---

## ✨ 主な機能

### 🌳 マルチ言語AST解析

Tree-sitterを使用した高速・正確なコード解析：

| 言語 | クラス | 関数 | メソッド | インポート | インターフェース |
|------|--------|------|----------|-----------|-----------------|
| Python | ✅ | ✅ | ✅ | ✅ | ✅ (Protocol) |
| TypeScript | ✅ | ✅ | ✅ | ✅ | ✅ |
| JavaScript | ✅ | ✅ | ✅ | ✅ | - |
| Rust | ✅ (struct) | ✅ | ✅ (impl) | ✅ | ✅ (trait) |

### 🧠 GraphRAG統合

Microsoft GraphRAGコンセプトに基づくコード理解：

- **コミュニティ検出**: Louvainアルゴリズムによる自動クラスタリング
- **グローバル検索**: コードベース全体の俯瞰的理解
- **ローカル検索**: エンティティ近傍のコンテキスト取得
- **LLM連携**: OpenAI / Anthropic / Ollama / ルールベース

### 🔧 MCP インターフェース

| カテゴリ | 数量 | 主な機能 |
|---------|------|----------|
| Tools | 14 | コード検索、依存分析、GraphRAG検索 |
| Resources | 4 | エンティティ、ファイル、コミュニティ、統計 |
| Prompts | 6 | コードレビュー、実装ガイド、デバッグ支援 |

### 📡 トランスポート

- **stdio**: 標準MCPクライアント向け（Claude Desktop, VS Code, Cursor）
- **SSE**: HTTP経由のリモート接続、デバッグ用

---

## 📦 インストール

```bash
pip install codegraph-mcp
```

### オプション依存

```bash
# OpenAI LLM統合
pip install codegraph-mcp[openai]

# SSEトランスポート
pip install codegraph-mcp[sse]

# 全機能
pip install codegraph-mcp[all]
```

---

## 🚀 クイックスタート

```bash
# リポジトリをインデックス
codegraph-mcp index /path/to/project --full

# MCPサーバーを起動
codegraph-mcp serve --repo /path/to/project
```

### Claude Desktop設定

`~/.config/claude/claude_desktop_config.json`:

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

---

## ⚡ パフォーマンス

| メトリクス | 実測値 | 目標値 |
|-----------|--------|--------|
| インデックス (700エンティティ) | 21秒 | < 30秒 |
| クエリ応答 | < 2ms | < 500ms |
| 増分インデックス | < 2秒 | < 2秒 |

---

## 🧪 テスト

```
182 tests passed, 1 skipped
Coverage: 80%+
```

---

## 📚 ドキュメント

- [README](README.md) - プロジェクト概要
- [API リファレンス](docs/api.md) - 詳細API仕様
- [設定ガイド](docs/configuration.md) - 環境変数・クライアント設定
- [使用例](docs/examples.md) - CLI・Python・MCP使用例
- [CHANGELOG](CHANGELOG.md) - 変更履歴

---

## 🙏 謝辞

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Tree-sitter](https://tree-sitter.github.io/)
- [NetworkX](https://networkx.org/)
- [Microsoft GraphRAG](https://github.com/microsoft/graphrag)

---

## 📄 ライセンス

MIT License

---

## 🔗 リンク

- **GitHub**: https://github.com/nahisaho/CodeGraphMCPServer
- **Issues**: https://github.com/nahisaho/CodeGraphMCPServer/issues
- **PyPI**: https://pypi.org/project/codegraph-mcp/
