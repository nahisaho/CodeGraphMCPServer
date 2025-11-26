# CHANGE-003: v0.2.0 Language Expansion

**Status**: 📋 Planning
**Created**: 2025-11-27
**Target Version**: v0.2.0

---

## 1. Change Overview

### Summary

CodeGraphMCPServer v0.2.0 では、Go と Java の言語サポートを追加し、より多くのプロジェクトでコードグラフ分析を利用可能にします。

### Motivation

- **Go**: クラウドネイティブ開発で広く使用（Kubernetes, Docker, etc.）
- **Java**: エンタープライズ開発の主要言語（Spring Boot, Android, etc.）

### Scope

| 言語 | エンティティ | 関係 | 優先度 |
|------|-------------|------|--------|
| Go | package, func, struct, interface, method | calls, imports, implements | P0 |
| Java | class, interface, method, field, enum | calls, imports, extends, implements | P0 |

---

## 2. Requirements

### REQ-AST-004: Go Language Support

**Type**: Functional
**Priority**: P0 (Critical)
**Status**: Proposed

**Statement**: 
When the system parses Go source files (.go), it SHALL extract functions, structs, interfaces, methods, and packages as entities.

**Acceptance Criteria**:
1. `func` declarations → Function entity
2. `type X struct` → Struct entity
3. `type X interface` → Interface entity
4. `func (r Receiver) Method()` → Method entity
5. `package` statement → Module entity
6. `import` statements → Import relations

---

### REQ-AST-005: Java Language Support

**Type**: Functional
**Priority**: P0 (Critical)
**Status**: Proposed

**Statement**:
When the system parses Java source files (.java), it SHALL extract classes, interfaces, methods, fields, and enums as entities.

**Acceptance Criteria**:
1. `class X` → Class entity
2. `interface X` → Interface entity
3. `enum X` → Enum entity
4. Method declarations → Method entity
5. Field declarations → Variable entity (optional)
6. `import` statements → Import relations
7. `extends/implements` → Inheritance relations

---

## 3. Design

### 3.1 Go Language Extractor

```
src/codegraph_mcp/languages/go.py
```

**Tree-sitter Node Types**:

| Go Construct | Tree-sitter Node | Entity Type |
|--------------|------------------|-------------|
| `func main()` | `function_declaration` | Function |
| `type X struct` | `type_declaration` → `struct_type` | Struct |
| `type X interface` | `type_declaration` → `interface_type` | Interface |
| `func (r R) M()` | `method_declaration` | Method |
| `package main` | `package_clause` | Module |
| `import "fmt"` | `import_declaration` | (Relation) |

**LanguageConfig**:
```python
config = LanguageConfig(
    name="go",
    extensions=[".go"],
    tree_sitter_name="go",
    function_nodes=["function_declaration", "method_declaration"],
    class_nodes=["type_declaration"],  # struct
    import_nodes=["import_declaration"],
    interface_nodes=["type_declaration"],  # interface
)
```

---

### 3.2 Java Language Extractor

```
src/codegraph_mcp/languages/java.py
```

**Tree-sitter Node Types**:

| Java Construct | Tree-sitter Node | Entity Type |
|----------------|------------------|-------------|
| `class X` | `class_declaration` | Class |
| `interface X` | `interface_declaration` | Interface |
| `enum X` | `enum_declaration` | Enum |
| `void method()` | `method_declaration` | Method |
| `int field;` | `field_declaration` | Variable |
| `import x.y.Z;` | `import_declaration` | (Relation) |

**LanguageConfig**:
```python
config = LanguageConfig(
    name="java",
    extensions=[".java"],
    tree_sitter_name="java",
    function_nodes=["method_declaration", "constructor_declaration"],
    class_nodes=["class_declaration", "enum_declaration"],
    import_nodes=["import_declaration"],
    interface_nodes=["interface_declaration"],
)
```

---

### 3.3 Dependencies

**pyproject.toml additions**:
```toml
dependencies = [
    # ... existing ...
    "tree-sitter-go>=0.21.0",
    "tree-sitter-java>=0.21.0",
]
```

---

## 4. Implementation Tasks

### TASK-065: Go Language Parser Implementation

**Description**: Go言語のAST解析器を実装
**Estimate**: 4 hours
**Dependencies**: None

