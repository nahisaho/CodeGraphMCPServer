# Release Notes - v0.6.0

**Release Date**: 2025-11-27

## 🎛️ Background Server Management Release

CodeGraphMCPServer v0.6.0 は、バックグラウンドでのサーバー管理機能を追加しました。

---

## ✨ 新機能

### Background Server Commands

```bash
# バックグラウンドでサーバー起動
codegraph-mcp start --repo /path/to/project

# サーバー状態確認
codegraph-mcp status

# サーバー停止
codegraph-mcp stop
```

**出力例:**
```
✅ Server started in background
   PID: 12345
   Repository: /home/user/project
   Transport: sse
   URL: http://localhost:8080
   Log: /home/user/.codegraph/server.log

Use 'codegraph-mcp stop' to stop the server
```

### コマンド一覧

| コマンド | 説明 |
|---------|------|
| `start` | バックグラウンドでサーバー起動 |
| `stop` | バックグラウンドサーバー停止 |
| `status` | サーバー状態確認（ログ表示付き） |
| `serve` | フォアグラウンドで起動（従来どおり） |
| `index` | リポジトリをインデックス |
| `query` | グラフクエリ実行 |
| `stats` | 統計情報表示 |

---

## 🔧 技術的詳細

- **PIDファイル**: `~/.codegraph/server.pid`
- **ログファイル**: `~/.codegraph/server.log`
- **デフォルトトランスポート**: SSE（バックグラウンド時）
- **デフォルトポート**: 8080

---

## 📈 バージョン履歴

| Version | Date | Highlights | Tests |
|---------|------|------------|-------|
| v0.1.0 | 2025-11-26 | Initial: Python, TS, JS, Rust | 182 |
| v0.2.0 | 2025-11-27 | +Go, Java | 212 |
| v0.3.0 | 2025-11-27 | +PHP, C#, C++, HCL, Ruby (11言語) | 286 |
| v0.4.0 | 2025-11-27 | CLI Progress Display | 286 |
| v0.5.0 | 2025-11-27 | 47x Performance (Batch DB) | 285 |
| **v0.6.0** | **2025-11-27** | **Background Server Management** | **285** |

---

## 🔗 リンク

- **GitHub**: https://github.com/nahisaho/CodeGraphMCPServer
- **PyPI**: https://pypi.org/project/codegraph-mcp-server/
- **CHANGELOG**: [CHANGELOG.md](CHANGELOG.md)
