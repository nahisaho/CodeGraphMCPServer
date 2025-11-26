#!/usr/bin/env python3
"""
Basic Usage Example
===================

CodeGraphMCPServerの基本的な使用方法を示す例です。

実行方法:
    cd /path/to/CodeGraphMCPServer
    source .venv/bin/activate
    python examples/basic_usage.py
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from codegraph_mcp.core.parser import ASTParser
from codegraph_mcp.core.graph import GraphEngine, GraphQuery
from codegraph_mcp.core.indexer import Indexer
from codegraph_mcp.config import Config


async def example_1_index_repository():
    """
    例1: リポジトリをインデックスする
    
    この例では、テストフィクスチャディレクトリをインデックスします。
    """
    print("=" * 60)
    print("例1: リポジトリのインデックス作成")
    print("=" * 60)
    
    # テストフィクスチャのパス
    fixture_path = project_root / "tests" / "fixtures" / "python"
    
    if not fixture_path.exists():
        print(f"フィクスチャが見つかりません: {fixture_path}")
        return
    
    print(f"対象ディレクトリ: {fixture_path}")
    
    # インデクサーを作成
    indexer = Indexer()
    
    # インデックスを実行
    result = await indexer.index_repository(fixture_path)
    
    print(f"\n結果:")
    print(f"  - エンティティ数: {result.entities_count}")
    print(f"  - リレーション数: {result.relations_count}")
    print(f"  - 処理ファイル数: {result.files_indexed}")
    print(f"  - 処理時間: {result.duration_seconds:.2f}秒")
    
    return result


async def example_2_query_entities():
    """
    例2: エンティティを検索する
    
    この例では、グラフエンジンを使用してエンティティを検索します。
    """
    print("\n" + "=" * 60)
    print("例2: エンティティの検索")
    print("=" * 60)
    
    fixture_path = project_root / "tests" / "fixtures" / "python"
    
    # グラフエンジンを初期化
    engine = GraphEngine(fixture_path)
    await engine.initialize()
    
    try:
        # クエリを作成
        query = GraphQuery(query="Calculator", max_results=10)
        
        # クエリを実行
        result = await engine.query(query)
        
        print(f"\n検索クエリ: 'Calculator'")
        print(f"結果: {len(result.entities)}件のエンティティが見つかりました")
        
        for entity in result.entities[:5]:
            print(f"  - {entity.name} ({entity.type.value})")
            print(f"    ファイル: {entity.file_path}:{entity.start_line}")
    finally:
        await engine.close()


async def example_3_find_callers():
    """
    例3: 呼び出し元を検索する
    
    この例では、特定のメソッドの呼び出し元を検索します。
    """
    print("\n" + "=" * 60)
    print("例3: 呼び出し元の検索")
    print("=" * 60)
    
    fixture_path = project_root / "tests" / "fixtures" / "python"
    
    engine = GraphEngine(fixture_path)
    await engine.initialize()
    
    try:
        # まずエンティティを検索
        query = GraphQuery(query="add", max_results=5)
        result = await engine.query(query)
        
        if not result.entities:
            print("エンティティが見つかりませんでした")
            return
        
        target_entity = result.entities[0]
        print(f"\n対象エンティティ: {target_entity.qualified_name}")
        
        # 呼び出し元を検索
        callers = await engine.find_callers(target_entity.id)
        
        print(f"呼び出し元: {len(callers)}件")
        for caller in callers:
            print(f"  - {caller.name} ({caller.type.value})")
    finally:
        await engine.close()


async def example_4_analyze_dependencies():
    """
    例4: 依存関係を分析する
    
    この例では、エンティティの依存関係を分析します。
    """
    print("\n" + "=" * 60)
    print("例4: 依存関係の分析")
    print("=" * 60)
    
    fixture_path = project_root / "tests" / "fixtures" / "python"
    
    engine = GraphEngine(fixture_path)
    await engine.initialize()
    
    try:
        # クラスを検索
        query = GraphQuery(query="Calculator", max_results=1)
        result = await engine.query(query)
        
        if not result.entities:
            print("エンティティが見つかりませんでした")
            return
        
        target = result.entities[0]
        print(f"\n対象エンティティ: {target.qualified_name}")
        
        # 依存関係を検索
        deps = await engine.find_dependencies(target.id, depth=2)
        
        print(f"\n依存関係:")
        for dep in deps.entities[:10]:
            print(f"  - {dep.name} ({dep.type.value})")
    finally:
        await engine.close()


async def example_5_get_statistics():
    """
    例5: 統計情報を取得する
    
    この例では、グラフの統計情報を取得します。
    """
    print("\n" + "=" * 60)
    print("例5: 統計情報の取得")
    print("=" * 60)
    
    fixture_path = project_root / "tests" / "fixtures" / "python"
    
    engine = GraphEngine(fixture_path)
    await engine.initialize()
    
    try:
        stats = await engine.get_statistics()
        
        print(f"\nグラフ統計:")
        print(f"  - エンティティ数: {stats.get('entity_count', 0)}")
        print(f"  - リレーション数: {stats.get('relation_count', 0)}")
        print(f"  - ファイル数: {stats.get('file_count', 0)}")
        
        if "entities_by_type" in stats:
            print(f"\nエンティティタイプ別:")
            for entity_type, count in stats["entities_by_type"].items():
                print(f"    - {entity_type}: {count}")
    finally:
        await engine.close()


async def example_6_use_parser_directly():
    """
    例6: パーサーを直接使用する
    
    この例では、ASTパーサーを直接使用してコードを解析します。
    """
    print("\n" + "=" * 60)
    print("例6: パーサーの直接使用")
    print("=" * 60)
    
    # サンプルコード
    sample_code = '''
class Calculator:
    """簡単な計算機クラス"""
    
    def add(self, a: int, b: int) -> int:
        """2つの数を足す"""
        return a + b
    
    def multiply(self, a: int, b: int) -> int:
        """2つの数を掛ける"""
        return a * b


def main():
    """メイン関数"""
    calc = Calculator()
    result = calc.add(1, 2)
    print(f"Result: {result}")
'''
    
    # パーサーを作成
    parser = ASTParser()
    
    # コードを解析
    entities, relations = parser.parse_code(
        code=sample_code,
        language="python",
        file_path="sample.py"
    )
    
    print(f"\n解析結果:")
    print(f"  - エンティティ数: {len(entities)}")
    print(f"  - リレーション数: {len(relations)}")
    
    print(f"\nエンティティ一覧:")
    for entity in entities:
        print(f"  - {entity.name} ({entity.type.value}) [行 {entity.start_line}-{entity.end_line}]")
    
    print(f"\nリレーション一覧:")
    for rel in relations:
        print(f"  - {rel.source_id} --[{rel.type.value}]--> {rel.target_id}")


async def main():
    """メイン関数"""
    print("\n" + "=" * 60)
    print("CodeGraphMCPServer 使用例")
    print("=" * 60 + "\n")
    
    # 各例を順番に実行
    await example_1_index_repository()
    await example_2_query_entities()
    await example_3_find_callers()
    await example_4_analyze_dependencies()
    await example_5_get_statistics()
    await example_6_use_parser_directly()
    
    print("\n" + "=" * 60)
    print("全ての例が完了しました")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
