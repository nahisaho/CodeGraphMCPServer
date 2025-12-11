"""
Lua Language Extractor

Extracts entities and relations from Lua source files.

Requirements: REQ-AST-013
Design Reference: v0.8.0 language expansion
"""

from pathlib import Path
from typing import Any

from codegraph_mcp.core.parser import (
    Entity,
    EntityType,
    Location,
    ParseResult,
    Relation,
    RelationType,
)
from codegraph_mcp.languages.config import (
    BaseExtractor,
    LanguageConfig,
    register_extractor,
)


class LuaExtractor(BaseExtractor):
    """
    Lua-specific entity and relation extractor.

    Extracts:
    - Functions (global and local)
    - Tables (as modules/classes)
    - Require statements
    - Function calls

    Requirements: REQ-AST-013
    """

    config = LanguageConfig(
        name="lua",
        extensions=[".lua"],
        tree_sitter_name="lua",
        function_nodes=["function_declaration", "local_function_declaration"],
        class_nodes=[],  # Lua doesn't have classes, but tables act as modules
        import_nodes=[],  # require() is a function call
        interface_nodes=None,
    )

    def extract(
        self,
        tree: Any,
        file_path: Path,
        source_code: str,
    ) -> ParseResult:
        """Extract entities and relations from Lua AST."""
        self._set_source(source_code)

        entities: list[Entity] = []
        relations: list[Relation] = []

        # Create module entity
        module_name = file_path.stem
        module_id = self._generate_entity_id(file_path, module_name, 1)

        entities.append(Entity(
            id=module_id,
            type=EntityType.MODULE,
            name=module_name,
            qualified_name=str(file_path),
            location=Location(
                file_path=file_path,
                start_line=1,
                start_column=0,
                end_line=source_code.count("\n") + 1,
                end_column=0,
            ),
        ))

        self._walk_tree(
            tree.root_node,
            file_path,
            source_code,
            entities,
            relations,
            module_id,
        )

        return ParseResult(entities=entities, relations=relations)

    def _walk_tree(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        entities: list[Entity],
        relations: list[Relation],
        parent_id: str,
    ) -> None:
        """Recursively walk the AST tree."""

        if node.type in ("function_declaration", "local_function_declaration"):
            entity = self._extract_function(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                self._extract_calls(
                    node, file_path, source_code,
                    entity.id, relations, entities
                )

        elif node.type == "function_definition":
            # Anonymous function assigned to variable
            entity = self._extract_anonymous_function(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))

        elif node.type == "function_call":
            # Check for require() calls
            self._check_require(node, file_path, source_code, entities, relations, parent_id)

        # Continue walking children
        for child in node.children:
            self._walk_tree(
                child, file_path, source_code,
                entities, relations, parent_id
            )

    def _extract_function(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract function entity."""
        name = None
        is_local = node.type == "local_function_declaration"

        for child in node.children:
            if child.type == "identifier":
                name = self._get_node_text(child, source_code)
                break
            elif child.type == "function_name":
                # Handle dot-notation names like M.func
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        return Entity(
            id=self._generate_entity_id(file_path, name, node.start_point[0] + 1),
            type=EntityType.FUNCTION,
            name=name,
            qualified_name=f"{file_path}::{name}",
            location=Location(
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                start_column=node.start_point[1],
                end_line=node.end_point[0] + 1,
                end_column=node.end_point[1],
            ),
            metadata={"lua_scope": "local" if is_local else "global"},
        )

    def _extract_anonymous_function(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract anonymous function (assigned to variable)."""
        # This handles: local foo = function() end
        # We need to look at parent for the variable name
        return None  # Skip for now, complex to track

    def _check_require(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        entities: list[Entity],
        relations: list[Relation],
        parent_id: str,
    ) -> None:
        """Check for require() calls and extract as imports."""
        # Get function name
        func_name = None
        args = None

        for child in node.children:
            if child.type == "identifier":
                func_name = self._get_node_text(child, source_code)
            elif child.type == "arguments":
                args = child

        if func_name == "require" and args:
            # Extract module name from arguments
            for arg_child in args.children:
                if arg_child.type == "string":
                    module_name = self._get_node_text(arg_child, source_code)
                    # Remove quotes
                    module_name = module_name.strip("'\"")

                    entity = Entity(
                        id=self._generate_entity_id(
                            file_path, f"require_{module_name}", node.start_point[0] + 1
                        ),
                        type=EntityType.MODULE,
                        name=module_name,
                        qualified_name=module_name,
                        location=Location(
                            file_path=file_path,
                            start_line=node.start_point[0] + 1,
                            start_column=node.start_point[1],
                            end_line=node.end_point[0] + 1,
                            end_column=node.end_point[1],
                        ),
                    )
                    entities.append(entity)
                    relations.append(Relation(
                        source_id=parent_id,
                        target_id=entity.id,
                        type=RelationType.IMPORTS,
                    ))
                    break

    def _extract_calls(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        caller_id: str,
        relations: list[Relation],
        entities: list[Entity],
    ) -> None:
        """Extract function calls from a function body."""
        if node.type == "function_call":
            # Get the function being called
            for child in node.children:
                if child.type == "identifier":
                    callee_name = self._get_node_text(child, source_code)
                    # Skip require() as it's handled separately
                    if callee_name != "require":
                        relations.append(Relation(
                            source_id=caller_id,
                            target_id=callee_name,
                            type=RelationType.CALLS,
                        ))
                    break
                elif child.type in ("field_expression", "method_index_expression"):
                    callee_name = self._get_node_text(child, source_code)
                    relations.append(Relation(
                        source_id=caller_id,
                        target_id=callee_name,
                        type=RelationType.CALLS,
                    ))
                    break

        for child in node.children:
            self._extract_calls(child, file_path, source_code, caller_id, relations, entities)


# Register the extractor
register_extractor("lua", LuaExtractor)
