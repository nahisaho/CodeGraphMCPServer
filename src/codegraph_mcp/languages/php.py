"""
PHP Language Extractor

Extracts entities and relations from PHP source files.

Requirements: REQ-AST-005
Design Reference: v0.3.0 Language Expansion
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


class PHPExtractor(BaseExtractor):
    """
    PHP-specific entity and relation extractor.

    Extracts:
    - Classes (class)
    - Functions (function)
    - Methods (public/private/protected function)
    - Interfaces (interface)
    - Traits (trait)
    - Namespaces (namespace)
    - Use statements (imports)

    Requirements: REQ-AST-005
    """

    config = LanguageConfig(
        name="php",
        extensions=[".php"],
        tree_sitter_name="php",
        function_nodes=["function_definition", "method_declaration"],
        class_nodes=["class_declaration"],
        import_nodes=["namespace_use_declaration"],
        interface_nodes=["interface_declaration"],
    )

    def extract(
        self,
        tree: Any,
        file_path: Path,
        source_code: str,
    ) -> ParseResult:
        """Extract entities and relations from PHP AST."""
        # Set source bytes for correct byte offset handling
        self._set_source(source_code)

        entities: list[Entity] = []
        relations: list[Relation] = []

        # Extract namespace for module entity
        namespace = self._extract_namespace(tree.root_node, source_code)
        module_name = namespace or file_path.stem
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

        # Walk the tree
        self._walk_tree(
            tree.root_node,
            file_path,
            source_code,
            entities,
            relations,
            module_id,
            namespace,
        )

        return ParseResult(entities=entities, relations=relations)

    def _extract_namespace(self, root_node: Any, source_code: str) -> str | None:
        """Extract namespace from AST."""
        for child in root_node.children:
            if child.type == "php_tag":
                continue
            if child.type == "namespace_definition":
                for ns_child in child.children:
                    if ns_child.type == "namespace_name":
                        return self._get_node_text(ns_child, source_code)
        return None

    def _walk_tree(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        entities: list[Entity],
        relations: list[Relation],
        parent_id: str,
        namespace: str | None,
    ) -> None:
        """Recursively walk the AST tree."""

        if node.type == "function_definition":
            entity = self._extract_function(node, file_path, source_code, namespace)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                self._extract_calls(node, file_path, source_code, entity.id, relations)

        elif node.type == "class_declaration":
            entity = self._extract_class(node, file_path, source_code, namespace)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                # Extract extends/implements
                self._extract_inheritance(node, source_code, entity.id, relations)
                # Extract methods within class
                self._extract_class_members(
                    node, file_path, source_code, entities, relations, entity.id, namespace
                )

        elif node.type == "interface_declaration":
            entity = self._extract_interface(node, file_path, source_code, namespace)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                self._extract_interface_extends(node, source_code, entity.id, relations)

        elif node.type == "trait_declaration":
            entity = self._extract_trait(node, file_path, source_code, namespace)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                # Extract methods within trait
                self._extract_class_members(
                    node, file_path, source_code, entities, relations, entity.id, namespace
                )

        elif node.type == "namespace_use_declaration":
            self._extract_use_statement(node, source_code, parent_id, relations)

        # Recurse into children (but not into class bodies - handled separately)
        if node.type not in ("class_declaration", "interface_declaration", "trait_declaration"):
            for child in node.children:
                self._walk_tree(
                    child, file_path, source_code,
                    entities, relations, parent_id, namespace,
                )

    def _extract_function(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        namespace: str | None,
    ) -> Entity | None:
        """Extract function entity from function_definition."""
        name = None
        for child in node.children:
            if child.type == "name":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        if namespace:
            qualified_name = f"{file_path}::{namespace}\\{name}"
        else:
            qualified_name = f"{file_path}::{name}"

        signature = self._extract_function_signature(node, name, source_code)
        docstring = self._extract_doc_comment(node, source_code)

        return Entity(
            id=self._generate_entity_id(file_path, name, node.start_point[0] + 1),
            type=EntityType.FUNCTION,
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

    def _extract_class(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        namespace: str | None,
    ) -> Entity | None:
        """Extract class entity from class_declaration."""
        name = None
        for child in node.children:
            if child.type == "name":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        if namespace:
            qualified_name = f"{file_path}::{namespace}\\{name}"
        else:
            qualified_name = f"{file_path}::{name}"

        docstring = self._extract_doc_comment(node, source_code)

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
        namespace: str | None,
    ) -> Entity | None:
        """Extract interface entity from interface_declaration."""
        name = None
        for child in node.children:
            if child.type == "name":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        if namespace:
            qualified_name = f"{file_path}::{namespace}\\{name}"
        else:
            qualified_name = f"{file_path}::{name}"

        docstring = self._extract_doc_comment(node, source_code)

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

    def _extract_trait(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        namespace: str | None,
    ) -> Entity | None:
        """Extract trait entity from trait_declaration."""
        name = None
        for child in node.children:
            if child.type == "name":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        if namespace:
            qualified_name = f"{file_path}::{namespace}\\{name}"
        else:
            qualified_name = f"{file_path}::{name}"

        docstring = self._extract_doc_comment(node, source_code)

        return Entity(
            id=self._generate_entity_id(file_path, name, node.start_point[0] + 1),
            type=EntityType.TRAIT,
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

    def _extract_class_members(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        entities: list[Entity],
        relations: list[Relation],
        class_id: str,
        namespace: str | None,
    ) -> None:
        """Extract methods and properties from class body."""
        for child in node.children:
            if child.type == "declaration_list":
                for member in child.children:
                    if member.type == "method_declaration":
                        entity = self._extract_method(member, file_path, source_code, namespace)
                        if entity:
                            entities.append(entity)
                            relations.append(Relation(
                                source_id=class_id,
                                target_id=entity.id,
                                type=RelationType.CONTAINS,
                            ))
                            self._extract_calls(member, file_path, source_code, entity.id, relations)

    def _extract_method(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        namespace: str | None,
    ) -> Entity | None:
        """Extract method entity from method_declaration."""
        name = None
        for child in node.children:
            if child.type == "name":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        qualified_name = f"{file_path}::{name}"
        signature = self._extract_method_signature(node, name, source_code)
        docstring = self._extract_doc_comment(node, source_code)

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

    def _extract_inheritance(
        self,
        node: Any,
        source_code: str,
        class_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract extends and implements relations."""
        for child in node.children:
            if child.type == "base_clause":
                # extends
                for base_child in child.children:
                    if base_child.type == "name":
                        parent_class = self._get_node_text(base_child, source_code)
                        relations.append(Relation(
                            source_id=class_id,
                            target_id=f"unresolved::{parent_class}",
                            type=RelationType.INHERITS,
                        ))
            elif child.type == "class_interface_clause":
                # implements
                for impl_child in child.children:
                    if impl_child.type == "name":
                        interface_name = self._get_node_text(impl_child, source_code)
                        relations.append(Relation(
                            source_id=class_id,
                            target_id=f"unresolved::{interface_name}",
                            type=RelationType.IMPLEMENTS,
                        ))

    def _extract_interface_extends(
        self,
        node: Any,
        source_code: str,
        interface_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract interface extends relations."""
        for child in node.children:
            if child.type == "base_clause":
                for base_child in child.children:
                    if base_child.type == "name":
                        parent_interface = self._get_node_text(base_child, source_code)
                        relations.append(Relation(
                            source_id=interface_id,
                            target_id=f"unresolved::{parent_interface}",
                            type=RelationType.INHERITS,
                        ))

    def _extract_use_statement(
        self,
        node: Any,
        source_code: str,
        parent_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract use statement (imports)."""
        for child in node.children:
            if child.type == "namespace_use_clause":
                for use_child in child.children:
                    if use_child.type == "qualified_name":
                        import_name = self._get_node_text(use_child, source_code)
                        relations.append(Relation(
                            source_id=parent_id,
                            target_id=f"module::{import_name}",
                            type=RelationType.IMPORTS,
                        ))

    def _extract_calls(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        caller_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract function/method call relations."""
        if node.type == "function_call_expression":
            for child in node.children:
                if child.type == "name":
                    func_name = self._get_node_text(child, source_code)
                    relations.append(Relation(
                        source_id=caller_id,
                        target_id=f"unresolved::{func_name}",
                        type=RelationType.CALLS,
                    ))
                    break

        elif node.type == "member_call_expression":
            for child in node.children:
                if child.type == "name":
                    method_name = self._get_node_text(child, source_code)
                    relations.append(Relation(
                        source_id=caller_id,
                        target_id=f"unresolved::{method_name}",
                        type=RelationType.CALLS,
                    ))
                    break

        elif node.type == "scoped_call_expression":
            # Static method call
            for child in node.children:
                if child.type == "name":
                    method_name = self._get_node_text(child, source_code)
                    relations.append(Relation(
                        source_id=caller_id,
                        target_id=f"unresolved::{method_name}",
                        type=RelationType.CALLS,
                    ))
                    break

        for child in node.children:
            self._extract_calls(child, file_path, source_code, caller_id, relations)

    def _extract_function_signature(
        self,
        node: Any,
        name: str,
        source_code: str,
    ) -> str:
        """Extract function signature."""
        params = ""
        return_type = ""

        for child in node.children:
            if child.type == "formal_parameters":
                params = self._get_node_text(child, source_code)
            elif child.type in ("type", "union_type", "named_type"):
                return_type = ": " + self._get_node_text(child, source_code)

        return f"function {name}{params}{return_type}"

    def _extract_method_signature(
        self,
        node: Any,
        name: str,
        source_code: str,
    ) -> str:
        """Extract method signature with visibility."""
        params = ""
        return_type = ""
        visibility = "public"

        for child in node.children:
            if child.type == "formal_parameters":
                params = self._get_node_text(child, source_code)
            elif child.type in ("type", "union_type", "named_type"):
                return_type = ": " + self._get_node_text(child, source_code)
            elif child.type == "visibility_modifier":
                visibility = self._get_node_text(child, source_code)

        return f"{visibility} function {name}{params}{return_type}"

    def _extract_doc_comment(self, node: Any, source_code: str) -> str | None:
        """Extract PHPDoc comment."""
        # Look for comment node before this node
        return None


# Register the extractor
register_extractor("php", PHPExtractor)
