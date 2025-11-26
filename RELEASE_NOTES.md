# Release Notes - v0.3.0

**Release Date**: 2025-11-27

## 🌐 Language Expansion Release

CodeGraphMCPServer v0.3.0 は、5つの新しいプログラミング言語サポートを追加し、合計11言語に対応しました。

---

## ✨ 新機能

### 🆕 5つの新言語サポート

| 言語 | 拡張子 | 主な抽出対象 |
|------|--------|-------------|
| **PHP** | `.php` | class, interface, trait, function, method, namespace |
| **C#** | `.cs` | class, struct, interface, enum, method, property |
| **C++** | `.cpp`, `.hpp`, `.h` | class, struct, function, method, namespace, template |
| **HCL (Terraform)** | `.tf`, `.hcl` | resource, data, variable, output, module, locals |
| **Ruby** | `.rb`, `.rake` | class, module, method, singleton_method |

### 📊 言語サポート一覧 (11言語)

| 言語 | クラス | 関数 | メソッド | インポート | インターフェース | その他 |
|------|--------|------|----------|-----------|-----------------|--------|
| Python | ✅ | ✅ | ✅ | ✅ | ✅ (Protocol) | デコレータ |
| TypeScript | ✅ | ✅ | ✅ | ✅ | ✅ | 型エイリアス |
| JavaScript | ✅ | ✅ | ✅ | ✅ | - | ES6+, JSX |
| Rust | ✅ (struct) | ✅ | ✅ (impl) | ✅ | ✅ (trait) | enum |
| Go | ✅ (struct) | ✅ | ✅ | ✅ | ✅ | レシーバ |
| Java | ✅ | ✅ | ✅ | ✅ | ✅ | enum |
| **PHP** | ✅ | ✅ | ✅ | ✅ | ✅ | trait |
| **C#** | ✅ | - | ✅ | ✅ | ✅ | struct, enum |
| **C++** | ✅ | ✅ | ✅ | ✅ (include) | - | struct, template |
| **HCL** | - | - | - | - | - | resource, module |
| **Ruby** | ✅ | ✅ | ✅ | ✅ (require) | - | module, mixin |

---

## 📦 新しい依存パッケージ

```bash
pip install codegraph-mcp  # 全言語サポート含む
```

追加されたtree-sitterパッケージ:
- `tree-sitter-php>=0.23.0`
- `tree-sitter-c-sharp>=0.23.0`
- `tree-sitter-cpp>=0.23.0`
- `tree-sitter-hcl>=0.23.0`
- `tree-sitter-ruby>=0.23.0`

---

## 🧪 テスト

```
286 tests passed, 1 skipped
Coverage: 80%+
New tests: 73 (PHP: 15, C#: 15, C++: 14, HCL: 13, Ruby: 16)
```

---

## 📈 バージョン履歴

| Version | Date | Languages | Tests |
|---------|------|-----------|-------|
| v0.1.0 | 2025-11-26 | 4 (Python, TypeScript, JavaScript, Rust) | 182 |
| v0.2.0 | 2025-11-27 | 6 (+Go, Java) | 212 |
| **v0.3.0** | **2025-11-27** | **11 (+PHP, C#, C++, HCL, Ruby)** | **286** |

---

## 🔗 リンク

- **GitHub**: https://github.com/nahisaho/CodeGraphMCPServer
- **PyPI**: https://pypi.org/project/codegraph-mcp/
- **CHANGELOG**: [CHANGELOG.md](CHANGELOG.md)
