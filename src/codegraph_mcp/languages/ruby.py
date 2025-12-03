"""
Ruby Language Extractor

Extracts entities and relations from Ruby source files.

Requirements: REQ-AST-009
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


class RubyExtractor(BaseExtractor):
    """
    Ruby-specific entity and relation extractor.

    Extracts:
    - Classes (class)
    - Modules (module)
    - Methods (def)
    - Singleton methods (def self.method)
    - Require statements (require/require_relative)
    - Include/extend statements

    Requirements: REQ-AST-009
    """

    config = LanguageConfig(
        name="ruby",
        extensions=[".rb", ".rake", ".gemspec"],
        tree_sitter_name="ruby",
        function_nodes=["method", "singleton_method"],
        class_nodes=["class"],
        import_nodes=["call"],  # require/require_relative are method calls
        interface_nodes=["module"],
    )

    def extract(
        self,
        tree: Any,
        file_path: Path,
        source_code: str,
    ) -> ParseResult:
        """Extract entities and relations from Ruby AST."""
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

        # Track current class/module scope
        self._scope_stack: list[str] = []

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

        if node.type == "class":
            entity = self._extract_class(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                self._extract_superclass(node, source_code, entity.id, relations)
                # Process class body
                self._scope_stack.append(entity.name)
                self._process_class_body(
                    node, file_path, source_code, entities, relations, entity.id
                )
                self._scope_stack.pop()
            return  # Don't recurse further, handled in process_class_body

        elif node.type == "module":
            entity = self._extract_module(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                # Process module body
                self._scope_stack.append(entity.name)
                self._process_class_body(
                    node, file_path, source_code, entities, relations, entity.id
                )
                self._scope_stack.pop()
            return

        elif node.type == "method":
            entity = self._extract_method(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                self._extract_calls(node, file_path, source_code, entity.id, relations)

        elif node.type == "singleton_method":
            entity = self._extract_singleton_method(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                self._extract_calls(node, file_path, source_code, entity.id, relations)

        elif node.type == "call":
            self._extract_require(node, source_code, parent_id, relations)
            self._extract_include_extend(node, source_code, parent_id, relations)

        # Recurse into children
        for child in node.children:
            self._walk_tree(
                child, file_path, source_code,
                entities, relations, parent_id,
            )

    def _process_class_body(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        entities: list[Entity],
        relations: list[Relation],
        class_id: str,
    ) -> None:
        """Process class/module body contents."""
        for child in node.children:
            if child.type == "body_statement":
                for body_child in child.children:
                    self._walk_tree(
                        body_child, file_path, source_code,
                        entities, relations, class_id,
                    )
            else:
                self._walk_tree(
                    child, file_path, source_code,
                    entities, relations, class_id,
                )

    def _get_qualified_name(self, name: str) -> str:
        """Get qualified name with scope."""
        if self._scope_stack:
            return "::".join(self._scope_stack) + "::" + name
        return name

    def _extract_class(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract class entity."""
        name = None
        for child in node.children:
            if child.type in ("constant", "scope_resolution"):
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

    def _extract_module(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract module entity."""
        name = None
        for child in node.children:
            if child.type in ("constant", "scope_resolution"):
                name = self._get_node_text(child, source_code)
                break

        if not name:
            return None

        qualified_name = f"{file_path}::{self._get_qualified_name(name)}"
        docstring = self._extract_doc_comment(node, source_code)

        return Entity(
            id=self._generate_entity_id(file_path, name, node.start_point[0] + 1),
            type=EntityType.MODULE,
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

        qualified_name = f"{file_path}::{self._get_qualified_name(name)}"
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

    def _extract_singleton_method(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract singleton method (class method) entity."""
        name = None
        for child in node.children:
            if child.type == "identifier":
                name = self._get_node_text(child, source_code)

        if not name:
            return None

        # Prepend self. to indicate class method
        full_name = f"self.{name}"
        qualified_name = f"{file_path}::{self._get_qualified_name(full_name)}"
        signature = self._extract_method_signature(node, full_name, source_code)
        docstring = self._extract_doc_comment(node, source_code)

        return Entity(
            id=self._generate_entity_id(file_path, full_name, node.start_point[0] + 1),
            type=EntityType.METHOD,
            name=full_name,
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

    def _extract_superclass(
        self,
        node: Any,
        source_code: str,
        class_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract inheritance relation."""
        for child in node.children:
            if child.type == "superclass":
                for super_child in child.children:
                    if super_child.type in ("constant", "scope_resolution"):
                        parent_class = self._get_node_text(super_child, source_code)
                        relations.append(Relation(
                            source_id=class_id,
                            target_id=f"unresolved::{parent_class}",
                            type=RelationType.INHERITS,
                        ))
                        break

    def _extract_require(
        self,
        node: Any,
        source_code: str,
        parent_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract require/require_relative statements."""
        method_name = None
        argument = None

        for child in node.children:
            if child.type == "identifier":
                method_name = self._get_node_text(child, source_code)
            elif child.type == "argument_list":
                for arg in child.children:
                    if arg.type == "string":
                        argument = self._get_node_text(arg, source_code)
                        # Remove quotes
                        argument = argument.strip("'\"")
                        break

        if method_name in ("require", "require_relative") and argument:
            relations.append(Relation(
                source_id=parent_id,
                target_id=f"module::{argument}",
                type=RelationType.IMPORTS,
            ))

    def _extract_include_extend(
        self,
        node: Any,
        source_code: str,
        parent_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract include/extend/prepend statements."""
        method_name = None
        modules: list[str] = []

        for child in node.children:
            if child.type == "identifier":
                method_name = self._get_node_text(child, source_code)
            elif child.type == "argument_list":
                for arg in child.children:
                    if arg.type in ("constant", "scope_resolution"):
                        modules.append(self._get_node_text(arg, source_code))

        if method_name in ("include", "extend", "prepend"):
            for mod in modules:
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=f"unresolved::{mod}",
                    type=RelationType.IMPLEMENTS,  # include is like implementing
                ))

    def _extract_calls(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        caller_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract method call relations."""
        if node.type == "call":
            method_name = None
            for child in node.children:
                if child.type == "identifier":
                    method_name = self._get_node_text(child, source_code)
                    break

            if method_name and method_name not in ("require", "require_relative", "include", "extend", "prepend"):
                relations.append(Relation(
                    source_id=caller_id,
                    target_id=f"unresolved::{method_name}",
                    type=RelationType.CALLS,
                ))

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
        params = ""

        for child in node.children:
            if child.type == "method_parameters":
                params = self._get_node_text(child, source_code)
                break

        if params:
            return f"def {name}{params}"
        return f"def {name}"

    def _extract_doc_comment(self, node: Any, source_code: str) -> str | None:
        """Extract YARD-style doc comment."""
        return None


# Register the extractor
register_extractor("ruby", RubyExtractor)
