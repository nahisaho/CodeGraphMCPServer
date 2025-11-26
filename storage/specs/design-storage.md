# CodeGraph MCP Server ストレージ設計書

**Project**: CodeGraph MCP Server  
**Version**: 1.0.0  
**Created**: 2025-11-26  
**Status**: Draft  
**Document Type**: C4 Model - Component Diagram (Level 3)

---

## 1. ドキュメント概要

### 1.1 目的

本ドキュメントは、CodeGraph MCP Serverのストレージ層の詳細設計を記述します。

### 1.2 スコープ

- SQLiteグラフストレージ設計
- ファイルキャッシュ設計
- ベクトルストア設計
- データ永続化戦略

### 1.3 対象要件

| 要件グループ | 要件ID | 説明 |
|-------------|--------|------|
| ストレージ | REQ-STR-001 ~ REQ-STR-004 | データ永続化 |
| グラフエンジン | REQ-GRF-005, REQ-GRF-006 | SQLite/インデックス |
| 非機能 | REQ-NFR-005, REQ-NFR-006 | メモリ/ディスク |

---

## 2. ストレージアーキテクチャ

### 2.1 全体構成

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Storage Container                                    │
│                         src/codegraph_mcp/storage/                          │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         Storage Manager                                  ││
│  │                                                                          ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  ││
│  │  │ SQLiteStore  │  │  FileCache   │  │ VectorStore  │                  ││
│  │  │ (Graph Data) │  │ (AST Cache)  │  │ (Embeddings) │                  ││
│  │  │              │  │              │  │              │                  ││
│  │  │ REQ-STR-001  │  │ REQ-STR-002  │  │ REQ-STR-003  │                  ││
│  │  │ REQ-GRF-005  │  │              │  │              │                  ││
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  ││
│  │         │                 │                 │                           ││
│  └─────────┼─────────────────┼─────────────────┼───────────────────────────┘│
│            │                 │                 │                             │
│            ▼                 ▼                 ▼                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         File System                                      ││
│  │                                                                          ││
│  │  ~/.codegraph/                                                          ││
│  │  ├── {repo_hash}/                                                       ││
│  │  │   ├── index.db              ← SQLite Database                       ││
│  │  │   ├── cache/                ← AST Cache                             ││
│  │  │   │   └── {file_hash}.json                                          ││
│  │  │   └── vectors/              ← Vector Store                          ││
│  │  │       └── embeddings.bin                                            ││
│  │  └── config.json               ← Global Config                         ││
│  │                                                                          ││
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 ディレクトリ構成

```
~/.codegraph/
├── config.json                    # グローバル設定
├── {repo_hash_1}/                 # リポジトリ1のデータ
│   ├── index.db                   # SQLiteデータベース
│   ├── cache/                     # ASTキャッシュ
│   │   ├── abc123.json            # ファイルハッシュ.json
│   │   └── def456.json
│   ├── vectors/                   # ベクトルストア
│   │   └── embeddings.bin
│   └── meta.json                  # リポジトリメタデータ
│
├── {repo_hash_2}/                 # リポジトリ2のデータ
│   └── ...
│
└── logs/                          # ログファイル
    └── codegraph.log
```

---

## 3. SQLiteストレージ設計

### 3.1 スキーマ定義

