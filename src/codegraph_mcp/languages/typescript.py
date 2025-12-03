"""
TypeScript Language Extractor

Extracts entities and relations from TypeScript source files.

Requirements: REQ-AST-002
Design Reference: design-core-engine.md §2.1
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


class TypeScriptExtractor(BaseExtractor):
    """
    TypeScript-specific entity and relation extractor.

    Extracts:
    - Functions and arrow functions
    - Classes and interfaces
    - Methods
    - Import relations
    - Call relations

    Requirements: REQ-AST-002
    """

    config = LanguageConfig(
        name="typescript",
        extensions=[".ts", ".tsx", ".js", ".jsx"],
        tree_sitter_name="typescript",
        function_nodes=[
            "function_declaration",
            "arrow_function",
            "method_definition",
        ],
        class_nodes=["class_declaration"],
        import_nodes=["import_statement"],
        interface_nodes=["interface_declaration"],
    )

    def extract(
        self,
        tree: Any,
        file_path: Path,
        source_code: str,
    ) -> ParseResult:
        """Extract entities and relations from TypeScript AST."""
        # Set source bytes for correct byte offset handling
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

        # Track current class context
        self._current_class: str | None = None
        self._current_class_id: str | None = None

        # Walk the tree
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

        if node.type == "function_declaration":
            entity = self._extract_function(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                self._extract_calls(
                    node, file_path, source_code, entity.id, relations
                )

        elif node.type == "class_declaration":
            entity = self._extract_class(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))

                # Extract inheritance/implements
                self._extract_class_relations(
                    node, file_path, source_code, entity.id, relations
                )

                # Process class body
                old_class = self._current_class
                old_class_id = self._current_class_id
                self._current_class = entity.name
                self._current_class_id = entity.id

                for child in node.children:
                    if child.type == "class_body":
                        self._walk_tree(
                            child, file_path, source_code,
                            entities, relations, entity.id,
                        )

                self._current_class = old_class
                self._current_class_id = old_class_id
                return

        elif node.type == "interface_declaration":
            entity = self._extract_interface(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))

        elif node.type == "method_definition":
            entity = self._extract_method(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                self._extract_calls(
                    node, file_path, source_code, entity.id, relations
                )

        elif node.type == "import_statement":
            self._extract_import(
                node, file_path, source_code, parent_id, relations
            )

        # Recurse
        for child in node.children:
            self._walk_tree(
                child, file_path, source_code,
                entities, relations, parent_id,
            )

    def _extract_function(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract function entity."""
        name = None
        for child in node.children:
            if child.type == "identifier":
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
            source_code=self._get_node_text(node, source_code),
        )

    def _extract_class(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract class entity."""
        name = None
        for child in node.children:
            if child.type in {"type_identifier", "identifier"}:
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        return Entity(
            id=self._generate_entity_id(file_path, name, node.start_point[0] + 1),
            type=EntityType.CLASS,
            name=name,
            qualified_name=f"{file_path}::{name}",
            location=Location(
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                start_column=node.start_point[1],
                end_line=node.end_point[0] + 1,
                end_column=node.end_point[1],
            ),
            source_code=self._get_node_text(node, source_code),
        )

    def _extract_interface(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract interface entity."""
        name = None
        for child in node.children:
            if child.type in {"type_identifier", "identifier"}:
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        return Entity(
            id=self._generate_entity_id(file_path, name, node.start_point[0] + 1),
            type=EntityType.INTERFACE,
            name=name,
            qualified_name=f"{file_path}::{name}",
            location=Location(
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                start_column=node.start_point[1],
                end_line=node.end_point[0] + 1,
                end_column=node.end_point[1],
            ),
            source_code=self._get_node_text(node, source_code),
        )

    def _extract_method(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract method entity."""
        name = None
        for child in node.children:
            if child.type in {"property_identifier", "identifier"}:
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        qualified_name = f"{file_path}::{name}"
        if self._current_class:
            qualified_name = f"{file_path}::{self._current_class}.{name}"

        return Entity(
            id=self._generate_entity_id(file_path, name, node.start_point[0] + 1),
            type=EntityType.METHOD,
            name=name,
            qualified_name=qualified_name,
            location=Location(
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                start_column=node.start_point[1],
                end_line=node.end_point[0] + 1,
                end_column=node.end_point[1],
            ),
            source_code=self._get_node_text(node, source_code),
        )

    def _extract_class_relations(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        class_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract inheritance and implements relations."""
        for child in node.children:
            if child.type == "class_heritage":
                for heritage in child.children:
                    if heritage.type == "extends_clause":
                        for ext in heritage.children:
                            if ext.type in {"identifier", "type_identifier"}:
                                parent = self._get_node_text(ext, source_code)
                                relations.append(Relation(
                                    source_id=class_id,
                                    target_id=f"unresolved::{parent}",
                                    type=RelationType.INHERITS,
                                ))
                    elif heritage.type == "implements_clause":
                        for impl in heritage.children:
                            if impl.type in {"identifier", "type_identifier"}:
                                iface = self._get_node_text(impl, source_code)
                                relations.append(Relation(
                                    source_id=class_id,
                                    target_id=f"unresolved::{iface}",
                                    type=RelationType.IMPLEMENTS,
                                ))

    def _extract_import(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        parent_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract import relations."""
        # Find the string node with module path
        for child in node.children:
            if child.type == "string":
                module_path = self._get_node_text(child, source_code)
                # Strip quotes
                module_path = module_path.strip("'\"")
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=f"module::{module_path}",
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
    ) -> None:
        """Extract function call relations."""
        if node.type == "call_expression":
            func_node = node.children[0] if node.children else None
            if func_node:
                if func_node.type == "identifier":
                    func_name = self._get_node_text(func_node, source_code)
                    relations.append(Relation(
                        source_id=caller_id,
                        target_id=f"unresolved::{func_name}",
                        type=RelationType.CALLS,
                    ))
                elif func_node.type == "member_expression":
                    # method call: obj.method()
                    text = self._get_node_text(func_node, source_code)
                    relations.append(Relation(
                        source_id=caller_id,
                        target_id=f"unresolved::{text}",
                        type=RelationType.CALLS,
                    ))

        # Recurse
        for child in node.children:
            self._extract_calls(child, file_path, source_code, caller_id, relations)


# Register the extractor
register_extractor("typescript", TypeScriptExtractor)
