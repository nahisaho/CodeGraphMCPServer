"""
Go Language Extractor

Extracts entities and relations from Go source files.

Requirements: REQ-AST-004
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


class GoExtractor(BaseExtractor):
    """
    Go-specific entity and relation extractor.

    Extracts:
    - Functions (func)
    - Structs (type X struct)
    - Interfaces (type X interface)
    - Methods (func (r Receiver) Method())
    - Package declarations
    - Import statements

    Requirements: REQ-AST-004
    """

    config = LanguageConfig(
        name="go",
        extensions=[".go"],
        tree_sitter_name="go",
        function_nodes=["function_declaration", "method_declaration"],
        class_nodes=["type_declaration"],  # For struct
        import_nodes=["import_declaration", "import_spec"],
        interface_nodes=["type_declaration"],  # For interface
    )

    def extract(
        self,
        tree: Any,
        file_path: Path,
        source_code: str,
    ) -> ParseResult:
        """Extract entities and relations from Go AST."""
        # Set source bytes for correct byte offset handling
        self._set_source(source_code)

        entities: list[Entity] = []
        relations: list[Relation] = []

        # Extract package name for module entity
        package_name = self._extract_package_name(tree.root_node, source_code)
        module_name = package_name or file_path.stem
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

        # Track current receiver type for method extraction
        self._current_receiver: str | None = None

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

    def _extract_package_name(self, root_node: Any, source_code: str) -> str | None:
        """Extract package name from AST."""
        for child in root_node.children:
            if child.type == "package_clause":
                for pkg_child in child.children:
                    if pkg_child.type == "package_identifier":
                        return self._get_node_text(pkg_child, source_code)
        return None

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
                # Extract call relations
                self._extract_calls(node, file_path, source_code, entity.id, relations)

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

        elif node.type == "type_declaration":
            # Can be struct, interface, or type alias
            self._extract_type_declaration(
                node, file_path, source_code, entities, relations, parent_id
            )

        elif node.type in ("import_declaration", "import_spec"):
            self._extract_import(node, file_path, source_code, parent_id, relations)

        # Recurse into children
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
        """Extract function entity from function_declaration."""
        name = None
        for child in node.children:
            if child.type == "identifier":
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        qualified_name = f"{file_path}::{name}"

        # Extract signature (parameters and return type)
        signature = self._extract_function_signature(node, name, source_code)

        # Extract doc comment (preceding comment)
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

    def _extract_method(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract method entity from method_declaration."""
        name = None
        receiver_type = None

        for child in node.children:
            if child.type == "parameter_list":
                # First parameter_list is the receiver
                if receiver_type is None:
                    receiver_type = self._extract_receiver_type(child, source_code)
            elif child.type == "field_identifier":
                name = self._get_node_text(child, source_code)

        if not name:
            return None

        if receiver_type:
            qualified_name = f"{file_path}::{receiver_type}.{name}"
        else:
            qualified_name = f"{file_path}::{name}"

        # Extract signature
        signature = self._extract_method_signature(node, name, receiver_type, source_code)

        # Extract doc comment
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

    def _extract_receiver_type(self, param_list: Any, source_code: str) -> str | None:
        """Extract receiver type from parameter list."""
        for child in param_list.children:
            if child.type == "parameter_declaration":
                for param_child in child.children:
                    if param_child.type == "type_identifier":
                        return self._get_node_text(param_child, source_code)
                    elif param_child.type == "pointer_type":
                        # *Type
                        for ptr_child in param_child.children:
                            if ptr_child.type == "type_identifier":
                                return self._get_node_text(ptr_child, source_code)
        return None

    def _extract_type_declaration(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        entities: list[Entity],
        relations: list[Relation],
        parent_id: str,
    ) -> None:
        """Extract struct, interface, or type alias from type_declaration."""
        for child in node.children:
            if child.type == "type_spec":
                self._extract_type_spec(
                    child, file_path, source_code, entities, relations, parent_id
                )

    def _extract_type_spec(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        entities: list[Entity],
        relations: list[Relation],
        parent_id: str,
    ) -> None:
        """Extract from type_spec node."""
        name = None
        type_node = None

        for child in node.children:
            if child.type == "type_identifier":
                name = self._get_node_text(child, source_code)
            elif child.type == "struct_type":
                type_node = child
                entity_type = EntityType.STRUCT
            elif child.type == "interface_type":
                type_node = child
                entity_type = EntityType.INTERFACE

        if not name or not type_node:
            return

        qualified_name = f"{file_path}::{name}"
        docstring = self._extract_doc_comment(node, source_code)

        entity = Entity(
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
            docstring=docstring,
            source_code=self._get_node_text(node, source_code),
        )

        entities.append(entity)
        relations.append(Relation(
            source_id=parent_id,
            target_id=entity.id,
            type=RelationType.CONTAINS,
        ))

        # Extract interface method signatures for implements detection
        if entity_type == EntityType.INTERFACE:
            self._extract_interface_methods(type_node, file_path, source_code, entity.id, relations)

    def _extract_interface_methods(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        interface_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract method signatures from interface."""
        # Interface methods can be used for implements detection
        for child in node.children:
            if child.type == "method_spec":
                for spec_child in child.children:
                    if spec_child.type == "field_identifier":
                        self._get_node_text(spec_child, source_code)
                        break
                # Could store method specs for later matching

    def _extract_import(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        parent_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract import relations."""
        if node.type == "import_declaration":
            # import "path" or import ( ... )
            for child in node.children:
                if child.type == "import_spec":
                    self._extract_import_spec(child, source_code, parent_id, relations)
                elif child.type == "import_spec_list":
                    for spec in child.children:
                        if spec.type == "import_spec":
                            self._extract_import_spec(spec, source_code, parent_id, relations)
        elif node.type == "import_spec":
            self._extract_import_spec(node, source_code, parent_id, relations)

    def _extract_import_spec(
        self,
        node: Any,
        source_code: str,
        parent_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract single import spec."""
        for child in node.children:
            if child.type == "interpreted_string_literal":
                import_path = self._get_node_text(child, source_code)
                # Remove quotes
                import_path = import_path.strip('"')
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=f"module::{import_path}",
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
            func_node = None
            for child in node.children:
                if child.type in ("identifier", "selector_expression"):
                    func_node = child
                    break

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

    def _extract_function_signature(
        self,
        node: Any,
        name: str,
        source_code: str,
    ) -> str:
        """Extract function signature."""
        params = ""
        returns = ""

        for child in node.children:
            if child.type == "parameter_list":
                params = self._get_node_text(child, source_code)
            elif child.type in ("type_identifier", "pointer_type", "slice_type",
                               "map_type", "channel_type", "function_type",
                               "qualified_type", "parameter_list"):
                # Return type
                if params:  # Already got params, this is return
                    returns = " " + self._get_node_text(child, source_code)

        return f"func {name}{params}{returns}"

    def _extract_method_signature(
        self,
        node: Any,
        name: str,
        receiver_type: str | None,
        source_code: str,
    ) -> str:
        """Extract method signature."""
        params = ""
        returns = ""
        receiver = ""
        param_count = 0

        for child in node.children:
            if child.type == "parameter_list":
                param_count += 1
                if param_count == 1 and receiver_type:
                    receiver = self._get_node_text(child, source_code)
                else:
                    params = self._get_node_text(child, source_code)
            elif child.type in ("type_identifier", "pointer_type", "slice_type"):
                returns = " " + self._get_node_text(child, source_code)

        if receiver:
            return f"func {receiver} {name}{params}{returns}"
        return f"func {name}{params}{returns}"

    def _extract_doc_comment(self, node: Any, source_code: str) -> str | None:
        """Extract doc comment preceding a declaration."""
        # Go doc comments are // comments directly above declarations
        # This is a simplified version - real implementation would check
        # previous siblings for comment nodes
        return None


# Register the extractor
register_extractor("go", GoExtractor)
