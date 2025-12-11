"""
Scala Language Extractor

Extracts entities and relations from Scala source files.

Requirements: REQ-AST-012
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


class ScalaExtractor(BaseExtractor):
    """
    Scala-specific entity and relation extractor.

    Extracts:
    - Classes
    - Objects
    - Traits
    - Case classes
    - Functions/Methods
    - Import statements

    Requirements: REQ-AST-012
    """

    config = LanguageConfig(
        name="scala",
        extensions=[".scala", ".sc"],
        tree_sitter_name="scala",
        function_nodes=["function_definition"],
        class_nodes=["class_definition", "object_definition"],
        import_nodes=["import_declaration"],
        interface_nodes=["trait_definition"],
    )

    def extract(
        self,
        tree: Any,
        file_path: Path,
        source_code: str,
    ) -> ParseResult:
        """Extract entities and relations from Scala AST."""
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

        self._current_class: str | None = None
        self._current_class_id: str | None = None

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

        if node.type == "class_definition":
            entity = self._extract_class(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                old_class = self._current_class
                old_class_id = self._current_class_id
                self._current_class = entity.name
                self._current_class_id = entity.id

                for child in node.children:
                    self._walk_tree(
                        child, file_path, source_code,
                        entities, relations, entity.id
                    )

                self._current_class = old_class
                self._current_class_id = old_class_id
                return

        elif node.type == "object_definition":
            entity = self._extract_object(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                for child in node.children:
                    self._walk_tree(
                        child, file_path, source_code,
                        entities, relations, entity.id
                    )
                return

        elif node.type == "trait_definition":
            entity = self._extract_trait(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                return

        elif node.type == "function_definition":
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
                    entity.id, relations
                )

        elif node.type == "import_declaration":
            entity = self._extract_import(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.IMPORTS,
                ))

        # Continue walking children
        for child in node.children:
            self._walk_tree(
                child, file_path, source_code,
                entities, relations, parent_id
            )

    def _extract_class(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract class entity."""
        name_node = None
        is_case_class = False

        for child in node.children:
            if child.type == "identifier":
                name_node = child
            elif child.type == "case":
                is_case_class = True

        if not name_node:
            return None

        name = self._get_node_text(name_node, source_code)

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
            metadata={"scala_type": "case_class" if is_case_class else "class"},
        )

    def _extract_object(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract Scala object (singleton) entity."""
        name_node = None
        for child in node.children:
            if child.type == "identifier":
                name_node = child
                break

        if not name_node:
            return None

        name = self._get_node_text(name_node, source_code)

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
            metadata={"scala_type": "object"},
        )

    def _extract_trait(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract trait entity."""
        name_node = None
        for child in node.children:
            if child.type == "identifier":
                name_node = child
                break

        if not name_node:
            return None

        name = self._get_node_text(name_node, source_code)

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
            metadata={"scala_type": "trait"},
        )

    def _extract_function(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract function/method entity."""
        name_node = None
        for child in node.children:
            if child.type == "identifier":
                name_node = child
                break

        if not name_node:
            return None

        name = self._get_node_text(name_node, source_code)
        qualified_name = (
            f"{file_path}::{self._current_class}::{name}"
            if self._current_class
            else f"{file_path}::{name}"
        )

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
        )

    def _extract_import(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract import statement."""
        import_text = self._get_node_text(node, source_code)
        name = import_text.replace("import ", "").strip()

        if not name:
            return None

        return Entity(
            id=self._generate_entity_id(file_path, f"import_{name}", node.start_point[0] + 1),
            type=EntityType.MODULE,
            name=name,
            qualified_name=name,
            location=Location(
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                start_column=node.start_point[1],
                end_line=node.end_point[0] + 1,
                end_column=node.end_point[1],
            ),
        )

    def _extract_calls(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        caller_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract function calls from a function body."""
        if node.type == "call_expression":
            for child in node.children:
                if child.type == "identifier":
                    callee_name = self._get_node_text(child, source_code)
                    relations.append(Relation(
                        source_id=caller_id,
                        target_id=callee_name,
                        type=RelationType.CALLS,
                    ))
                    break

        for child in node.children:
            self._extract_calls(child, file_path, source_code, caller_id, relations)


# Register the extractor
register_extractor("scala", ScalaExtractor)