```sql
-- storage/schema.sql (REQ-STR-001, REQ-GRF-005)

-- ========================================
-- エンティティテーブル
-- ========================================
CREATE TABLE IF NOT EXISTS entities (
    -- 主キー
    id TEXT PRIMARY KEY,
    
    -- 基本情報
    type TEXT NOT NULL CHECK(type IN (
        'file', 'module', 'class', 'function', 
        'method', 'interface', 'import'
    )),
    name TEXT NOT NULL,
    qualified_name TEXT,
    
    -- ロケーション情報
    file_path TEXT NOT NULL,
    start_line INTEGER NOT NULL CHECK(start_line >= 1),
    end_line INTEGER NOT NULL CHECK(end_line >= start_line),
    
    -- コンテンツ
    signature TEXT,
    docstring TEXT,
    source_code TEXT,
    
    -- セマンティック情報
    embedding BLOB,           -- ベクトル埋め込み
    community_id INTEGER,     -- コミュニティID
    description TEXT,         -- LLM生成の説明
    
    -- メタデータ
    language TEXT,
    complexity INTEGER,       -- 循環的複雑度（オプション）
    
    -- 監査情報
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- 関係テーブル
-- ========================================
CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- エンティティ参照
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    
    -- 関係情報
    type TEXT NOT NULL CHECK(type IN (
        'calls', 'imports', 'inherits', 
        'contains', 'implements', 'uses'
    )),
    weight REAL DEFAULT 1.0 CHECK(weight >= 0),
    
    -- 追加情報
    metadata TEXT,  -- JSON形式
    line_number INTEGER,  -- 呼び出し行番号
    
    -- 監査情報
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外部キー制約
    FOREIGN KEY (source_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES entities(id) ON DELETE CASCADE
);

-- ========================================
-- コミュニティテーブル（GraphRAG用）
-- ========================================
CREATE TABLE IF NOT EXISTS communities (
    id INTEGER PRIMARY KEY,
    
    -- 階層情報
    level INTEGER NOT NULL DEFAULT 0 CHECK(level >= 0),
    parent_id INTEGER,
    
    -- コンテンツ
    name TEXT,
    summary TEXT,           -- LLM生成の要約
    
    -- 統計情報
    member_count INTEGER DEFAULT 0,
    
    -- 監査情報
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_id) REFERENCES communities(id) ON DELETE SET NULL
);

-- ========================================
-- インデックス情報テーブル
-- ========================================
CREATE TABLE IF NOT EXISTS index_info (
    id INTEGER PRIMARY KEY,
    
    -- リポジトリ情報
    repo_path TEXT NOT NULL UNIQUE,
    repo_name TEXT,
    
    -- Git情報
    last_commit TEXT,
    branch TEXT,
    
    -- 統計情報
    total_files INTEGER DEFAULT 0,
    total_entities INTEGER DEFAULT 0,
    total_relations INTEGER DEFAULT 0,
    
    -- タイミング情報
    last_indexed_at TIMESTAMP,
    index_duration_ms REAL,
    
    -- 監査情報
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- ファイル状態テーブル（増分インデックス用）
-- ========================================
CREATE TABLE IF NOT EXISTS file_states (
    file_path TEXT PRIMARY KEY,
    
    -- ファイル情報
    content_hash TEXT NOT NULL,     -- ファイル内容のハッシュ
    size_bytes INTEGER,
    
    -- 状態
    last_modified TIMESTAMP,
    last_indexed_at TIMESTAMP,
    
    -- 解析結果
    entity_count INTEGER DEFAULT 0,
    relation_count INTEGER DEFAULT 0,
    parse_errors TEXT,              -- JSON配列
    
    -- 監査情報
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- インデックス定義 (REQ-GRF-006)
-- ========================================

-- エンティティインデックス
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_file ON entities(file_path);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_qualified ON entities(qualified_name);
CREATE INDEX IF NOT EXISTS idx_entities_community ON entities(community_id);
CREATE INDEX IF NOT EXISTS idx_entities_language ON entities(language);

-- 関係インデックス
CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id);
CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id);
CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(type);

-- 複合インデックス（クエリ最適化用）
CREATE INDEX IF NOT EXISTS idx_relations_src_type ON relations(source_id, type);
CREATE INDEX IF NOT EXISTS idx_relations_tgt_type ON relations(target_id, type);
CREATE INDEX IF NOT EXISTS idx_entities_file_type ON entities(file_path, type);

-- コミュニティインデックス
CREATE INDEX IF NOT EXISTS idx_communities_level ON communities(level);
CREATE INDEX IF NOT EXISTS idx_communities_parent ON communities(parent_id);

-- ファイル状態インデックス
CREATE INDEX IF NOT EXISTS idx_file_states_hash ON file_states(content_hash);

-- ========================================
-- トリガー定義
-- ========================================

-- エンティティ更新時にupdated_atを更新
CREATE TRIGGER IF NOT EXISTS update_entity_timestamp
AFTER UPDATE ON entities
BEGIN
    UPDATE entities SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- コミュニティ更新時にupdated_atを更新
CREATE TRIGGER IF NOT EXISTS update_community_timestamp
AFTER UPDATE ON communities
BEGIN
    UPDATE communities SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- ファイル状態更新時にupdated_atを更新
CREATE TRIGGER IF NOT EXISTS update_file_state_timestamp
AFTER UPDATE ON file_states
BEGIN
    UPDATE file_states SET updated_at = CURRENT_TIMESTAMP 
    WHERE file_path = NEW.file_path;
END;
```

