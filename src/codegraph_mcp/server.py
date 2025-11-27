"""
MCP Server Main Module

This module implements the main MCP server that exposes code graph analysis
capabilities through the Model Context Protocol.

Requirements: REQ-TRP-001 ~ REQ-TRP-005
Design Reference: design-mcp-interface.md
"""

from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server

from codegraph_mcp.config import Config
from codegraph_mcp.utils.logging import get_logger


logger = get_logger(__name__)


def create_server(config: Config) -> Server:
    """
    Create and configure the MCP server.

    Args:
        config: Server configuration

    Returns:
        Configured MCP server instance
    """
    server = Server("codegraph-mcp")

    # Import handlers to register tools, resources, and prompts
    from codegraph_mcp.mcp import prompts, resources, tools

    # Register MCP components
    tools.register(server, config)
    resources.register(server, config)
    prompts.register(server, config)

    return server


async def run_server_async(
    repo_path: Path,
    transport: str = "stdio",
    port: int = 8080,
) -> int:
    """
    Run the MCP server asynchronously.

    Args:
        repo_path: Path to the repository to serve
        transport: Transport protocol ("stdio" or "sse")
        port: Port for SSE transport

    Returns:
        Exit code (0 for success)
    """
    config = Config(repo_path=repo_path)
    server = create_server(config)

    logger.info(f"Starting CodeGraph MCP Server for {repo_path}")
    logger.info(f"Transport: {transport}")

    if transport == "stdio":
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    elif transport == "sse":
        # SSE transport implementation (REQ-TRP-003)
        import uvicorn
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request: Any) -> Response:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await server.run(
                    streams[0],
                    streams[1],
                    server.create_initialization_options(),
                )
            return Response()

        app = Starlette(
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ]
        )

        logger.info(f"SSE server running on port {port}")
        config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
        server_instance = uvicorn.Server(config)
        await server_instance.serve()

    return 0


def run_server(
    repo_path: Path,
    transport: str = "stdio",
    port: int = 8080,
) -> int:
    """
    Run the MCP server (synchronous wrapper).

    Args:
        repo_path: Path to the repository to serve
        transport: Transport protocol ("stdio" or "sse")
        port: Port for SSE transport

    Returns:
        Exit code (0 for success)
    """
    import asyncio
    return asyncio.run(run_server_async(repo_path, transport, port))
