"""
Python Language Extractor

Extracts entities and relations from Python source files.

Requirements: REQ-AST-001
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


class PythonExtractor(BaseExtractor):
    """
    Python-specific entity and relation extractor.

    Extracts:
    - Functions and methods
    - Classes
    - Import relations
    - Call relations
    - Inheritance relations

    Requirements: REQ-AST-001
    """

    config = LanguageConfig(
        name="python",
        extensions=[".py", ".pyi"],
        tree_sitter_name="python",
        function_nodes=["function_definition"],
        class_nodes=["class_definition"],
        import_nodes=["import_statement", "import_from_statement"],
    )

    def extract(
        self,
        tree: Any,
        file_path: Path,
        source_code: str,
    ) -> ParseResult:
        """Extract entities and relations from Python AST."""
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

        # Track current class for method extraction
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

        if node.type == "function_definition":
            entity = self._extract_function(node, file_path, source_code)
            if entity:
                entities.append(entity)

                # Add contains relation
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))

                # Extract call relations within function
                self._extract_calls(
                    node, file_path, source_code, entity.id, relations
                )

        elif node.type == "class_definition":
            entity = self._extract_class(node, file_path, source_code)
            if entity:
                entities.append(entity)

                # Add contains relation
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))

                # Extract inheritance relations
                self._extract_inheritance(
                    node, file_path, source_code, entity.id, relations
                )

                # Process class body with this class as context
                old_class = self._current_class
                old_class_id = self._current_class_id
                self._current_class = entity.name
                self._current_class_id = entity.id

                for child in node.children:
                    if child.type == "block":
                        self._walk_tree(
                            child, file_path, source_code,
                            entities, relations, entity.id,
                        )

                self._current_class = old_class
                self._current_class_id = old_class_id
                return

        elif node.type in ("import_statement", "import_from_statement"):
            self._extract_import(
                node, file_path, source_code, parent_id, relations
            )

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
        """Extract function entity from AST node."""
        name_node = None
        for child in node.children:
            if child.type == "identifier":
                name_node = child
                break

        if not name_node:
            return None

        name = self._get_node_text(name_node, source_code)

        # Determine if method or function
        if self._current_class:
            entity_type = EntityType.METHOD
            qualified_name = f"{file_path}::{self._current_class}.{name}"
        else:
            entity_type = EntityType.FUNCTION
            qualified_name = f"{file_path}::{name}"

        # Extract signature (parameters)
        signature = None
        for child in node.children:
            if child.type == "parameters":
                signature = f"def {name}{self._get_node_text(child, source_code)}"
                break

        # Extract docstring
        docstring = self._get_docstring(node, source_code)

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
            docstring=docstring,
            source_code=self._get_node_text(node, source_code),
        )

    def _extract_class(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract class entity from AST node."""
        name_node = None
        for child in node.children:
            if child.type == "identifier":
                name_node = child
                break

        if not name_node:
            return None

        name = self._get_node_text(name_node, source_code)
        qualified_name = f"{file_path}::{name}"

        # Extract docstring
        docstring = self._get_docstring(node, source_code)

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

    def _extract_inheritance(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        class_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract inheritance relations from class definition."""
        for child in node.children:
            if child.type == "argument_list":
                # Parent classes are in the argument list
                for arg in child.children:
                    if arg.type == "identifier":
                        parent_name = self._get_node_text(arg, source_code)
                        relations.append(Relation(
                            source_id=class_id,
                            target_id=f"unresolved::{parent_name}",
                            type=RelationType.INHERITS,
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
        self._get_node_text(node, source_code)

        # Simple extraction of module name
        if node.type == "import_statement":
            # import module_name
            for child in node.children:
                if child.type == "dotted_name":
                    module_name = self._get_node_text(child, source_code)
                    relations.append(Relation(
                        source_id=parent_id,
                        target_id=f"module::{module_name}",
                        type=RelationType.IMPORTS,
                    ))

        elif node.type == "import_from_statement":
            # from module import name
            module_name = None
            for child in node.children:
                if child.type == "dotted_name":
                    module_name = self._get_node_text(child, source_code)
                    break

            if module_name:
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=f"module::{module_name}",
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
        """Extract function call relations."""
        if node.type == "call":
            # Get function name being called
            func_node = node.children[0] if node.children else None
            if func_node:
                if func_node.type == "identifier":
                    func_name = self._get_node_text(func_node, source_code)
                    relations.append(Relation(
                        source_id=caller_id,
                        target_id=f"unresolved::{func_name}",
                        type=RelationType.CALLS,
                    ))
                elif func_node.type == "attribute":
                    # method call: obj.method()
                    attr_text = self._get_node_text(func_node, source_code)
                    relations.append(Relation(
                        source_id=caller_id,
                        target_id=f"unresolved::{attr_text}",
                        type=RelationType.CALLS,
                    ))

        # Recurse
        for child in node.children:
            self._extract_calls(child, file_path, source_code, caller_id, relations)


# Register the extractor
register_extractor("python", PythonExtractor)