### 3.2 SQLiteストアクラス

```python
# storage/sqlite.py

import aiosqlite
from pathlib import Path
from typing import Optional, AsyncIterator
from contextlib import asynccontextmanager

class SQLiteStore:
    """SQLiteベースのグラフストレージ (REQ-STR-001)"""
    
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self) -> None:
        """データベースに接続"""
        # ディレクトリ作成
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 接続
        self._connection = await aiosqlite.connect(
            self._db_path,
            isolation_level=None  # autocommit
        )
        
        # 設定
        await self._connection.execute("PRAGMA journal_mode=WAL")
        await self._connection.execute("PRAGMA synchronous=NORMAL")
        await self._connection.execute("PRAGMA cache_size=10000")
        await self._connection.execute("PRAGMA temp_store=MEMORY")
        
        # スキーマ初期化
        await self._init_schema()
    
    async def close(self) -> None:
        """接続を閉じる"""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def _init_schema(self) -> None:
        """スキーマを初期化"""
        schema_path = Path(__file__).parent / "schema.sql"
        schema = schema_path.read_text()
        await self._connection.executescript(schema)
    
    # ========================================
    # エンティティ操作
    # ========================================
    
    async def add_entity(self, entity: Entity) -> str:
        """エンティティを追加"""
        sql = """
            INSERT OR REPLACE INTO entities (
                id, type, name, qualified_name,
                file_path, start_line, end_line,
                signature, docstring, source_code,
                embedding, community_id, language
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        await self._connection.execute(sql, (
            entity.id,
            entity.type.value,
            entity.name,
            entity.qualified_name,
            entity.file_path,
            entity.start_line,
            entity.end_line,
            entity.signature,
            entity.docstring,
            entity.source_code,
            entity.embedding,
            entity.community_id,
            self._detect_language(entity.file_path)
        ))
        return entity.id
    
    async def add_entities_batch(
        self, 
        entities: list[Entity]
    ) -> int:
        """エンティティを一括追加（パフォーマンス最適化）"""
        sql = """
            INSERT OR REPLACE INTO entities (
                id, type, name, qualified_name,
                file_path, start_line, end_line,
                signature, docstring, source_code,
                embedding, community_id, language
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        data = [
            (
                e.id, e.type.value, e.name, e.qualified_name,
                e.file_path, e.start_line, e.end_line,
                e.signature, e.docstring, e.source_code,
                e.embedding, e.community_id,
                self._detect_language(e.file_path)
            )
            for e in entities
        ]
        await self._connection.executemany(sql, data)
        return len(entities)
    
    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        """エンティティを取得"""
        sql = "SELECT * FROM entities WHERE id = ?"
        async with self._connection.execute(sql, (entity_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_entity(row)
        return None
    
    async def get_entity_by_name(
        self, 
        name: str, 
        entity_type: str = None
    ) -> Optional[Entity]:
        """名前でエンティティを取得"""
        if entity_type:
            sql = """
                SELECT * FROM entities 
                WHERE (name = ? OR qualified_name = ?) AND type = ?
            """
            params = (name, name, entity_type)
        else:
            sql = """
                SELECT * FROM entities 
                WHERE name = ? OR qualified_name = ?
            """
            params = (name, name)
        
        async with self._connection.execute(sql, params) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_entity(row)
        return None
    
    async def get_entities_by_file(
        self, 
        file_path: str
    ) -> list[Entity]:
        """ファイル内のエンティティを取得"""
        sql = """
            SELECT * FROM entities 
            WHERE file_path = ?
            ORDER BY start_line
        """
        async with self._connection.execute(sql, (file_path,)) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
    
    async def search_entities(
        self,
        query: str,
        entity_types: list[str] = None,
        limit: int = 100
    ) -> list[Entity]:
        """エンティティを検索"""
        conditions = ["(name LIKE ? OR qualified_name LIKE ? OR docstring LIKE ?)"]
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]
        
        if entity_types:
            placeholders = ','.join('?' * len(entity_types))
            conditions.append(f"type IN ({placeholders})")
            params.extend(entity_types)
        
        sql = f"""
            SELECT * FROM entities 
            WHERE {' AND '.join(conditions)}
            LIMIT ?
        """
        params.append(limit)
        
        async with self._connection.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
    
    async def delete_entities_by_file(self, file_path: str) -> int:
        """ファイルのエンティティを削除"""
        # まず関係を削除
        await self._connection.execute("""
            DELETE FROM relations 
            WHERE source_id IN (SELECT id FROM entities WHERE file_path = ?)
               OR target_id IN (SELECT id FROM entities WHERE file_path = ?)
        """, (file_path, file_path))
        
        # エンティティを削除
        cursor = await self._connection.execute(
            "DELETE FROM entities WHERE file_path = ?",
            (file_path,)
        )
        return cursor.rowcount
    
    # ========================================
    # 関係操作
    # ========================================
    
    async def add_relation(self, relation: Relation) -> int:
        """関係を追加"""
        sql = """
            INSERT INTO relations (
                source_id, target_id, type, weight, metadata, line_number
            ) VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor = await self._connection.execute(sql, (
            relation.source_id,
            relation.target_id,
            relation.type.value,
            relation.weight,
            json.dumps(relation.metadata) if relation.metadata else None,
            relation.line_number
        ))
        return cursor.lastrowid
    
    async def add_relations_batch(
        self, 
        relations: list[Relation]
    ) -> int:
        """関係を一括追加"""
        sql = """
            INSERT INTO relations (
                source_id, target_id, type, weight, metadata, line_number
            ) VALUES (?, ?, ?, ?, ?, ?)
        """
        data = [
            (
                r.source_id, r.target_id, r.type.value, r.weight,
                json.dumps(r.metadata) if r.metadata else None,
                r.line_number
            )
            for r in relations
        ]
        await self._connection.executemany(sql, data)
        return len(relations)
    
    async def get_relations_by_source(
        self,
        source_id: str,
        relation_types: list[str] = None
    ) -> list[Relation]:
        """ソースIDで関係を取得"""
        if relation_types:
            placeholders = ','.join('?' * len(relation_types))
            sql = f"""
                SELECT * FROM relations 
                WHERE source_id = ? AND type IN ({placeholders})
            """
            params = [source_id] + relation_types
        else:
            sql = "SELECT * FROM relations WHERE source_id = ?"
            params = [source_id]
        
        async with self._connection.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_relation(row) for row in rows]
    
    async def get_relations_by_target(
        self,
        target_id: str,
        relation_types: list[str] = None
    ) -> list[Relation]:
        """ターゲットIDで関係を取得"""
        if relation_types:
            placeholders = ','.join('?' * len(relation_types))
            sql = f"""
                SELECT * FROM relations 
                WHERE target_id = ? AND type IN ({placeholders})
            """
            params = [target_id] + relation_types
        else:
            sql = "SELECT * FROM relations WHERE target_id = ?"
            params = [target_id]
        
        async with self._connection.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_relation(row) for row in rows]
    
    # ========================================
    # 統計・メタ情報
    # ========================================
    
    async def get_stats(self) -> GraphStats:
        """統計情報を取得"""
        # エンティティ数
        async with self._connection.execute(
            "SELECT COUNT(*) FROM entities"
        ) as cursor:
            total_entities = (await cursor.fetchone())[0]
        
        # 関係数
        async with self._connection.execute(
            "SELECT COUNT(*) FROM relations"
        ) as cursor:
            total_relations = (await cursor.fetchone())[0]
        
        # エンティティ内訳
        async with self._connection.execute(
            "SELECT type, COUNT(*) FROM entities GROUP BY type"
        ) as cursor:
            entity_breakdown = dict(await cursor.fetchall())
        
        # 言語内訳
        async with self._connection.execute(
            "SELECT language, COUNT(*) FROM entities GROUP BY language"
        ) as cursor:
            language_breakdown = dict(await cursor.fetchall())
        
        # ファイル数
        async with self._connection.execute(
            "SELECT COUNT(DISTINCT file_path) FROM entities"
        ) as cursor:
            total_files = (await cursor.fetchone())[0]
        
        # インデックス情報
        async with self._connection.execute(
            "SELECT last_indexed_at, index_duration_ms FROM index_info LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            last_indexed_at = row[0] if row else None
            index_duration_ms = row[1] if row else 0
        
        return GraphStats(
            total_files=total_files,
            total_entities=total_entities,
            total_relations=total_relations,
            entity_breakdown=entity_breakdown,
            language_breakdown=language_breakdown,
            last_indexed_at=last_indexed_at,
            index_duration_ms=index_duration_ms
        )
```

