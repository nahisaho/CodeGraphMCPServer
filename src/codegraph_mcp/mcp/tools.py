"""
MCP Tools Module

14 MCP tools for code analysis and manipulation.

Requirements: REQ-TLS-001 ~ REQ-TLS-014
Design Reference: design-mcp-interface.md §2
"""

from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from codegraph_mcp.config import Config


def register(server: Server, config: Config) -> None:
    """Register all MCP tools with the server."""

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """Return list of available tools."""
        return [
            # Graph Query Tools (REQ-TLS-001 ~ REQ-TLS-006)
            Tool(
                name="query_codebase",
                description=(
                    "Query the code graph using natural language. "
                    "Returns entities with relevance scores and community info."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language query",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum results to return",
                            "default": 20,
                        },
                        "include_related": {
                            "type": "boolean",
                            "description": "Include related entities",
                            "default": True,
                        },
                        "entity_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Filter by entity types "
                                "(function, class, method, module, variable)"
                            ),
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="find_dependencies",
                description=(
                    "Find dependencies of a code entity. "
                    "Supports partial entity ID matching."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": (
                                "Entity identifier (full ID, name, or "
                                "file::name pattern)"
                            ),
                        },
                        "depth": {
                            "type": "integer",
                            "description": "Dependency traversal depth",
                            "default": 2,
                        },
                    },
                    "required": ["entity_id"],
                },
            ),
            Tool(
                name="find_callers",
                description=(
                    "Find all callers of a function or method. "
                    "Supports partial entity ID matching."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": (
                                "Function/method identifier (full ID, name, "
                                "or file::name pattern)"
                            ),
                        },
                    },
                    "required": ["entity_id"],
                },
            ),
            Tool(
                name="find_callees",
                description=(
                    "Find all functions called by an entity. "
                    "Supports partial entity ID matching."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "Function/method identifier",
                        },
                    },
                    "required": ["entity_id"],
                },
            ),
            Tool(
                name="find_implementations",
                description="Find implementations of an interface or abstract class",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "Interface/class identifier",
                        },
                    },
                    "required": ["entity_id"],
                },
            ),
            Tool(
                name="analyze_module_structure",
                description="Analyze the structure of a module/file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file",
                        },
                    },
                    "required": ["file_path"],
                },
            ),
            # Code Retrieval Tools (REQ-TLS-007 ~ REQ-TLS-009)
            Tool(
                name="get_code_snippet",
                description="Get source code for an entity",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "Entity identifier",
                        },
                        "include_context": {
                            "type": "boolean",
                            "description": "Include surrounding context",
                            "default": True,
                        },
                    },
                    "required": ["entity_id"],
                },
            ),
            Tool(
                name="read_file_content",
                description="Read file content with optional line range",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file",
                        },
                        "start_line": {
                            "type": "integer",
                            "description": "Start line number",
                        },
                        "end_line": {
                            "type": "integer",
                            "description": "End line number",
                        },
                    },
                    "required": ["file_path"],
                },
            ),
            Tool(
                name="get_file_structure",
                description="Get structural overview of a file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file",
                        },
                    },
                    "required": ["file_path"],
                },
            ),
            # GraphRAG Tools (REQ-TLS-010 ~ REQ-TLS-011)
            Tool(
                name="global_search",
                description="Search across all communities using GraphRAG",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="local_search",
                description="Search within entity neighborhood using GraphRAG",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "entity_id": {
                            "type": "string",
                            "description": "Starting entity for local search",
                        },
                    },
                    "required": ["query", "entity_id"],
                },
            ),
            # Management Tools (REQ-TLS-012 ~ REQ-TLS-014)
            Tool(
                name="suggest_refactoring",
                description="Suggest refactoring opportunities",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "Entity to analyze",
                        },
                        "type": {
                            "type": "string",
                            "enum": ["extract", "rename", "move", "simplify"],
                            "description": "Refactoring type",
                        },
                    },
                    "required": ["entity_id"],
                },
            ),
            Tool(
                name="reindex_repository",
                description="Trigger repository re-indexing",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "incremental": {
                            "type": "boolean",
                            "description": "Incremental update only",
                            "default": True,
                        },
                    },
                },
            ),
            Tool(
                name="execute_shell_command",
                description="Execute a shell command in repository context",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Shell command to execute",
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds",
                            "default": 30,
                        },
                    },
                    "required": ["command"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        from codegraph_mcp.core.graph import GraphEngine

        engine = GraphEngine(config.repo_path)
        await engine.initialize()

        try:
            result = await _dispatch_tool(name, arguments, engine, config)
            return [TextContent(type="text", text=str(result))]
        finally:
            await engine.close()


async def _dispatch_tool(
    name: str,
    args: dict[str, Any],
    engine: Any,
    config: Config,
) -> Any:
    """Dispatch tool call to appropriate handler."""

    handlers = {
        "query_codebase": _handle_query_codebase,
        "find_dependencies": _handle_find_dependencies,
        "find_callers": _handle_find_callers,
        "find_callees": _handle_find_callees,
        "find_implementations": _handle_find_implementations,
        "analyze_module_structure": _handle_analyze_module,
        "get_code_snippet": _handle_get_code_snippet,
        "read_file_content": _handle_read_file,
        "get_file_structure": _handle_get_file_structure,
        "global_search": _handle_global_search,
        "local_search": _handle_local_search,
        "suggest_refactoring": _handle_suggest_refactoring,
        "reindex_repository": _handle_reindex,
        "execute_shell_command": _handle_execute_command,
    }

    handler = handlers.get(name)
    if handler:
        return await handler(args, engine, config)

    return {"error": f"Unknown tool: {name}"}


async def _handle_query_codebase(
    args: dict[str, Any],
    engine: Any,
    config: Config,
) -> dict[str, Any]:
    """Handle query_codebase tool with enhanced search."""
    from codegraph_mcp.core.graph import GraphQuery
    from codegraph_mcp.core.parser import EntityType

    # Parse entity types if provided
    entity_types = None
    if args.get("entity_types"):
        type_map = {
            "function": EntityType.FUNCTION,
            "class": EntityType.CLASS,
            "method": EntityType.METHOD,
            "module": EntityType.MODULE,
            "variable": EntityType.VARIABLE,
        }
        entity_types = [
            type_map[t.lower()]
            for t in args["entity_types"]
            if t.lower() in type_map
        ]

    query = GraphQuery(
        query=args["query"],
        max_results=args.get("max_results", 20),
        include_related=args.get("include_related", True),
        include_community=True,
        entity_types=entity_types if entity_types else None,
    )
    result = await engine.query(query)
    return result.to_dict()


async def _handle_find_dependencies(
    args: dict[str, Any],
    engine: Any,
    config: Config,
) -> dict[str, Any]:
    """Handle find_dependencies tool."""
    result = await engine.find_dependencies(
        args["entity_id"],
        depth=args.get("depth", 2),
    )
    return result.to_dict()


async def _handle_find_callers(
    args: dict[str, Any],
    engine: Any,
    config: Config,
) -> dict[str, Any]:
    """Handle find_callers tool."""
    entities = await engine.find_callers(args["entity_id"])
    return {
        "callers": [
            {"id": e.id, "name": e.name, "type": e.type.value}
            for e in entities
        ]
    }


async def _handle_find_callees(
    args: dict[str, Any],
    engine: Any,
    config: Config,
) -> dict[str, Any]:
    """Handle find_callees tool."""
    entities = await engine.find_callees(args["entity_id"])
    return {
        "callees": [
            {"id": e.id, "name": e.name, "type": e.type.value}
            for e in entities
        ]
    }


async def _handle_find_implementations(
    args: dict[str, Any],
    engine: Any,
    config: Config,
) -> dict[str, Any]:
    """Handle find_implementations tool."""
    # Query for entities that implement the given interface
    cursor = await engine._connection.execute(
        """
        SELECT e.* FROM entities e
        JOIN relations r ON e.id = r.source_id
        WHERE r.target_id = ? AND r.type = 'implements'
        """,
        (args["entity_id"],),
    )
    rows = await cursor.fetchall()
    return {
        "implementations": [
            {"id": row[0], "name": row[2], "type": row[1]}
            for row in rows
        ]
    }


async def _handle_analyze_module(
    args: dict[str, Any],
    engine: Any,
    config: Config,
) -> dict[str, Any]:
    """Handle analyze_module_structure tool."""
    file_path = args["file_path"]

    cursor = await engine._connection.execute(
        "SELECT type, name, start_line, end_line FROM entities WHERE file_path = ?",
        (file_path,),
    )
    rows = await cursor.fetchall()

    return {
        "file": file_path,
        "entities": [
            {"type": row[0], "name": row[1], "lines": f"{row[2]}-{row[3]}"}
            for row in rows
        ],
    }


async def _handle_get_code_snippet(
    args: dict[str, Any],
    engine: Any,
    config: Config,
) -> dict[str, Any]:
    """Handle get_code_snippet tool."""
    entity = await engine.get_entity(args["entity_id"])
    if not entity:
        return {"error": "Entity not found"}

    return {
        "entity_id": entity.id,
        "name": entity.name,
        "source": entity.source_code or "Source code not available",
    }


async def _handle_read_file(
    args: dict[str, Any],
    engine: Any,
    config: Config,
) -> dict[str, Any]:
    """Handle read_file_content tool."""

    file_path = config.repo_path / args["file_path"]
    if not file_path.exists():
        return {"error": "File not found"}

    content = file_path.read_text()
    lines = content.split("\n")

    start = args.get("start_line", 1) - 1
    end = args.get("end_line", len(lines))

    return {
        "file": args["file_path"],
        "content": "\n".join(lines[start:end]),
        "lines": f"{start + 1}-{end}",
    }


async def _handle_get_file_structure(
    args: dict[str, Any],
    engine: Any,
    config: Config,
) -> dict[str, Any]:
    """Handle get_file_structure tool."""
    return await _handle_analyze_module(args, engine, config)


async def _handle_global_search(
    args: dict[str, Any],
    engine: Any,
    config: Config,
) -> dict[str, Any]:
    """Handle global_search tool (GraphRAG)."""
    from codegraph_mcp.core.graphrag import GraphRAGSearch

    search = GraphRAGSearch(engine, use_llm=config.semantic.llm_enabled)
    result = await search.global_search(
        query=args["query"],
        community_level=args.get("community_level", 0),
    )

    return {
        "query": result.query,
        "answer": result.answer,
        "communities_searched": result.communities_searched,
        "confidence": result.confidence,
        "relevant_communities": result.relevant_communities[:5],
        "supporting_entities": [
            {
                "id": e.entity_id,
                "name": e.name,
                "type": e.entity_type,
                "file": e.file_path,
                "relevance": e.relevance_score,
            }
            for e in result.supporting_entities[:10]
        ],
    }


async def _handle_local_search(
    args: dict[str, Any],
    engine: Any,
    config: Config,
) -> dict[str, Any]:
    """Handle local_search tool (GraphRAG)."""
    from codegraph_mcp.core.graphrag import GraphRAGSearch

    search = GraphRAGSearch(engine, use_llm=config.semantic.llm_enabled)
    result = await search.local_search(
        query=args["query"],
        entity_id=args["entity_id"],
        depth=args.get("depth", 2),
    )

    return {
        "query": result.query,
        "answer": result.answer,
        "start_entity": result.start_entity,
        "entities_searched": result.entities_searched,
        "confidence": result.confidence,
        "relevant_entities": [
            {
                "id": e.entity_id,
                "name": e.name,
                "type": e.entity_type,
                "relevance": e.relevance_score,
            }
            for e in result.relevant_entities[:10]
        ],
        "relationships": result.relationships[:20],
    }


async def _handle_suggest_refactoring(
    args: dict[str, Any],
    engine: Any,
    config: Config,
) -> dict[str, Any]:
    """Handle suggest_refactoring tool."""
    entity = await engine.get_entity(args["entity_id"])
    if not entity:
        return {"error": "Entity not found"}

    suggestions = []

    # Analyze complexity
    if entity.source_code:
        lines = entity.source_code.count("\n") + 1
        if lines > 50:
            suggestions.append({
                "type": "extract",
                "reason": f"Function is {lines} lines, consider extraction",
            })

    return {
        "entity": entity.name,
        "suggestions": suggestions,
    }


async def _handle_reindex(
    args: dict[str, Any],
    engine: Any,
    config: Config,
) -> dict[str, Any]:
    """Handle reindex_repository tool."""
    from codegraph_mcp.core.indexer import Indexer

    indexer = Indexer()
    result = await indexer.index_repository(
        config.repo_path,
        incremental=args.get("incremental", True),
    )

    return {
        "entities": result.entities_count,
        "relations": result.relations_count,
        "files": result.files_indexed,
        "duration": result.duration_seconds,
    }


async def _handle_execute_command(
    args: dict[str, Any],
    engine: Any,
    config: Config,
) -> dict[str, Any]:
    """Handle execute_shell_command tool."""
    import asyncio
    import subprocess

    timeout = args.get("timeout", 30)

    try:
        proc = await asyncio.create_subprocess_shell(
            args["command"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=config.repo_path,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout,
        )

        return {
            "exit_code": proc.returncode,
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
        }
    except TimeoutError:
        return {"error": f"Command timed out after {timeout}s"}
