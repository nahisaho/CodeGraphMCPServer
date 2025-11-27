"""
MCP Resources Module

4 MCP resource types for code graph access.

Requirements: REQ-RSC-001 ~ REQ-RSC-004
Design Reference: design-mcp-interface.md §3
"""

from typing import Any

from mcp.server import Server
from mcp.types import Resource

from codegraph_mcp.config import Config


def register(server: Server, config: Config) -> None:
    """Register all MCP resources with the server."""

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """Return list of available resources."""
        return [
            Resource(
                uri="codegraph://entities/{entity_id}",
                name="Code Entity",
                description="Access a specific code entity by ID",
                mimeType="application/json",
            ),
            Resource(
                uri="codegraph://files/{file_path}",
                name="File Graph",
                description="Access the code graph for a specific file",
                mimeType="application/json",
            ),
            Resource(
                uri="codegraph://communities/{community_id}",
                name="Code Community",
                description="Access a code community and its members",
                mimeType="application/json",
            ),
            Resource(
                uri="codegraph://stats",
                name="Graph Statistics",
                description="Get overall code graph statistics",
                mimeType="application/json",
            ),
        ]

    @server.read_resource()
    async def read_resource(uri: str) -> str:
        """Read resource content."""
        import json

        from codegraph_mcp.core.graph import GraphEngine

        engine = GraphEngine(config.repo_path)
        await engine.initialize()

        try:
            result = await _dispatch_resource(uri, engine)
            return json.dumps(result, indent=2)
        finally:
            await engine.close()


async def _dispatch_resource(uri: str, engine: Any) -> dict[str, Any]:
    """Dispatch resource request to appropriate handler."""

    if uri.startswith("codegraph://entities/"):
        entity_id = uri.split("/")[-1]
        return await _read_entity(entity_id, engine)

    elif uri.startswith("codegraph://files/"):
        file_path = "/".join(uri.split("/")[3:])
        return await _read_file_graph(file_path, engine)

    elif uri.startswith("codegraph://communities/"):
        community_id = int(uri.split("/")[-1])
        return await _read_community(community_id, engine)

    elif uri == "codegraph://stats":
        return await _read_stats(engine)

    return {"error": f"Unknown resource: {uri}"}


async def _read_entity(entity_id: str, engine: Any) -> dict[str, Any]:
    """Read entity resource (REQ-RSC-001)."""
    entity = await engine.get_entity(entity_id)

    if not entity:
        return {"error": "Entity not found", "entity_id": entity_id}

    # Get related entities
    callers = await engine.find_callers(entity_id)
    callees = await engine.find_callees(entity_id)

    return {
        "entity": {
            "id": entity.id,
            "type": entity.type.value,
            "name": entity.name,
            "qualified_name": entity.qualified_name,
            "file_path": str(entity.file_path),
            "start_line": entity.start_line,
            "end_line": entity.end_line,
            "signature": entity.signature,
            "docstring": entity.docstring,
            "source_code": entity.source_code,
        },
        "relations": {
            "callers": [{"id": e.id, "name": e.name} for e in callers],
            "callees": [{"id": e.id, "name": e.name} for e in callees],
        },
    }


async def _read_file_graph(file_path: str, engine: Any) -> dict[str, Any]:
    """Read file graph resource (REQ-RSC-002)."""
    # Get entities in file
    cursor = await engine._connection.execute(
        """
        SELECT id, type, name, start_line, end_line, signature
        FROM entities WHERE file_path LIKE ?
        ORDER BY start_line
        """,
        (f"%{file_path}",),
    )
    rows = await cursor.fetchall()

    entities = [
        {
            "id": row[0],
            "type": row[1],
            "name": row[2],
            "start_line": row[3],
            "end_line": row[4],
            "signature": row[5],
        }
        for row in rows
    ]

    # Get relations within file
    entity_ids = [e["id"] for e in entities]
    if entity_ids:
        placeholders = ",".join("?" * len(entity_ids))
        cursor = await engine._connection.execute(
            f"""
            SELECT source_id, target_id, type
            FROM relations
            WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})
            """,
            entity_ids + entity_ids,
        )
        relations = [
            {"source": row[0], "target": row[1], "type": row[2]}
            for row in await cursor.fetchall()
        ]
    else:
        relations = []

    return {
        "file_path": file_path,
        "entities": entities,
        "relations": relations,
        "entity_count": len(entities),
    }


async def _read_community(community_id: int, engine: Any) -> dict[str, Any]:
    """Read community resource (REQ-RSC-003)."""
    # Get community info
    cursor = await engine._connection.execute(
        "SELECT id, level, name, summary, member_count FROM communities WHERE id = ?",
        (community_id,),
    )
    row = await cursor.fetchone()

    if not row:
        return {"error": "Community not found", "community_id": community_id}

    # Get member entities
    cursor = await engine._connection.execute(
        """
        SELECT id, type, name, file_path
        FROM entities WHERE community_id = ?
        ORDER BY type, name
        """,
        (community_id,),
    )
    members = [
        {"id": r[0], "type": r[1], "name": r[2], "file": r[3]}
        for r in await cursor.fetchall()
    ]

    return {
        "community": {
            "id": row[0],
            "level": row[1],
            "name": row[2],
            "summary": row[3],
            "member_count": row[4],
        },
        "members": members,
    }


async def _read_stats(engine: Any) -> dict[str, Any]:
    """Read graph statistics resource (REQ-RSC-004)."""
    stats = await engine.get_statistics()

    return {
        "statistics": {
            "entities": stats.entity_count,
            "relations": stats.relation_count,
            "communities": stats.community_count,
            "files": stats.file_count,
            "languages": stats.languages,
        },
        "entities_by_type": stats.entities_by_type,
        "relations_by_type": stats.relations_by_type,
    }