---

## 4. ファイルキャッシュ設計

### 4.1 キャッシュ構造

```python
# storage/cache.py (REQ-STR-002)

import hashlib
import json
from pathlib import Path
from typing import Optional
from dataclasses import asdict

@dataclass
class CacheEntry:
    """キャッシュエントリ"""
    file_path: str
    content_hash: str
    language: str
    entities: list[dict]
    relations: list[dict]
    parse_errors: list[str]
    cached_at: str

class FileCache:
    """ファイルキャッシュマネージャー"""
    
    def __init__(self, cache_dir: str):
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, file_path: str) -> Path:
        """キャッシュファイルパスを取得"""
        # ファイルパスのハッシュをキャッシュキーとして使用
        path_hash = hashlib.md5(file_path.encode()).hexdigest()
        return self._cache_dir / f"{path_hash}.json"
    
    def _compute_content_hash(self, content: str) -> str:
        """コンテンツハッシュを計算"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def get(
        self, 
        file_path: str, 
        content: str
    ) -> Optional[CacheEntry]:
        """キャッシュを取得"""
        cache_path = self._get_cache_path(file_path)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            entry = CacheEntry(**data)
            
            # コンテンツハッシュを検証
            current_hash = self._compute_content_hash(content)
            if entry.content_hash != current_hash:
                # ファイルが変更されている
                return None
            
            return entry
            
        except (json.JSONDecodeError, TypeError, KeyError):
            # キャッシュが破損している
            cache_path.unlink(missing_ok=True)
            return None
    
    async def set(
        self,
        file_path: str,
        content: str,
        language: str,
        entities: list[Entity],
        relations: list[Relation],
        parse_errors: list[str]
    ) -> None:
        """キャッシュを設定"""
        cache_path = self._get_cache_path(file_path)
        
        entry = CacheEntry(
            file_path=file_path,
            content_hash=self._compute_content_hash(content),
            language=language,
            entities=[asdict(e) for e in entities],
            relations=[asdict(r) for r in relations],
            parse_errors=parse_errors,
            cached_at=datetime.utcnow().isoformat()
        )
        
        with open(cache_path, 'w') as f:
            json.dump(asdict(entry), f, indent=2)
    
    async def invalidate(self, file_path: str) -> None:
        """キャッシュを無効化"""
        cache_path = self._get_cache_path(file_path)
        cache_path.unlink(missing_ok=True)
    
    async def clear(self) -> int:
        """全キャッシュをクリア"""
        count = 0
        for cache_file in self._cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        return count
    
    async def get_cache_stats(self) -> dict:
        """キャッシュ統計を取得"""
        cache_files = list(self._cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "entry_count": len(cache_files),
            "total_size_bytes": total_size,
            "cache_dir": str(self._cache_dir)
        }
```

