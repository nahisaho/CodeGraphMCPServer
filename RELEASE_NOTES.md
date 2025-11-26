# Release Notes - v0.4.0

**Release Date**: 2025-11-27

## ⚡ CLI Enhancement Release

CodeGraphMCPServer v0.4.0 は、CLIのユーザーエクスペリエンスを大幅に向上させました。

---

## ✨ 新機能

### 🎨 Rich Progress Display

`codegraph-mcp index` コマンドにアニメーション付きプログレス表示を追加：

```
🔍 CodeGraph Indexer
Repository: /path/to/project
Mode: Full

  Processing: parser.py ━━━━━━━━━━━━━━━━━━━━ 45% 0:00:12

   📊 Indexing Results
┌───────────────┬────────┐
│ Entities      │ 941    │
│ Relations     │ 4741   │
│ Files Indexed │ 67     │
│ Duration      │ 29.47s │
└───────────────┴────────┘

✅ Indexing completed successfully!
```

**機能:**
- スピナーアニメーション
- リアルタイムプログレスバー
- ファイル処理状況表示
- カラー付き結果テーブル

---

## ⚡ パフォーマンス実測値

| メトリクス | 実測値 | 備考 |
|-----------|--------|------|
| インデックス速度 | **32 エンティティ/秒** | 67ファイル, 941エンティティ |
| ファイル処理速度 | **0.44秒/ファイル** | 11言語混在プロジェクト |
| 増分インデックス | **< 2秒** | 変更ファイルのみ処理 |
| クエリレスポンス | **< 2ms** | グラフ検索 |

---

## 📈 バージョン履歴

| Version | Date | Highlights | Tests |
|---------|------|------------|-------|
| v0.1.0 | 2025-11-26 | Initial: Python, TS, JS, Rust | 182 |
| v0.2.0 | 2025-11-27 | +Go, Java | 212 |
| v0.3.0 | 2025-11-27 | +PHP, C#, C++, HCL, Ruby (11言語) | 286 |
| **v0.4.0** | **2025-11-27** | **CLI Progress Display** | **286** |

---

## 🔗 リンク

- **GitHub**: https://github.com/nahisaho/CodeGraphMCPServer
- **PyPI**: https://pypi.org/project/codegraph-mcp-server/
- **CHANGELOG**: [CHANGELOG.md](CHANGELOG.md)
