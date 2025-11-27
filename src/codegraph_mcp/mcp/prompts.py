"""
MCP Prompts Module

6 MCP prompt templates for common code analysis tasks.

Requirements: REQ-PRM-001 ~ REQ-PRM-006
Design Reference: design-mcp-interface.md §4
"""

from typing import Any

from mcp.server import Server
from mcp.types import Prompt, PromptArgument, PromptMessage, TextContent

from codegraph_mcp.config import Config


def register(server: Server, config: Config) -> None:
    """Register all MCP prompts with the server."""

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        """Return list of available prompts."""
        return [
            # REQ-PRM-001
            Prompt(
                name="code_review",
                description="Review code for issues and improvements",
                arguments=[
                    PromptArgument(
                        name="entity_id",
                        description="Entity to review",
                        required=True,
                    ),
                    PromptArgument(
                        name="focus",
                        description="Review focus (security, performance, style)",
                        required=False,
                    ),
                ],
            ),
            # REQ-PRM-002
            Prompt(
                name="explain_codebase",
                description="Explain the overall codebase structure",
                arguments=[
                    PromptArgument(
                        name="depth",
                        description="Explanation depth (overview, detailed)",
                        required=False,
                    ),
                ],
            ),
            # REQ-PRM-003
            Prompt(
                name="implement_feature",
                description="Guide implementing a new feature",
                arguments=[
                    PromptArgument(
                        name="description",
                        description="Feature description",
                        required=True,
                    ),
                    PromptArgument(
                        name="related_entities",
                        description="Related existing entities",
                        required=False,
                    ),
                ],
            ),
            # REQ-PRM-004
            Prompt(
                name="debug_issue",
                description="Help debug an issue in the code",
                arguments=[
                    PromptArgument(
                        name="error_message",
                        description="Error message or symptom",
                        required=True,
                    ),
                    PromptArgument(
                        name="context",
                        description="Additional context",
                        required=False,
                    ),
                ],
            ),
            # REQ-PRM-005
            Prompt(
                name="refactor_guidance",
                description="Provide refactoring guidance for code",
                arguments=[
                    PromptArgument(
                        name="entity_id",
                        description="Entity to refactor",
                        required=True,
                    ),
                    PromptArgument(
                        name="goal",
                        description="Refactoring goal",
                        required=False,
                    ),
                ],
            ),
            # REQ-PRM-006
            Prompt(
                name="test_generation",
                description="Generate tests for an entity",
                arguments=[
                    PromptArgument(
                        name="entity_id",
                        description="Entity to test",
                        required=True,
                    ),
                    PromptArgument(
                        name="test_type",
                        description="Type of tests (unit, integration)",
                        required=False,
                    ),
                ],
            ),
        ]

    @server.get_prompt()
    async def get_prompt(
        name: str,
        arguments: dict[str, str] | None = None,
    ) -> list[PromptMessage]:
        """Get prompt messages for the given prompt."""
        from codegraph_mcp.core.graph import GraphEngine

        arguments = arguments or {}

        engine = GraphEngine(config.repo_path)
        await engine.initialize()

        try:
            return await _dispatch_prompt(name, arguments, engine, config)
        finally:
            await engine.close()


async def _dispatch_prompt(
    name: str,
    args: dict[str, str],
    engine: Any,
    config: Config,
) -> list[PromptMessage]:
    """Dispatch prompt request to appropriate handler."""
    handlers = {
        "code_review": _prompt_code_review,
        "explain_codebase": _prompt_explain_codebase,
        "implement_feature": _prompt_implement_feature,
        "debug_issue": _prompt_debug_issue,
        "refactor_guidance": _prompt_refactor_guidance,
        "test_generation": _prompt_test_generation,
    }

    handler = handlers.get(name)
    if handler:
        return await handler(args, engine, config)

    return [PromptMessage(
        role="user",
        content=TextContent(type="text", text=f"Unknown prompt: {name}"),
    )]


async def _prompt_code_review(
    args: dict[str, str],
    engine: Any,
    config: Config,
) -> list[PromptMessage]:
    """Generate code review prompt (REQ-PRM-001)."""
    entity = await engine.get_entity(args["entity_id"])
    focus = args.get("focus", "general")

    if not entity:
        return [PromptMessage(
            role="user",
            content=TextContent(type="text", text="Entity not found"),
        )]

    # Get context
    callers = await engine.find_callers(entity.id)
    callees = await engine.find_callees(entity.id)

    context = f"""
# Code Review Request

## Entity Information
- **Name**: {entity.name}
- **Type**: {entity.type.value}
- **File**: {entity.file_path}:{entity.start_line}-{entity.end_line}
- **Signature**: {entity.signature or 'N/A'}

## Source Code
```
{entity.source_code or 'Source code not available'}
```

## Context
- Called by: {', '.join(e.name for e in callers[:5])} ({len(callers)} total)
- Calls: {', '.join(e.name for e in callees[:5])} ({len(callees)} total)

## Review Focus
{focus}

Please review this code for:
1. Potential bugs or errors
2. Code quality issues
3. Performance concerns
4. Security vulnerabilities (if applicable)
5. Suggestions for improvement
"""

    return [PromptMessage(
        role="user",
        content=TextContent(type="text", text=context),
    )]