---

## 5. ベクトルストア設計

### 5.1 ベクトルストア構造

```python
# storage/vectors.py (REQ-STR-003)

import numpy as np
from pathlib import Path
from typing import Optional
import struct

class VectorStore:
    """ベクトルストア（埋め込み管理）"""
    
    VECTOR_DIM = 384  # sentence-transformers default
    
    def __init__(self, store_path: str):
        self._store_path = Path(store_path)
        self._store_path.mkdir(parents=True, exist_ok=True)
        
        self._embeddings_file = self._store_path / "embeddings.bin"
        self._index_file = self._store_path / "index.json"
        
        self._id_to_offset: dict[str, int] = {}
        self._embeddings: Optional[np.memmap] = None
        
        self._load_index()
    
    def _load_index(self) -> None:
        """インデックスを読み込み"""
        if self._index_file.exists():
            with open(self._index_file, 'r') as f:
                self._id_to_offset = json.load(f)
    
    def _save_index(self) -> None:
        """インデックスを保存"""
        with open(self._index_file, 'w') as f:
            json.dump(self._id_to_offset, f)
    
    async def add(
        self, 
        entity_id: str, 
        embedding: np.ndarray
    ) -> None:
        """埋め込みを追加"""
        if embedding.shape[0] != self.VECTOR_DIM:
            raise ValueError(
                f"Invalid embedding dimension: {embedding.shape[0]}, "
                f"expected {self.VECTOR_DIM}"
            )
        
        # ファイルに追記
        offset = 0
        if self._embeddings_file.exists():
            offset = self._embeddings_file.stat().st_size // (self.VECTOR_DIM * 4)
        
        with open(self._embeddings_file, 'ab') as f:
            f.write(embedding.astype(np.float32).tobytes())
        
        # インデックス更新
        self._id_to_offset[entity_id] = offset
        self._save_index()
    
    async def add_batch(
        self, 
        embeddings: dict[str, np.ndarray]
    ) -> int:
        """埋め込みを一括追加"""
        if not embeddings:
            return 0
        
        offset = 0
        if self._embeddings_file.exists():
            offset = self._embeddings_file.stat().st_size // (self.VECTOR_DIM * 4)
        
        with open(self._embeddings_file, 'ab') as f:
            for entity_id, embedding in embeddings.items():
                if embedding.shape[0] != self.VECTOR_DIM:
                    continue
                
                f.write(embedding.astype(np.float32).tobytes())
                self._id_to_offset[entity_id] = offset
                offset += 1
        
        self._save_index()
        return len(embeddings)
    
    async def get(self, entity_id: str) -> Optional[np.ndarray]:
        """埋め込みを取得"""
        if entity_id not in self._id_to_offset:
            return None
        
        offset = self._id_to_offset[entity_id]
        
        with open(self._embeddings_file, 'rb') as f:
            f.seek(offset * self.VECTOR_DIM * 4)
            data = f.read(self.VECTOR_DIM * 4)
            return np.frombuffer(data, dtype=np.float32)
    
    async def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        entity_ids: list[str] = None
    ) -> list[tuple[str, float]]:
        """類似ベクトルを検索"""
        if not self._embeddings_file.exists():
            return []
        
        # 全埋め込みを読み込み
        embeddings = np.memmap(
            self._embeddings_file,
            dtype=np.float32,
            mode='r',
            shape=(len(self._id_to_offset), self.VECTOR_DIM)
        )
        
        # コサイン類似度を計算
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        similarities = np.dot(embeddings_norm, query_norm)
        
        # フィルタリング（指定IDのみ）
        if entity_ids:
            mask = np.zeros(len(self._id_to_offset), dtype=bool)
            id_list = list(self._id_to_offset.keys())
            for i, eid in enumerate(id_list):
                if eid in entity_ids:
                    mask[i] = True
            similarities = np.where(mask, similarities, -1)
        
        # Top-K取得
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        id_list = list(self._id_to_offset.keys())
        results = [
            (id_list[i], float(similarities[i]))
            for i in top_indices
            if similarities[i] > 0
        ]
        
        return results
    
    async def delete(self, entity_id: str) -> bool:
        """埋め込みを削除（論理削除）"""
        if entity_id in self._id_to_offset:
            del self._id_to_offset[entity_id]
            self._save_index()
            return True
        return False
    
    async def rebuild(self) -> None:
        """ベクトルストアを再構築（論理削除の反映）"""
        if not self._embeddings_file.exists():
            return
        
        # 有効なエントリのみを新ファイルに書き出し
        new_file = self._store_path / "embeddings_new.bin"
        new_offsets = {}
        
        with open(new_file, 'wb') as f_out:
            with open(self._embeddings_file, 'rb') as f_in:
                offset = 0
                for entity_id, old_offset in self._id_to_offset.items():
                    f_in.seek(old_offset * self.VECTOR_DIM * 4)
                    data = f_in.read(self.VECTOR_DIM * 4)
                    f_out.write(data)
                    new_offsets[entity_id] = offset
                    offset += 1
        
        # ファイル入れ替え
        self._embeddings_file.unlink()
        new_file.rename(self._embeddings_file)
        
        self._id_to_offset = new_offsets
        self._save_index()
```

