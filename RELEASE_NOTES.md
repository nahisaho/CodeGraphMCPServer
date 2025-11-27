# Release Notes - v0.7.0

**Release Date**: 2025-11-27

## 👀 File Watch & CI/CD Release

CodeGraphMCPServer v0.7.0は、ファイル監視による自動再インデックス機能とGitHub Actions CI/CDパイプラインを追加しました。

---

## ✨ 新機能

### File Watching (`watch` command)

```bash
# ファイル変更を監視して自動再インデックス
codegraph-mcp watch /path/to/repo

# デバウンス時間を指定（デフォルト: 1.0秒）
codegraph-mcp watch /path/to/repo --debounce 2.0

# 再インデックス後にコミュニティ検出を実行
codegraph-mcp watch /path/to/repo --community
```

**特徴:**
- リアルタイムファイル監視（watchfiles使用）
- サポート言語のファイルのみを監視
- Ctrl+Cでグレースフル終了
- 設定可能なデバウンス時間

### GitHub Actions CI/CD

**CI Workflow** (`.github/workflows/ci.yml`):
- Python 3.11/3.12でテスト実行
- ruffによるリント、mypyによる型チェック
- Codecovへのカバレッジレポート
- ビルド検証

**Release Workflow** (`.github/workflows/release.yml`):
- バージョンタグ(v*)で自動トリガー
- リリース前テスト実行
- GitHub Releaseとアーティファクト作成
- PyPIへの自動公開

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
| v0.6.2 | 2025-11-27 | Partial ID, Auto Community, Query Enhancement | 300 |
| **v0.7.0** | **2025-11-27** | **File Watch, GitHub Actions CI/CD** | **308** |

---

## 🔗 リンク

- **GitHub**: https://github.com/nahisaho/CodeGraphMCPServer
- **PyPI**: https://pypi.org/project/codegraph-mcp-server/
- **CHANGELOG**: [CHANGELOG.md](CHANGELOG.md)