async def _prompt_explain_codebase(
    args: dict[str, str],
    engine: Any,
    config: Config,
) -> list[PromptMessage]:
    """Generate codebase explanation prompt (REQ-PRM-002)."""
    stats = await engine.get_statistics()
    depth = args.get("depth", "overview")

    # Get community summaries for high-level overview
    cursor = await engine._connection.execute(
        "SELECT name, summary, member_count FROM communities ORDER BY member_count DESC LIMIT 10"
    )
    communities = await cursor.fetchall()

    community_text = "\n".join(
        f"- **{c[0] or f'Community {i}'}** ({c[2]} members): {c[1] or 'No summary'}"
        for i, c in enumerate(communities)
    )

    context = f"""
# Codebase Explanation Request

## Statistics
- **Total Entities**: {stats.entity_count}
- **Total Relations**: {stats.relation_count}
- **Communities**: {stats.community_count}
- **Files**: {stats.file_count}

## Entity Types
{chr(10).join(f'- {k}: {v}' for k, v in stats.entities_by_type.items())}

## Main Code Communities
{community_text}

## Request
Please explain this codebase at the {depth} level:
- What is the main purpose of this codebase?
- What are the key components and how do they interact?
- What architectural patterns are used?
"""

    return [PromptMessage(
        role="user",
        content=TextContent(type="text", text=context),
    )]


async def _prompt_implement_feature(
    args: dict[str, str],
    engine: Any,
    config: Config,
) -> list[PromptMessage]:
    """Generate feature implementation prompt (REQ-PRM-003)."""
    description = args["description"]
    related = args.get("related_entities", "")

    # Search for related entities
    from codegraph_mcp.core.graph import GraphQuery
    result = await engine.query(GraphQuery(query=description, max_results=10))

    related_text = "\n".join(
        f"- {e.type.value} `{e.qualified_name}` in {e.file_path}"
        for e in result.entities
    )

    context = f"""
# Feature Implementation Request

## Feature Description
{description}

## Related Entities
{related_text or 'No directly related entities found'}

{f'## User-specified Related Entities: {related}' if related else ''}

## Request
Please help implement this feature:
1. Suggest where to add the new code
2. Identify existing code to modify or extend
3. Provide implementation guidance
4. Consider edge cases and error handling
"""

    return [PromptMessage(
        role="user",
        content=TextContent(type="text", text=context),
    )]


async def _prompt_debug_issue(
    args: dict[str, str],
    engine: Any,
    config: Config,
) -> list[PromptMessage]:
    """Generate debug assistance prompt (REQ-PRM-004)."""
    error_message = args["error_message"]
    additional_context = args.get("context", "")

    # Search for entities related to the error
    from codegraph_mcp.core.graph import GraphQuery
    result = await engine.query(GraphQuery(query=error_message, max_results=10))

    related_text = "\n".join(
        f"- {e.type.value} `{e.name}` at {e.file_path}:{e.start_line}"
        for e in result.entities
    )

    context = f"""
# Debug Assistance Request

## Error/Issue
```
{error_message}
```

## Additional Context
{additional_context or 'None provided'}

## Potentially Related Code
{related_text or 'No related code found'}

## Request
Please help debug this issue:
1. Analyze the error message
2. Identify potential causes
3. Suggest debugging steps
4. Recommend fixes
"""

    return [PromptMessage(
        role="user",
        content=TextContent(type="text", text=context),
    )]


async def _prompt_refactor_guidance(
    args: dict[str, str],
    engine: Any,
    config: Config,
) -> list[PromptMessage]:
    """Generate refactoring guidance prompt (REQ-PRM-005)."""
    entity = await engine.get_entity(args["entity_id"])
    goal = args.get("goal", "improve code quality")

    if not entity:
        return [PromptMessage(
            role="user",
            content=TextContent(type="text", text="Entity not found"),
        )]

    # Get usage context
    callers = await engine.find_callers(entity.id)
    callees = await engine.find_callees(entity.id)

    context = f"""
# Refactoring Guidance Request

## Target Entity
- **Name**: {entity.name}
- **Type**: {entity.type.value}
- **File**: {entity.file_path}:{entity.start_line}-{entity.end_line}

## Source Code
```
{entity.source_code or 'Source code not available'}
```

## Usage
- Used by {len(callers)} caller(s)
- Calls {len(callees)} function(s)

## Refactoring Goal
{goal}

## Request
Please provide refactoring guidance:
1. Identify code smells or issues
2. Suggest specific refactoring techniques
3. Show before/after examples
4. Consider impact on callers
"""

    return [PromptMessage(
        role="user",
        content=TextContent(type="text", text=context),
    )]


async def _prompt_test_generation(
    args: dict[str, str],
    engine: Any,
    config: Config,
) -> list[PromptMessage]:
    """Generate test generation prompt (REQ-PRM-006)."""
    entity = await engine.get_entity(args["entity_id"])
    test_type = args.get("test_type", "unit")

    if not entity:
        return [PromptMessage(
            role="user",
            content=TextContent(type="text", text="Entity not found"),
        )]

    # Get dependencies for mocking
    deps = await engine.find_dependencies(entity.id, depth=1)

    context = f"""
# Test Generation Request

## Target Entity
- **Name**: {entity.name}
- **Type**: {entity.type.value}
- **Signature**: {entity.signature or 'N/A'}

## Source Code
```
{entity.source_code or 'Source code not available'}
```

## Dependencies (may need mocking)
{chr(10).join(f'- {e.name}' for e in deps.entities[:10])}

## Test Type
{test_type}

## Request
Please generate {test_type} tests for this code:
1. Cover main functionality
2. Test edge cases
3. Test error conditions
4. Suggest mocking strategy for dependencies
"""

    return [PromptMessage(
        role="user",
        content=TextContent(type="text", text=context),
    )]
