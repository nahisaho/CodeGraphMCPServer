#!/usr/bin/env python3
"""
MCP Client Example
==================

MCPクライアントからCodeGraphMCPServerを利用する例です。

実行方法:
    # 1. 別ターミナルでサーバーを起動
    codegraph-mcp serve --repo /path/to/project

    # 2. このスクリプトを実行
    python examples/mcp_client.py

注意:
    この例を実行するには、MCP Python SDKが必要です。
    pip install mcp
"""

import asyncio
import json
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


async def example_1_list_tools():
    """
    例1: 利用可能なツールを一覧表示

    MCPサーバーに接続して、利用可能なツールの一覧を取得します。
    """
    print("=" * 60)
    print("例1: 利用可能なツールの一覧")
    print("=" * 60)

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        # サーバーパラメータを設定
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "codegraph_mcp", "serve", "--repo", str(project_root)],
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # ツール一覧を取得
                tools = await session.list_tools()
                print(f"\n利用可能なツール: {len(tools.tools)}個")
                for tool in tools.tools:
                    print(f"  - {tool.name}")
                    print(f"    {tool.description[:60]}...")

    except ImportError:
        print("\nMCP SDKがインストールされていません。")
        print("以下のコマンドでインストールしてください:")
        print("  pip install mcp")


async def example_2_call_tool():
    """
    例2: ツールを呼び出す

    query_codebaseツールを呼び出してコードを検索します。
    """
    print("\n" + "=" * 60)
    print("例2: ツールの呼び出し")
    print("=" * 60)

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        server_params = StdioServerParameters(
            command="python",
            args=["-m", "codegraph_mcp", "serve", "--repo", str(project_root)],
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # query_codebaseツールを呼び出し
                print("\nquery_codebaseツールを呼び出し中...")
                result = await session.call_tool(
                    "query_codebase",
                    arguments={
                        "query": "GraphEngine",
                        "max_results": 5,
                    },
                )

                print(f"\n結果:")
                for content in result.content:
                    print(content.text)

    except ImportError:
        print("\nMCP SDKがインストールされていません。")


async def example_3_list_resources():
    """
    例3: リソースを一覧表示

    MCPサーバーで利用可能なリソースを取得します。
    """
    print("\n" + "=" * 60)
    print("例3: 利用可能なリソースの一覧")
    print("=" * 60)

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        server_params = StdioServerParameters(
            command="python",
            args=["-m", "codegraph_mcp", "serve", "--repo", str(project_root)],
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # リソース一覧を取得
                resources = await session.list_resources()
                print(f"\n利用可能なリソース: {len(resources.resources)}個")
                for resource in resources.resources:
                    print(f"  - {resource.uri}")
                    print(f"    {resource.description[:60]}...")

    except ImportError:
        print("\nMCP SDKがインストールされていません。")


async def example_4_read_resource():
    """
    例4: リソースを読み取る

    統計情報リソースを読み取ります。
    """
    print("\n" + "=" * 60)
    print("例4: リソースの読み取り")
    print("=" * 60)

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        server_params = StdioServerParameters(
            command="python",
            args=["-m", "codegraph_mcp", "serve", "--repo", str(project_root)],
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # 統計リソースを読み取り
                print("\ncodegraph://statsリソースを読み取り中...")
                content = await session.read_resource("codegraph://stats")

                print(f"\n統計情報:")
                for item in content.contents:
                    print(item.text)

    except ImportError:
        print("\nMCP SDKがインストールされていません。")


async def example_5_list_prompts():
    """
    例5: プロンプトを一覧表示

    MCPサーバーで利用可能なプロンプトを取得します。
    """
    print("\n" + "=" * 60)
    print("例5: 利用可能なプロンプトの一覧")
    print("=" * 60)

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        server_params = StdioServerParameters(
            command="python",
            args=["-m", "codegraph_mcp", "serve", "--repo", str(project_root)],
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # プロンプト一覧を取得
                prompts = await session.list_prompts()
                print(f"\n利用可能なプロンプト: {len(prompts.prompts)}個")
                for prompt in prompts.prompts:
                    print(f"  - {prompt.name}")
                    print(f"    {prompt.description[:60]}...")

    except ImportError:
        print("\nMCP SDKがインストールされていません。")


async def example_6_get_prompt():
    """
    例6: プロンプトを取得する

    code_reviewプロンプトを取得します。
    """
    print("\n" + "=" * 60)
    print("例6: プロンプトの取得")
    print("=" * 60)

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        server_params = StdioServerParameters(
            command="python",
            args=["-m", "codegraph_mcp", "serve", "--repo", str(project_root)],
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # プロンプトを取得
                print("\ncode_reviewプロンプトを取得中...")
                result = await session.get_prompt(
                    "code_review",
                    arguments={
                        "entity_id": "sample_entity",
                        "focus_areas": "performance,security",
                    },
                )

                print(f"\n生成されたプロンプト:")
                for message in result.messages:
                    print(f"  Role: {message.role}")
                    print(f"  Content: {message.content.text[:200]}...")

    except ImportError:
        print("\nMCP SDKがインストールされていません。")


def show_manual_usage():
    """MCPを使わない手動使用例を表示"""
    print("\n" + "=" * 60)
    print("MCP SDKなしでの使用方法")
    print("=" * 60)

    print("""
MCPクライアントがない場合は、CLIを直接使用できます:

1. インデックス作成:
   codegraph-mcp index /path/to/repository --full

2. クエリ実行:
   codegraph-mcp query "Calculator" --repo /path/to/repository

3. 統計情報:
   codegraph-mcp stats /path/to/repository

4. サーバー起動:
   codegraph-mcp serve --repo /path/to/repository

詳細は README.md を参照してください。
""")


async def main():
    """メイン関数"""
    print("\n" + "=" * 60)
    print("CodeGraphMCPServer MCPクライアント例")
    print("=" * 60)

    # MCP SDKの存在確認
    try:
        import mcp
        print(f"\nMCP SDK バージョン: {mcp.__version__}")
        has_mcp = True
    except ImportError:
        has_mcp = False
        print("\nMCP SDKが見つかりません。")
        print("インストール: pip install mcp")

    if has_mcp:
        print("\n注意: 以下の例はMCPサーバーをサブプロセスとして起動します。")
        print("Ctrl+Cで中断できます。")

        try:
            await example_1_list_tools()
            await example_2_call_tool()
            await example_3_list_resources()
            await example_4_read_resource()
            await example_5_list_prompts()
            await example_6_get_prompt()
        except KeyboardInterrupt:
            print("\n\n中断されました。")
        except Exception as e:
            print(f"\nエラー: {e}")
            print("サーバーが正しく起動できない可能性があります。")

    # 手動使用例を表示
    show_manual_usage()

    print("\n" + "=" * 60)
    print("完了")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
