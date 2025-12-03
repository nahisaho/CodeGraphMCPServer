"""
Java Language Extractor

Extracts entities and relations from Java source files.

Requirements: REQ-AST-005
Design Reference: CHANGE-003-v0.2.0-language-expansion.md
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


class JavaExtractor(BaseExtractor):
    """
    Java-specific entity and relation extractor.

    Extracts:
    - Classes
    - Interfaces
    - Enums
    - Methods
    - Constructors
    - Import statements
    - Inheritance relations (extends/implements)

    Requirements: REQ-AST-005
    """

    config = LanguageConfig(
        name="java",
        extensions=[".java"],
        tree_sitter_name="java",
        function_nodes=["method_declaration", "constructor_declaration"],
        class_nodes=["class_declaration", "enum_declaration"],
        import_nodes=["import_declaration"],
        interface_nodes=["interface_declaration"],
    )

    def extract(
        self,
        tree: Any,
        file_path: Path,
        source_code: str,
    ) -> ParseResult:
        """Extract entities and relations from Java AST."""
        # Set source bytes for correct byte offset handling
        self._set_source(source_code)

        entities: list[Entity] = []
        relations: list[Relation] = []

        # Create module entity (compilation unit)
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

        if node.type == "class_declaration":
            entity = self._extract_class(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))

                # Extract inheritance relations
                self._extract_inheritance(node, source_code, entity.id, relations)

                # Process class body
                old_class = self._current_class
                old_class_id = self._current_class_id
                self._current_class = entity.name
                self._current_class_id = entity.id

                for child in node.children:
                    if child.type == "class_body":
                        for body_child in child.children:
                            self._walk_tree(
                                body_child, file_path, source_code,
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

                # Process interface body
                old_class = self._current_class
                old_class_id = self._current_class_id
                self._current_class = entity.name
                self._current_class_id = entity.id

                for child in node.children:
                    if child.type == "interface_body":
                        for body_child in child.children:
                            self._walk_tree(
                                body_child, file_path, source_code,
                                entities, relations, entity.id,
                            )

                self._current_class = old_class
                self._current_class_id = old_class_id
                return

        elif node.type == "enum_declaration":
            entity = self._extract_enum(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))

        elif node.type == "method_declaration":
            entity = self._extract_method(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                # Extract call relations
                self._extract_calls(node, file_path, source_code, entity.id, relations)

        elif node.type == "constructor_declaration":
            entity = self._extract_constructor(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                # Extract call relations
                self._extract_calls(node, file_path, source_code, entity.id, relations)

        elif node.type == "import_declaration":
            self._extract_import(node, source_code, parent_id, relations)

        # Recurse into children
        for child in node.children:
            self._walk_tree(
                child, file_path, source_code,
                entities, relations, parent_id,
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
            if child.type == "identifier":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        qualified_name = f"{file_path}::{name}"
        docstring = self._extract_javadoc(node, source_code)

        return Entity(
            id=self._generate_entity_id(file_path, name, node.start_point[0] + 1),
            type=EntityType.CLASS,
            name=name,
            qualified_name=qualified_name,
            location=Location(
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                start_column=node.start_point[1],
                end_line=node.end_point[0] + 1,
                end_column=node.end_point[1],
            ),
            docstring=docstring,
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
            if child.type == "identifier":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        qualified_name = f"{file_path}::{name}"
        docstring = self._extract_javadoc(node, source_code)

        return Entity(
            id=self._generate_entity_id(file_path, name, node.start_point[0] + 1),
            type=EntityType.INTERFACE,
            name=name,
            qualified_name=qualified_name,
            location=Location(
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                start_column=node.start_point[1],
                end_line=node.end_point[0] + 1,
                end_column=node.end_point[1],
            ),
            docstring=docstring,
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
            if child.type == "identifier":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        qualified_name = f"{file_path}::{name}"

        return Entity(
            id=self._generate_entity_id(file_path, name, node.start_point[0] + 1),
            type=EntityType.ENUM,
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

    def _extract_method(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract method entity."""
        name = None
        for child in node.children:
            if child.type == "identifier":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        if self._current_class:
            qualified_name = f"{file_path}::{self._current_class}.{name}"
        else:
            qualified_name = f"{file_path}::{name}"

        signature = self._extract_method_signature(node, name, source_code)
        docstring = self._extract_javadoc(node, source_code)

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
            signature=signature,
            docstring=docstring,
            source_code=self._get_node_text(node, source_code),
        )

    def _extract_constructor(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract constructor entity."""
        name = None
        for child in node.children:
            if child.type == "identifier":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        qualified_name = f"{file_path}::{name}.<init>"
        signature = self._extract_constructor_signature(node, name, source_code)

        return Entity(
            id=self._generate_entity_id(file_path, f"{name}.<init>", node.start_point[0] + 1),
            type=EntityType.METHOD,  # Constructors as methods
            name=f"{name}",
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

    def _extract_inheritance(
        self,
        node: Any,
        source_code: str,
        class_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract inheritance (extends/implements) relations."""
        for child in node.children:
            if child.type == "superclass":
                # extends clause
                for super_child in child.children:
                    if super_child.type == "type_identifier":
                        parent_name = self._get_node_text(super_child, source_code)
                        relations.append(Relation(
                            source_id=class_id,
                            target_id=f"unresolved::{parent_name}",
                            type=RelationType.INHERITS,
                        ))

            elif child.type == "super_interfaces":
                # implements clause
                for iface_child in child.children:
                    if iface_child.type == "type_list":
                        for type_child in iface_child.children:
                            if type_child.type == "type_identifier":
                                iface_name = self._get_node_text(type_child, source_code)
                                relations.append(Relation(
                                    source_id=class_id,
                                    target_id=f"unresolved::{iface_name}",
                                    type=RelationType.IMPLEMENTS,
                                ))

    def _extract_import(
        self,
        node: Any,
        source_code: str,
        parent_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract import relation."""
        # Find the scoped_identifier or identifier
        for child in node.children:
            if child.type == "scoped_identifier":
                import_path = self._get_node_text(child, source_code)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=f"module::{import_path}",
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
        """Extract method call relations."""
        if node.type == "method_invocation":
            # Get the method name
            for child in node.children:
                if child.type == "identifier":
                    method_name = self._get_node_text(child, source_code)
                    relations.append(Relation(
                        source_id=caller_id,
                        target_id=f"unresolved::{method_name}",
                        type=RelationType.CALLS,
                    ))
                    break

        elif node.type == "object_creation_expression":
            # new ClassName()
            for child in node.children:
                if child.type == "type_identifier":
                    class_name = self._get_node_text(child, source_code)
                    relations.append(Relation(
                        source_id=caller_id,
                        target_id=f"unresolved::{class_name}.<init>",
                        type=RelationType.CALLS,
                    ))
                    break

        # Recurse
        for child in node.children:
            self._extract_calls(child, file_path, source_code, caller_id, relations)

    def _extract_method_signature(
        self,
        node: Any,
        name: str,
        source_code: str,
    ) -> str:
        """Extract method signature."""
        return_type = "void"
        params = ""
        modifiers = ""

        for child in node.children:
            if child.type == "modifiers":
                modifiers = self._get_node_text(child, source_code) + " "
            elif child.type in ("type_identifier", "void_type", "integral_type",
                               "floating_point_type", "boolean_type", "array_type",
                               "generic_type"):
                return_type = self._get_node_text(child, source_code)
            elif child.type == "formal_parameters":
                params = self._get_node_text(child, source_code)

        return f"{modifiers}{return_type} {name}{params}"

    def _extract_constructor_signature(
        self,
        node: Any,
        name: str,
        source_code: str,
    ) -> str:
        """Extract constructor signature."""
        params = ""
        modifiers = ""

        for child in node.children:
            if child.type == "modifiers":
                modifiers = self._get_node_text(child, source_code) + " "
            elif child.type == "formal_parameters":
                params = self._get_node_text(child, source_code)

        return f"{modifiers}{name}{params}"

    def _extract_javadoc(self, node: Any, source_code: str) -> str | None:
        """Extract Javadoc comment if present."""
        # Simplified - would need to check previous sibling for block_comment
        return None


# Register the extractor
register_extractor("java", JavaExtractor)
