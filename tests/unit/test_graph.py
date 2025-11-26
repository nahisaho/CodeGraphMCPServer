"""
Graph Unit Tests
================

グラフエンジンの単体テスト。
"""

from pathlib import Path

import pytest

from codegraph_mcp.core.parser import (
    Entity,
    EntityType,
    Location,
    Relation,
    RelationType,
)
from codegraph_mcp.core.graph import (
    GraphEngine,
    GraphQuery,
    QueryResult,
    GraphStatistics,
)


def make_entity(
    name: str,
    entity_type: EntityType = EntityType.FUNCTION,
    file_path: str = "/test/file.py",
    line: int = 1,
) -> Entity:
    """Helper to create test entities."""
    return Entity(
        id=f"{file_path}::{name}::{line}",
        type=entity_type,
        name=name,
        qualified_name=f"{file_path}::{name}",
        location=Location(
            file_path=Path(file_path),
            start_line=line,
            start_column=0,
            end_line=line + 10,
            end_column=0,
        ),
    )


def make_relation(
    source_name: str,
    target_name: str,
    rel_type: RelationType = RelationType.CALLS,
) -> Relation:
    """Helper to create test relations."""
    return Relation(
        source_id=f"/test/file.py::{source_name}::1",
        target_id=f"/test/file.py::{target_name}::1",
        type=rel_type,
    )


class TestGraphEngine:
    """GraphEngineのテスト"""

    @pytest.mark.asyncio
    async def test_graph_initialization(self, temp_dir):
        """グラフエンジンの初期化テスト"""
        engine = GraphEngine(temp_dir)
        await engine.initialize()
        
        assert engine.db_path.exists()
        
        await engine.close()

    @pytest.mark.asyncio
    async def test_add_and_get_entity(self, temp_dir):
        """エンティティの追加と取得テスト"""
        engine = GraphEngine(temp_dir)
        await engine.initialize()
        
        entity = make_entity("test_func")
        await engine.add_entity(entity)
        
        retrieved = await engine.get_entity(entity.id)
        assert retrieved is not None
        assert retrieved.name == "test_func"
        assert retrieved.type == EntityType.FUNCTION
        
        await engine.close()

    @pytest.mark.asyncio
    async def test_add_relation(self, temp_dir):
        """リレーション追加テスト"""
        engine = GraphEngine(temp_dir)
        await engine.initialize()
        
        # Add entities first
        e1 = make_entity("func_a")
        e2 = make_entity("func_b", line=20)
        await engine.add_entity(e1)
        await engine.add_entity(e2)
        
        # Add relation
        rel = Relation(
            source_id=e1.id,
            target_id=e2.id,
            type=RelationType.CALLS,
        )
        await engine.add_relation(rel)
        
        # Verify via callees
        callees = await engine.find_callees(e1.id)
        assert len(callees) == 1
        assert callees[0].name == "func_b"
        
        await engine.close()

    @pytest.mark.asyncio
    async def test_find_callers(self, temp_dir):
        """呼び出し元検索テスト"""
        engine = GraphEngine(temp_dir)
        await engine.initialize()
        
        # func_a -> func_b, func_c -> func_b
        e_a = make_entity("func_a", line=1)
        e_b = make_entity("func_b", line=20)
        e_c = make_entity("func_c", line=40)
        
        await engine.add_entity(e_a)
        await engine.add_entity(e_b)
        await engine.add_entity(e_c)
        
        await engine.add_relation(Relation(
            source_id=e_a.id, target_id=e_b.id, type=RelationType.CALLS
        ))
        await engine.add_relation(Relation(
            source_id=e_c.id, target_id=e_b.id, type=RelationType.CALLS
        ))
        
        callers = await engine.find_callers(e_b.id)
        assert len(callers) == 2
        caller_names = {c.name for c in callers}
        assert "func_a" in caller_names
        assert "func_c" in caller_names
        
        await engine.close()

    @pytest.mark.asyncio
    async def test_query_by_name(self, temp_dir):
        """名前でのクエリテスト"""
        engine = GraphEngine(temp_dir)
        await engine.initialize()
        
        await engine.add_entity(make_entity("get_user", line=1))
        await engine.add_entity(make_entity("get_order", line=20))
        await engine.add_entity(make_entity("create_user", line=40))
        
        # Search for "get"
        result = await engine.query(GraphQuery(query="get"))
        assert len(result.entities) == 2
        
        # Search for "user"
        result = await engine.query(GraphQuery(query="user"))
        assert len(result.entities) == 2
        
        await engine.close()

    @pytest.mark.asyncio
    async def test_query_by_type(self, temp_dir):
        """型でのクエリテスト"""
        engine = GraphEngine(temp_dir)
        await engine.initialize()
        
        await engine.add_entity(make_entity(
            "MyClass", EntityType.CLASS, line=1
        ))
        await engine.add_entity(make_entity(
            "my_func", EntityType.FUNCTION, line=20
        ))
        await engine.add_entity(make_entity(
            "OtherClass", EntityType.CLASS, line=40
        ))
        
        result = await engine.query(GraphQuery(
            query="",
            entity_types=[EntityType.CLASS],
        ))
        assert len(result.entities) == 2
        for e in result.entities:
            assert e.type == EntityType.CLASS
        
        await engine.close()

    @pytest.mark.asyncio
    async def test_get_statistics(self, temp_dir):
        """統計情報取得テスト"""
        engine = GraphEngine(temp_dir)
        await engine.initialize()
        
        await engine.add_entity(make_entity("func1", EntityType.FUNCTION))
        await engine.add_entity(make_entity("func2", EntityType.FUNCTION, line=20))
        await engine.add_entity(make_entity("MyClass", EntityType.CLASS, line=40))
        
        await engine.add_relation(Relation(
            source_id=f"/test/file.py::func1::1",
            target_id=f"/test/file.py::func2::20",
            type=RelationType.CALLS,
        ))
        
        stats = await engine.get_statistics()
        assert stats.entity_count == 3
        assert stats.relation_count == 1
        assert stats.entities_by_type["function"] == 2
        assert stats.entities_by_type["class"] == 1
        
        await engine.close()

    @pytest.mark.asyncio
    async def test_search_by_name(self, temp_dir):
        """名前パターン検索テスト"""
        engine = GraphEngine(temp_dir)
        await engine.initialize()
        
        await engine.add_entity(make_entity("UserService", EntityType.CLASS))
        await engine.add_entity(make_entity("OrderService", EntityType.CLASS, line=50))
        await engine.add_entity(make_entity("get_user", EntityType.FUNCTION, line=100))
        
        results = await engine.search_by_name("Service")
        assert len(results) == 2
        
        results = await engine.search_by_name(
            "Service",
            entity_types=[EntityType.CLASS],
        )
        assert len(results) == 2
        
        await engine.close()

    @pytest.mark.asyncio
    async def test_delete_file_entities(self, temp_dir):
        """ファイルエンティティ削除テスト"""
        engine = GraphEngine(temp_dir)
        await engine.initialize()
        
        await engine.add_entity(make_entity("func1", file_path="/test/a.py"))
        await engine.add_entity(make_entity("func2", file_path="/test/a.py", line=20))
        await engine.add_entity(make_entity("func3", file_path="/test/b.py"))
        
        deleted = await engine.delete_file_entities(Path("/test/a.py"))
        assert deleted == 2
        
        stats = await engine.get_statistics()
        assert stats.entity_count == 1
        
        await engine.close()

    @pytest.mark.asyncio
    async def test_clear(self, temp_dir):
        """クリアテスト"""
        engine = GraphEngine(temp_dir)
        await engine.initialize()
        
        await engine.add_entity(make_entity("func1"))
        await engine.add_entity(make_entity("func2", line=20))
        
        await engine.clear()
        
        stats = await engine.get_statistics()
        assert stats.entity_count == 0
        
        await engine.close()


