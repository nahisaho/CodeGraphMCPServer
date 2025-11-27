# Release Notes - v0.7.1

**Release Date**: 2025-11-27

## 🇨 C Language Support Release

CodeGraphMCPServer v0.7.1は、C言語（`.c`ファイル）のサポートを追加し、対応言語数が12言語になりました。

---

## ✨ 新機能

### C Language Support

```bash
# C言語プロジェクトのインデックス作成
codegraph-mcp index /path/to/c-project --full

# Linux Kernel kernel/ディレクトリの例
# 54,748 entities, 142,532 relations in 5.77s
```

**対応拡張子:**
- `.c` - Pure C source files (NEW)
- `.cpp`, `.cc`, `.cxx` - C++ source files
- `.h`, `.hpp`, `.hxx` - Header files

**検証済み大規模Cプロジェクト:**
| プロジェクト | ファイル数 | エンティティ数 | リレーション数 | 時間 |
|-------------|-----------|--------------|--------------|------|
| Linux Kernel (kernel/) | 596 | 54,748 | 142,532 | 5.77s |

---

## 📈 バージョン履歴

| Version | Date | Highlights | Languages | Tests |
|---------|------|------------|-----------|-------|
| v0.1.0 | 2025-11-26 | Initial: Python, TS, JS, Rust | 4 | 182 |
| v0.2.0 | 2025-11-27 | +Go, Java | 6 | 212 |
| v0.3.0 | 2025-11-27 | +PHP, C#, C++, HCL, Ruby | 11 | 286 |
| v0.4.0 | 2025-11-27 | CLI Progress Display | 11 | 286 |
| v0.5.0 | 2025-11-27 | 47x Performance (Batch DB) | 11 | 285 |
| v0.6.0 | 2025-11-27 | Background Server Management | 11 | 285 |
| v0.6.1 | 2025-11-27 | SSE/Unicode Fixes | 11 | 285 |
| v0.6.2 | 2025-11-27 | Partial ID, Auto Community | 11 | 300 |
| v0.7.0 | 2025-11-27 | File Watch, GitHub Actions CI/CD | 11 | 308 |
| **v0.7.1** | **2025-11-27** | **C Language Support** | **12** | **308** |

---

## 🌐 対応言語（12言語）

| 言語 | 拡張子 | クラス | 関数 | メソッド |
|------|--------|--------|------|----------|
| Python | .py, .pyi | ✅ | ✅ | ✅ |
| TypeScript | .ts, .tsx | ✅ | ✅ | ✅ |
| JavaScript | .js, .jsx | ✅ | ✅ | ✅ |
| Rust | .rs | ✅ | ✅ | ✅ |
| Go | .go | ✅ | ✅ | ✅ |
| Java | .java | ✅ | ✅ | ✅ |
| PHP | .php | ✅ | ✅ | ✅ |
| C# | .cs | ✅ | - | ✅ |
| **C** | **.c** | - | **✅** | - |
| C++ | .cpp, .cc, .cxx | ✅ | ✅ | ✅ |
| HCL | .hcl, .tf | - | - | - |
| Ruby | .rb | ✅ | ✅ | ✅ |

---

## 🔗 リンク

- **GitHub**: https://github.com/nahisaho/CodeGraphMCPServer
- **PyPI**: https://pypi.org/project/codegraph-mcp-server/
- **CHANGELOG**: [CHANGELOG.md](CHANGELOG.md)