---

## 6. ストレージマネージャー設計

### 6.1 統合マネージャー

```python
# storage/__init__.py

from pathlib import Path
import hashlib

class StorageManager:
    """ストレージ統合マネージャー"""
    
    def __init__(self, base_dir: str = None):
        self._base_dir = Path(base_dir or Path.home() / ".codegraph")
        self._base_dir.mkdir(parents=True, exist_ok=True)
        
        self._stores: dict[str, tuple[SQLiteStore, FileCache, VectorStore]] = {}
    
    def _get_repo_hash(self, repo_path: str) -> str:
        """リポジトリパスのハッシュを取得"""
        return hashlib.md5(repo_path.encode()).hexdigest()[:12]
    
    def _get_repo_dir(self, repo_path: str) -> Path:
        """リポジトリのストレージディレクトリを取得"""
        repo_hash = self._get_repo_hash(repo_path)
        return self._base_dir / repo_hash
    
    async def get_stores(
        self, 
        repo_path: str
    ) -> tuple[SQLiteStore, FileCache, VectorStore]:
        """リポジトリのストアを取得"""
        if repo_path in self._stores:
            return self._stores[repo_path]
        
        repo_dir = self._get_repo_dir(repo_path)
        repo_dir.mkdir(parents=True, exist_ok=True)
        
        # 各ストアを初期化
        sqlite_store = SQLiteStore(str(repo_dir / "index.db"))
        await sqlite_store.connect()
        
        file_cache = FileCache(str(repo_dir / "cache"))
        vector_store = VectorStore(str(repo_dir / "vectors"))
        
        # メタデータを保存
        await self._save_repo_meta(repo_dir, repo_path)
        
        stores = (sqlite_store, file_cache, vector_store)
        self._stores[repo_path] = stores
        
        return stores
    
    async def _save_repo_meta(self, repo_dir: Path, repo_path: str) -> None:
        """リポジトリメタデータを保存"""
        meta_file = repo_dir / "meta.json"
        meta = {
            "repo_path": repo_path,
            "created_at": datetime.utcnow().isoformat()
        }
        with open(meta_file, 'w') as f:
            json.dump(meta, f, indent=2)
    
    async def list_repositories(self) -> list[dict]:
        """管理中のリポジトリ一覧を取得"""
        repos = []
        for repo_dir in self._base_dir.iterdir():
            if not repo_dir.is_dir():
                continue
            
            meta_file = repo_dir / "meta.json"
            if meta_file.exists():
                with open(meta_file, 'r') as f:
                    meta = json.load(f)
                    repos.append(meta)
        
        return repos
    
    async def delete_repository(self, repo_path: str) -> bool:
        """リポジトリのストレージを削除"""
        repo_dir = self._get_repo_dir(repo_path)
        
        if not repo_dir.exists():
            return False
        
        # 接続を閉じる
        if repo_path in self._stores:
            sqlite_store, _, _ = self._stores[repo_path]
            await sqlite_store.close()
            del self._stores[repo_path]
        
        # ディレクトリを削除
        import shutil
        shutil.rmtree(repo_dir)
        
        return True
    
    async def close_all(self) -> None:
        """すべての接続を閉じる"""
        for repo_path, (sqlite_store, _, _) in self._stores.items():
            await sqlite_store.close()
        self._stores.clear()
```

