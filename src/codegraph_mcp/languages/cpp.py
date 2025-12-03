"""
C++ Language Extractor

Extracts entities and relations from C++ source files.

Requirements: REQ-AST-007
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


class CppExtractor(BaseExtractor):
    """
    C/C++-specific entity and relation extractor.

    Extracts:
    - Classes (class)
    - Structs (struct)
    - Functions (function)
    - Methods (member functions)
    - Namespaces (namespace)
    - Include statements
    - Templates

    Requirements: REQ-AST-007
    """

    config = LanguageConfig(
        name="cpp",
        extensions=[".c", ".cpp", ".cc", ".cxx", ".hpp", ".h", ".hxx"],
        tree_sitter_name="cpp",
        function_nodes=["function_definition"],
        class_nodes=["class_specifier", "struct_specifier"],
        import_nodes=["preproc_include"],
        interface_nodes=[],
    )

    def extract(
        self,
        tree: Any,
        file_path: Path,
        source_code: str,
    ) -> ParseResult:
        """Extract entities and relations from C/C++ AST."""
        # Set source bytes for correct byte offset handling
        self._set_source(source_code)

        entities: list[Entity] = []
        relations: list[Relation] = []

        # Use filename as module
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

        # Track current namespace
        self._current_namespace: list[str] = []

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

        if node.type == "function_definition":
            entity = self._extract_function(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                self._extract_calls(node, file_path, source_code, entity.id, relations)

        elif node.type == "class_specifier":
            entity = self._extract_class(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                self._extract_base_classes(node, source_code, entity.id, relations)
                self._extract_class_members(
                    node, file_path, source_code, entities, relations, entity.id
                )

        elif node.type == "struct_specifier":
            entity = self._extract_struct(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                self._extract_class_members(
                    node, file_path, source_code, entities, relations, entity.id
                )

        elif node.type == "namespace_definition":
            self._process_namespace(
                node, file_path, source_code, entities, relations, parent_id
            )
            return  # Namespace handles its own children

        elif node.type == "preproc_include":
            self._extract_include(node, source_code, parent_id, relations)

        # Recurse (but not into class bodies - handled separately)
        if node.type not in ("class_specifier", "struct_specifier"):
            for child in node.children:
                self._walk_tree(
                    child, file_path, source_code,
                    entities, relations, parent_id,
                )

    def _process_namespace(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        entities: list[Entity],
        relations: list[Relation],
        parent_id: str,
    ) -> None:
        """Process namespace and its contents."""
        ns_name = None
        body = None

        for child in node.children:
            if child.type in ("identifier", "namespace_identifier"):
                ns_name = self._get_node_text(child, source_code)
            elif child.type == "declaration_list":
                body = child

        if ns_name:
            self._current_namespace.append(ns_name)

        # Process namespace body
        if body:
            for child in body.children:
                self._walk_tree(
                    child, file_path, source_code,
                    entities, relations, parent_id,
                )

        if ns_name:
            self._current_namespace.pop()

    def _get_qualified_name(self, name: str) -> str:
        """Get fully qualified name with namespace."""
        if self._current_namespace:
            return "::".join(self._current_namespace) + "::" + name
        return name

    def _extract_function(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract function entity."""
        name = None

        for child in node.children:
            if child.type == "function_declarator":
                for decl_child in child.children:
                    if decl_child.type in ("identifier", "field_identifier"):
                        name = self._get_node_text(decl_child, source_code)
                        break
                    elif decl_child.type == "qualified_identifier":
                        # Method defined outside class
                        name = self._get_node_text(decl_child, source_code)
                        break

        if not name:
            return None

        qualified_name = f"{file_path}::{self._get_qualified_name(name)}"
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
    ) -> Entity | None:
        """Extract class entity."""
        name = None
        for child in node.children:
            if child.type == "type_identifier":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        qualified_name = f"{file_path}::{self._get_qualified_name(name)}"
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

        qualified_name = f"{file_path}::{self._get_qualified_name(name)}"
        docstring = self._extract_doc_comment(node, source_code)

        return Entity(
            id=self._generate_entity_id(file_path, name, node.start_point[0] + 1),
            type=EntityType.STRUCT,
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
    ) -> None:
        """Extract methods from class body."""
        for child in node.children:
            if child.type == "field_declaration_list":
                for member in child.children:
                    if member.type == "function_definition":
                        entity = self._extract_method(member, file_path, source_code)
                        if entity:
                            entities.append(entity)
                            relations.append(Relation(
                                source_id=class_id,
                                target_id=entity.id,
                                type=RelationType.CONTAINS,
                            ))
                            self._extract_calls(member, file_path, source_code, entity.id, relations)
                    elif member.type == "field_declaration":
                        # Could be method declaration or field - check for function_declarator
                        for decl_child in member.children:
                            if decl_child.type == "function_declarator":
                                entity = self._extract_method_declaration(member, file_path, source_code)
                                if entity:
                                    entities.append(entity)
                                    relations.append(Relation(
                                        source_id=class_id,
                                        target_id=entity.id,
                                        type=RelationType.CONTAINS,
                                    ))
                                break

    def _extract_method(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract method entity from function_definition inside class."""
        name = None

        for child in node.children:
            if child.type == "function_declarator":
                for decl_child in child.children:
                    if decl_child.type in ("identifier", "field_identifier"):
                        name = self._get_node_text(decl_child, source_code)
                        break

        if not name:
            return None

        qualified_name = f"{file_path}::{name}"
        signature = self._extract_function_signature(node, name, source_code)
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

    def _extract_method_declaration(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract method entity from declaration (header only)."""
        name = None

        for child in node.children:
            if child.type == "function_declarator":
                for decl_child in child.children:
                    if decl_child.type in ("identifier", "field_identifier"):
                        name = self._get_node_text(decl_child, source_code)
                        break

        if not name:
            return None

        qualified_name = f"{file_path}::{name}"
        signature = self._get_node_text(node, source_code).rstrip(";")

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
            source_code=self._get_node_text(node, source_code),
        )

    def _extract_base_classes(
        self,
        node: Any,
        source_code: str,
        class_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract inheritance relations."""
        for child in node.children:
            if child.type == "base_class_clause":
                for base in child.children:
                    if base.type == "type_identifier":
                        base_name = self._get_node_text(base, source_code)
                        relations.append(Relation(
                            source_id=class_id,
                            target_id=f"unresolved::{base_name}",
                            type=RelationType.INHERITS,
                        ))

    def _extract_include(
        self,
        node: Any,
        source_code: str,
        parent_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract include directive."""
        for child in node.children:
            if child.type in ("string_literal", "system_lib_string"):
                include_path = self._get_node_text(child, source_code)
                # Remove quotes/brackets
                include_path = include_path.strip('"<>')
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=f"module::{include_path}",
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
        if node.type == "call_expression":
            for child in node.children:
                if child.type == "identifier":
                    func_name = self._get_node_text(child, source_code)
                    relations.append(Relation(
                        source_id=caller_id,
                        target_id=f"unresolved::{func_name}",
                        type=RelationType.CALLS,
                    ))
                    break
                elif child.type == "field_expression":
                    # method call: obj.method()
                    for field_child in child.children:
                        if field_child.type == "field_identifier":
                            method_name = self._get_node_text(field_child, source_code)
                            relations.append(Relation(
                                source_id=caller_id,
                                target_id=f"unresolved::{method_name}",
                                type=RelationType.CALLS,
                            ))
                            break
                    break
                elif child.type == "qualified_identifier":
                    # Namespace::function()
                    func_name = self._get_node_text(child, source_code)
                    relations.append(Relation(
                        source_id=caller_id,
                        target_id=f"unresolved::{func_name}",
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
        return_type = ""
        params = ""

        for child in node.children:
            if child.type in ("primitive_type", "type_identifier", "qualified_identifier"):
                return_type = self._get_node_text(child, source_code)
            elif child.type == "function_declarator":
                for decl_child in child.children:
                    if decl_child.type == "parameter_list":
                        params = self._get_node_text(decl_child, source_code)

        return f"{return_type} {name}{params}"

    def _extract_doc_comment(self, node: Any, source_code: str) -> str | None:
        """Extract doxygen-style comment."""
        return None


# Register the extractor
register_extractor("cpp", CppExtractor)
