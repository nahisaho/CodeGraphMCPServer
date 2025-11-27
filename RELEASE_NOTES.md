# Release Notes - v0.6.2

**Release Date**: 2025-11-27

## 🔍 Enhanced Query & Partial ID Matching Release

CodeGraphMCPServer v0.6.2 は、部分ID解決、自動コミュニティ検出、強化されたクエリ機能を追加しました。

---

## ✨ 新機能

### Entity ID Partial Matching

```bash
# 部分IDでエンティティを検索
codegraph-mcp query /path/to/repo --entity "hashmap_random_keys"
codegraph-mcp query /path/to/repo --entity "linux.rs::hashmap_random_keys"
```

**解決パターン:**
- 完全一致 → 名前一致 → qualified_name接尾辞 → `file::name`パターン

### Auto Community Detection

```bash
# インデックス作成時に自動でコミュニティ検出（デフォルト）
codegraph-mcp index /path/to/repo --full

# 大規模リポジトリでは無効化可能
codegraph-mcp index /path/to/repo --full --no-community
```

**出力例:**
```
Indexed 230,796 entities, 651,140 relations in 128.45s
Detected 456 communities (modularity: 0.847)
```

### Enhanced query_codebase

- **関連性スコアリング**: 完全一致(1.0), 前方一致(0.8), 部分一致(0.6)
- **`include_related`**: 関連エンティティを結果に含める
- **`include_community`**: コミュニティ情報を含める
- **`entity_types`フィルタ**: function, class, method等でフィルタ

### Large Repository Support

- **サンプリング**: 50,000ノード超は次数ベースでサンプリング
- **バッチ処理**: NetworkX/SQLite操作の最適化
- **実績**: Rust コンパイラ (230K エンティティ) で検証済み

---

## 📈 バージョン履歴

| Version | Date | Highlights | Tests |
|---------|------|------------|-------|
| v0.1.0 | 2025-11-26 | Initial: Python, TS, JS, Rust | 182 |
| v0.2.0 | 2025-11-27 | +Go, Java | 212 |
| v0.3.0 | 2025-11-27 | +PHP, C#, C++, HCL, Ruby (11言語) | 286 |
| v0.4.0 | 2025-11-27 | CLI Progress Display | 286 |
| v0.5.0 | 2025-11-27 | 47x Performance (Batch DB) | 285 |
| v0.6.0 | 2025-11-27 | Background Server Management | 285 |
| v0.6.1 | 2025-11-27 | SSE/Unicode Fixes | 285 |
| **v0.6.2** | **2025-11-27** | **Partial ID, Auto Community, Query Enhancement** | **300** |

---

## 🔗 リンク

- **GitHub**: https://github.com/nahisaho/CodeGraphMCPServer
- **PyPI**: https://pypi.org/project/codegraph-mcp-server/
- **CHANGELOG**: [CHANGELOG.md](CHANGELOG.md)