class TestGraphQuery:
    """GraphQueryのテスト"""

    def test_query_defaults(self):
        """クエリデフォルト値テスト"""
        query = GraphQuery(query="test")
        assert query.max_depth == 3
        assert query.max_results == 100
        assert query.entity_types is None

    def test_query_with_filters(self):
        """フィルター付きクエリテスト"""
        query = GraphQuery(
            query="service",
            entity_types=[EntityType.CLASS],
            file_patterns=["*.py"],
            max_results=10,
        )
        assert query.entity_types == [EntityType.CLASS]
        assert query.file_patterns == ["*.py"]
        assert query.max_results == 10


class TestQueryResult:
    """QueryResultのテスト"""

    def test_empty_result(self):
        """空の結果テスト"""
        result = QueryResult()
        assert len(result.entities) == 0
        assert len(result.relations) == 0

    def test_to_dict(self):
        """辞書変換テスト"""
        entity = make_entity("test_func")
        result = QueryResult(entities=[entity])
        
        d = result.to_dict()
        assert "entities" in d
        assert len(d["entities"]) == 1
        assert d["entities"][0]["name"] == "test_func"

    def test_str_representation(self):
        """文字列表現テスト"""
        entity = make_entity("test_func")
        result = QueryResult(entities=[entity])
        
        s = str(result)
        assert "Found 1 entities" in s
        assert "test_func" in s


class TestGraphStatistics:
    """GraphStatisticsのテスト"""

    def test_default_values(self):
        """デフォルト値テスト"""
        stats = GraphStatistics()
        assert stats.entity_count == 0
        assert stats.relation_count == 0
        assert stats.community_count == 0