**Subtasks**:
- [ ] Create `src/codegraph_mcp/languages/go.py`
- [ ] Implement `GoExtractor` class
- [ ] Extract function entities
- [ ] Extract struct entities
- [ ] Extract interface entities
- [ ] Extract method entities (with receiver)
- [ ] Extract import relations
- [ ] Register extractor

---

### TASK-066: Go Language Tests

**Description**: Go言語パーサーのテストを作成
**Estimate**: 2 hours
**Dependencies**: TASK-065

**Subtasks**:
- [ ] Create `tests/unit/test_go.py`
- [ ] Create `tests/fixtures/go/` sample files
- [ ] Test function extraction
- [ ] Test struct extraction
- [ ] Test interface extraction
- [ ] Test method extraction
- [ ] Test import extraction

---

### TASK-067: Java Language Parser Implementation

**Description**: Java言語のAST解析器を実装
**Estimate**: 4 hours
**Dependencies**: None

**Subtasks**:
- [ ] Create `src/codegraph_mcp/languages/java.py`
- [ ] Implement `JavaExtractor` class
- [ ] Extract class entities
- [ ] Extract interface entities
- [ ] Extract enum entities
- [ ] Extract method entities
- [ ] Extract constructor entities
- [ ] Extract import relations
- [ ] Extract inheritance relations (extends/implements)
- [ ] Register extractor

---

### TASK-068: Java Language Tests

**Description**: Java言語パーサーのテストを作成
**Estimate**: 2 hours
**Dependencies**: TASK-067

**Subtasks**:
- [ ] Create `tests/unit/test_java.py`
- [ ] Create `tests/fixtures/java/` sample files
- [ ] Test class extraction
- [ ] Test interface extraction
- [ ] Test enum extraction
- [ ] Test method extraction
- [ ] Test inheritance extraction

---

### TASK-069: Integration Testing

**Description**: Go/Java統合テスト
**Estimate**: 2 hours
**Dependencies**: TASK-066, TASK-068

**Subtasks**:
- [ ] Test multi-language project indexing
- [ ] Test cross-language query (if applicable)
- [ ] Performance benchmark with real Go/Java projects

---

### TASK-070: Documentation Update

**Description**: ドキュメント更新
**Estimate**: 1 hour
**Dependencies**: TASK-069

**Subtasks**:
- [ ] Update README.md with Go/Java support
- [ ] Update docs/api.md
- [ ] Update docs/configuration.md
- [ ] Update CHANGELOG.md

---

### TASK-071: Release v0.2.0

**Description**: v0.2.0リリース
**Estimate**: 1 hour
**Dependencies**: TASK-070

**Subtasks**:
- [ ] Bump version to 0.2.0
- [ ] Build package
- [ ] Run full test suite
- [ ] Publish to PyPI
- [ ] Create GitHub Release

---

## 5. Timeline

| Week | Tasks | Milestone |
|------|-------|-----------|
| Week 1 | TASK-065, TASK-066 | Go support complete |
| Week 2 | TASK-067, TASK-068 | Java support complete |
| Week 3 | TASK-069, TASK-070, TASK-071 | v0.2.0 release |

**Target Release Date**: 2025-12-15

---

## 6. Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Tree-sitter binding issues | High | Low | Use well-tested bindings |
| Complex Java generics | Medium | Medium | Simplify to basic type extraction |
| Go interface method sets | Medium | Low | Focus on explicit declarations |

---

## 7. Success Criteria

1. **Go Support**:
   - [ ] Parse 95%+ of standard Go constructs
   - [ ] Index Go stdlib in < 60 seconds
   - [ ] All tests pass

2. **Java Support**:
   - [ ] Parse 95%+ of standard Java constructs
   - [ ] Index Spring Boot project in < 60 seconds
   - [ ] All tests pass

3. **Overall**:
   - [ ] No regression in existing tests
   - [ ] Documentation complete
   - [ ] PyPI release successful

---

## 8. References

- [Tree-sitter Go](https://github.com/tree-sitter/tree-sitter-go)
- [Tree-sitter Java](https://github.com/tree-sitter/tree-sitter-java)
- [Go Language Specification](https://go.dev/ref/spec)
- [Java Language Specification](https://docs.oracle.com/javase/specs/)

---

**Approved By**: _Pending_
**Approval Date**: _Pending_