---

## 7. データ整合性

### 7.1 トランザクション管理

```python
# storage/transaction.py

from contextlib import asynccontextmanager

class TransactionManager:
    """トランザクションマネージャー"""
    
    def __init__(self, sqlite_store: SQLiteStore):
        self._store = sqlite_store
    
    @asynccontextmanager
    async def transaction(self):
        """トランザクションコンテキスト"""
        conn = self._store._connection
        
        await conn.execute("BEGIN TRANSACTION")
        try:
            yield
            await conn.execute("COMMIT")
        except Exception:
            await conn.execute("ROLLBACK")
            raise
    
    async def batch_update(
        self,
        entities: list[Entity],
        relations: list[Relation]
    ) -> None:
        """バッチ更新（トランザクション内で実行）"""
        async with self.transaction():
            await self._store.add_entities_batch(entities)
            await self._store.add_relations_batch(relations)
```

### 7.2 バックアップ・復旧

```python
# storage/backup.py

import shutil
from datetime import datetime

class BackupManager:
    """バックアップマネージャー"""
    
    def __init__(self, storage_manager: StorageManager):
        self._storage = storage_manager
    
    async def create_backup(self, repo_path: str) -> str:
        """バックアップを作成"""
        repo_dir = self._storage._get_repo_dir(repo_path)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = repo_dir.parent / f"{repo_dir.name}_backup_{timestamp}"
        
        shutil.copytree(repo_dir, backup_dir)
        
        return str(backup_dir)
    
    async def restore_backup(
        self, 
        repo_path: str, 
        backup_path: str
    ) -> bool:
        """バックアップから復旧 (REQ-NFR-008)"""
        repo_dir = self._storage._get_repo_dir(repo_path)
        backup_dir = Path(backup_path)
        
        if not backup_dir.exists():
            return False
        
        # 現在のディレクトリを削除
        if repo_dir.exists():
            shutil.rmtree(repo_dir)
        
        # バックアップからコピー
        shutil.copytree(backup_dir, repo_dir)
        
        return True
    
    async def list_backups(self, repo_path: str) -> list[str]:
        """バックアップ一覧を取得"""
        repo_dir = self._storage._get_repo_dir(repo_path)
        base_name = repo_dir.name
        
        backups = []
        for d in repo_dir.parent.iterdir():
            if d.is_dir() and d.name.startswith(f"{base_name}_backup_"):
                backups.append(str(d))
        
        return sorted(backups, reverse=True)
```

