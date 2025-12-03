"""
Rust Language Extractor

Extracts entities and relations from Rust source files.

Requirements: REQ-AST-003
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


class RustExtractor(BaseExtractor):
    """
    Rust-specific entity and relation extractor.

    Extracts:
    - Functions
    - Structs and enums
    - Traits and impl blocks
    - Use statements (imports)
    - Call relations

    Requirements: REQ-AST-003
    """

    config = LanguageConfig(
        name="rust",
        extensions=[".rs"],
        tree_sitter_name="rust",
        function_nodes=["function_item"],
        class_nodes=["struct_item", "enum_item"],
        import_nodes=["use_declaration"],
        interface_nodes=["trait_item"],
    )

    def extract(
        self,
        tree: Any,
        file_path: Path,
        source_code: str,
    ) -> ParseResult:
        """Extract entities and relations from Rust AST."""
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

        # Context tracking
        self._current_impl: str | None = None
        self._current_impl_id: str | None = None

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

        if node.type == "function_item":
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

        elif node.type == "struct_item":
            entity = self._extract_struct(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))

        elif node.type == "enum_item":
            entity = self._extract_enum(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))

        elif node.type == "trait_item":
            entity = self._extract_trait(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))

        elif node.type == "impl_item":
            self._extract_impl(
                node, file_path, source_code,
                entities, relations, parent_id,
            )
            return  # impl_item handles its own children

        elif node.type == "use_declaration":
            self._extract_use(
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

        qualified_name = f"{file_path}::{name}"
        entity_type = EntityType.FUNCTION

        if self._current_impl:
            qualified_name = f"{file_path}::{self._current_impl}::{name}"
            entity_type = EntityType.METHOD

        # Extract signature
        signature = None
        for child in node.children:
            if child.type == "parameters":
                params = self._get_node_text(child, source_code)
                signature = f"fn {name}{params}"
                break

        return Entity(
            id=self._generate_entity_id(file_path, name, node.start_point[0] + 1),
            type=entity_type,
            name=name,
            qualified_name=qualified_name,
            location=Location(
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                start_column=node.start_point[1],
                end_line=node.end_point[0] + 1,
                end_column=node.end_point[1],
            ),
            signature=signature,
            source_code=self._get_node_text(node, source_code),
        )

    def _extract_struct(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract struct entity."""
        name = None
        for child in node.children:
            if child.type == "type_identifier":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        return Entity(
            id=self._generate_entity_id(file_path, name, node.start_point[0] + 1),
            type=EntityType.STRUCT,
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

    def _extract_enum(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract enum entity."""
        name = None
        for child in node.children:
            if child.type == "type_identifier":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        return Entity(
            id=self._generate_entity_id(file_path, name, node.start_point[0] + 1),
            type=EntityType.ENUM,
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

    def _extract_trait(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract trait entity."""
        name = None
        for child in node.children:
            if child.type == "type_identifier":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        return Entity(
            id=self._generate_entity_id(file_path, name, node.start_point[0] + 1),
            type=EntityType.TRAIT,
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

    def _extract_impl(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        entities: list[Entity],
        relations: list[Relation],
        parent_id: str,
    ) -> None:
        """Extract impl block and its methods."""
        # Find the type being implemented
        impl_type = None
        trait_name = None

        for child in node.children:
            if child.type == "type_identifier":
                if impl_type is None:
                    impl_type = self._get_node_text(child, source_code)
                else:
                    # Second type_identifier is the trait being implemented
                    trait_name = impl_type
                    impl_type = self._get_node_text(child, source_code)

        if not impl_type:
            return

        # Add implements relation if trait
        if trait_name:
            relations.append(Relation(
                source_id=f"unresolved::{impl_type}",
                target_id=f"unresolved::{trait_name}",
                type=RelationType.IMPLEMENTS,
            ))

        # Process impl body
        old_impl = self._current_impl
        self._current_impl = impl_type

        for child in node.children:
            if child.type == "declaration_list":
                for item in child.children:
                    self._walk_tree(
                        item, file_path, source_code,
                        entities, relations, parent_id,
                    )

        self._current_impl = old_impl

    def _extract_use(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        parent_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract use (import) relations."""
        # Extract the path being imported
        self._get_node_text(node, source_code)

        # Simple path extraction
        for child in node.children:
            if child.type in {"use_tree", "scoped_identifier"}:
                path = self._get_node_text(child, source_code)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=f"module::{path}",
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
                func_text = self._get_node_text(func_node, source_code)
                relations.append(Relation(
                    source_id=caller_id,
                    target_id=f"unresolved::{func_text}",
                    type=RelationType.CALLS,
                ))

        # Recurse
        for child in node.children:
            self._extract_calls(child, file_path, source_code, caller_id, relations)


# Register the extractor
register_extractor("rust", RustExtractor)
