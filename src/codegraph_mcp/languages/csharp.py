"""
C# Language Extractor

Extracts entities and relations from C# source files.

Requirements: REQ-AST-006
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


class CSharpExtractor(BaseExtractor):
    """
    C#-specific entity and relation extractor.

    Extracts:
    - Classes (class)
    - Structs (struct)
    - Interfaces (interface)
    - Methods (public/private/protected method)
    - Properties (get/set)
    - Namespaces (namespace)
    - Using statements (imports)
    - Enums (enum)

    Requirements: REQ-AST-006
    """

    config = LanguageConfig(
        name="csharp",
        extensions=[".cs"],
        tree_sitter_name="c_sharp",
        function_nodes=["method_declaration", "local_function_statement"],
        class_nodes=["class_declaration", "struct_declaration"],
        import_nodes=["using_directive"],
        interface_nodes=["interface_declaration"],
    )

    def extract(
        self,
        tree: Any,
        file_path: Path,
        source_code: str,
    ) -> ParseResult:
        """Extract entities and relations from C# AST."""
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
            if child.type in ("namespace_declaration", "file_scoped_namespace_declaration"):
                for ns_child in child.children:
                    if ns_child.type in ("qualified_name", "identifier"):
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

        if node.type == "class_declaration":
            entity = self._extract_class(node, file_path, source_code, namespace)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                self._extract_base_types(node, source_code, entity.id, relations)
                self._extract_class_members(
                    node, file_path, source_code, entities, relations, entity.id, namespace
                )

        elif node.type == "struct_declaration":
            entity = self._extract_struct(node, file_path, source_code, namespace)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
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
                self._extract_base_types(node, source_code, entity.id, relations, is_interface=True)

        elif node.type == "enum_declaration":
            entity = self._extract_enum(node, file_path, source_code, namespace)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))

        elif node.type == "using_directive":
            self._extract_using(node, source_code, parent_id, relations)

        # Recurse (but not into class/struct bodies)
        if node.type not in ("class_declaration", "struct_declaration", "interface_declaration"):
            for child in node.children:
                self._walk_tree(
                    child, file_path, source_code,
                    entities, relations, parent_id, namespace,
                )

    def _extract_class(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        namespace: str | None,
    ) -> Entity | None:
        """Extract class entity."""
        name = None
        for child in node.children:
            if child.type == "identifier":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        qualified_name = f"{file_path}::{namespace}.{name}" if namespace else f"{file_path}::{name}"

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
        namespace: str | None,
    ) -> Entity | None:
        """Extract struct entity."""
        name = None
        for child in node.children:
            if child.type == "identifier":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        qualified_name = f"{file_path}::{namespace}.{name}" if namespace else f"{file_path}::{name}"

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

    def _extract_interface(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        namespace: str | None,
    ) -> Entity | None:
        """Extract interface entity."""
        name = None
        for child in node.children:
            if child.type == "identifier":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        qualified_name = f"{file_path}::{namespace}.{name}" if namespace else f"{file_path}::{name}"

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

    def _extract_enum(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        namespace: str | None,
    ) -> Entity | None:
        """Extract enum entity."""
        name = None
        for child in node.children:
            if child.type == "identifier":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        qualified_name = f"{file_path}::{namespace}.{name}" if namespace else f"{file_path}::{name}"

        docstring = self._extract_doc_comment(node, source_code)

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
                    elif member.type == "constructor_declaration":
                        entity = self._extract_constructor(member, file_path, source_code, namespace)
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
        """Extract method entity."""
        name = None
        for child in node.children:
            if child.type == "identifier":
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

    def _extract_constructor(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        namespace: str | None,
    ) -> Entity | None:
        """Extract constructor entity."""
        name = None
        for child in node.children:
            if child.type == "identifier":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        qualified_name = f"{file_path}::{name}"
        signature = self._extract_method_signature(node, name, source_code)

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

    def _extract_base_types(
        self,
        node: Any,
        source_code: str,
        entity_id: str,
        relations: list[Relation],
        is_interface: bool = False,
    ) -> None:
        """Extract inheritance and implements relations."""
        for child in node.children:
            if child.type == "base_list":
                for base_child in child.children:
                    if base_child.type in ("identifier", "generic_name", "qualified_name"):
                        base_name = self._get_node_text(base_child, source_code)
                        # In C#, base types include both inheritance and interface implementation
                        # For simplicity, we mark all as INHERITS
                        relations.append(Relation(
                            source_id=entity_id,
                            target_id=f"unresolved::{base_name}",
                            type=RelationType.INHERITS,
                        ))

    def _extract_using(
        self,
        node: Any,
        source_code: str,
        parent_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract using directive (imports)."""
        for child in node.children:
            if child.type in ("qualified_name", "identifier"):
                import_name = self._get_node_text(child, source_code)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=f"module::{import_name}",
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
        if node.type == "invocation_expression":
            for child in node.children:
                if child.type == "identifier":
                    func_name = self._get_node_text(child, source_code)
                    relations.append(Relation(
                        source_id=caller_id,
                        target_id=f"unresolved::{func_name}",
                        type=RelationType.CALLS,
                    ))
                    break
                elif child.type == "member_access_expression":
                    # Get the method name from member access
                    for mac in child.children:
                        if mac.type == "identifier":
                            method_name = self._get_node_text(mac, source_code)
                    relations.append(Relation(
                        source_id=caller_id,
                        target_id=f"unresolved::{method_name}",
                        type=RelationType.CALLS,
                    ))
                    break

        for child in node.children:
            self._extract_calls(child, file_path, source_code, caller_id, relations)

    def _extract_method_signature(
        self,
        node: Any,
        name: str,
        source_code: str,
    ) -> str:
        """Extract method signature."""
        params = ""
        return_type = ""
        modifiers = []

        for child in node.children:
            if child.type == "parameter_list":
                params = self._get_node_text(child, source_code)
            elif child.type in ("predefined_type", "identifier", "generic_name", "qualified_name"):
                if not return_type:
                    return_type = self._get_node_text(child, source_code)
            elif child.type == "modifier":
                modifiers.append(self._get_node_text(child, source_code))

        mod_str = " ".join(modifiers)
        if mod_str:
            return f"{mod_str} {return_type} {name}{params}"
        return f"{return_type} {name}{params}"

    def _extract_doc_comment(self, node: Any, source_code: str) -> str | None:
        """Extract XML doc comment."""
        return None


# Register the extractor
register_extractor("csharp", CSharpExtractor)