---

## 8. パフォーマンス最適化

### 8.1 最適化戦略

| 戦略 | 説明 | 対象要件 |
|------|------|---------|
| WALモード | 書き込みパフォーマンス向上 | REQ-NFR-001 |
| バッチ挿入 | 一括挿入による高速化 | REQ-NFR-001 |
| インデックス | クエリ高速化 | REQ-NFR-003 |
| 接続プール | 接続再利用 | REQ-NFR-003 |
| キャッシュ | パース結果の再利用 | REQ-NFR-002 |

### 8.2 メモリ管理

```python
# storage/memory.py (REQ-NFR-005)

class MemoryManager:
    """メモリ管理"""
    
    MAX_CACHE_SIZE_MB = 100
    MAX_BATCH_SIZE = 1000
    
    def __init__(self, file_cache: FileCache):
        self._cache = file_cache
    
    async def enforce_limits(self) -> None:
        """メモリ制限を強制"""
        stats = await self._cache.get_cache_stats()
        
        if stats["total_size_bytes"] > self.MAX_CACHE_SIZE_MB * 1024 * 1024:
            # 古いキャッシュを削除
            await self._evict_old_entries()
    
    async def _evict_old_entries(self) -> None:
        """古いエントリを削除（LRU）"""
        # 実装省略
        pass
```

---

## 9. 要件トレーサビリティ

### 9.1 コンポーネント → 要件マッピング

| コンポーネント | ファイル | 要件ID | Phase |
|---------------|---------|--------|-------|
| SQLiteStore | storage/sqlite.py | REQ-STR-001, REQ-GRF-005, REQ-GRF-006 | P0 |
| FileCache | storage/cache.py | REQ-STR-002 | P0 |
| VectorStore | storage/vectors.py | REQ-STR-003 | P1 |
| StorageManager | storage/__init__.py | REQ-STR-001~003 | P0 |
| BackupManager | storage/backup.py | REQ-NFR-008 | P0 |
| MemoryManager | storage/memory.py | REQ-NFR-005 | P0 |

---

## 10. 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|------------|------|----------|--------|
| 1.0.0 | 2025-11-26 | 初版作成 | System |

---

**Document Status**: Draft  
**Constitutional Compliance**: Article I (Library-First), Article VIII (No Abstraction) ✓
