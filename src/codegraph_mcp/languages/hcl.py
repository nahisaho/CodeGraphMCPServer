"""
HCL (HashiCorp Configuration Language) Extractor

Extracts entities and relations from HCL/Terraform files.

Requirements: REQ-AST-008
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


class HCLExtractor(BaseExtractor):
    """
    HCL/Terraform-specific entity and relation extractor.

    Extracts:
    - Resources (resource "type" "name")
    - Data sources (data "type" "name")
    - Variables (variable "name")
    - Outputs (output "name")
    - Modules (module "name")
    - Locals (locals)
    - Providers (provider "name")

    Requirements: REQ-AST-008
    """

    config = LanguageConfig(
        name="hcl",
        extensions=[".tf", ".hcl", ".tfvars"],
        tree_sitter_name="hcl",
        function_nodes=[],
        class_nodes=["block"],
        import_nodes=[],
        interface_nodes=[],
    )

    def extract(
        self,
        tree: Any,
        file_path: Path,
        source_code: str,
    ) -> ParseResult:
        """Extract entities and relations from HCL/Terraform AST."""
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

        if node.type == "block":
            entity = self._extract_block(node, file_path, source_code)
            if entity:
                entities.append(entity)
                relations.append(Relation(
                    source_id=parent_id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                ))
                # Extract references within block
                self._extract_references(node, file_path, source_code, entity.id, relations)

        # Recurse into children
        for child in node.children:
            self._walk_tree(
                child, file_path, source_code,
                entities, relations, parent_id,
            )

    def _extract_block(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
    ) -> Entity | None:
        """Extract HCL block entity (resource, data, variable, etc.)."""
        block_type = None
        labels: list[str] = []

        for child in node.children:
            if child.type == "identifier":
                if block_type is None:
                    block_type = self._get_node_text(child, source_code)
            elif child.type == "string_lit":
                label = self._get_node_text(child, source_code)
                # Remove quotes
                label = label.strip('"')
                labels.append(label)

        if not block_type:
            return None

        # Determine entity type and name based on block type
        if block_type == "resource":
            if len(labels) >= 2:
                name = f"{labels[0]}.{labels[1]}"
                entity_type = EntityType.CLASS  # Resources are like classes
            else:
                return None
        elif block_type == "data":
            if len(labels) >= 2:
                name = f"data.{labels[0]}.{labels[1]}"
                entity_type = EntityType.CLASS
            else:
                return None
        elif block_type == "variable":
            if labels:
                name = f"var.{labels[0]}"
                entity_type = EntityType.FUNCTION  # Variables as functions
            else:
                return None
        elif block_type == "output":
            if labels:
                name = f"output.{labels[0]}"
                entity_type = EntityType.FUNCTION
            else:
                return None
        elif block_type == "module":
            if labels:
                name = f"module.{labels[0]}"
                entity_type = EntityType.MODULE
            else:
                return None
        elif block_type == "provider":
            if labels:
                name = f"provider.{labels[0]}"
                entity_type = EntityType.MODULE
            else:
                name = f"provider.{block_type}"
                entity_type = EntityType.MODULE
        elif block_type == "locals":
            name = "locals"
            entity_type = EntityType.MODULE
        elif block_type == "terraform":
            name = "terraform"
            entity_type = EntityType.MODULE
        else:
            # Generic block
            name = f"{block_type}.{'.'.join(labels)}" if labels else block_type
            entity_type = EntityType.CLASS

        qualified_name = f"{file_path}::{name}"

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
            source_code=self._get_node_text(node, source_code),
        )

    def _extract_references(
        self,
        node: Any,
        file_path: Path,
        source_code: str,
        entity_id: str,
        relations: list[Relation],
    ) -> None:
        """Extract references to other resources/variables."""
        # Look for expressions that reference other resources
        if node.type == "expression":
            text = self._get_node_text(node, source_code)

            # Check for resource references (e.g., aws_instance.example)
            if "." in text and not text.startswith('"'):
                # Could be a reference
                parts = text.split(".")
                if len(parts) >= 2:
                    ref_type = parts[0]
                    if ref_type in ("var", "local", "data", "module"):
                        ref_name = f"{ref_type}.{parts[1]}"
                    else:
                        # Likely a resource reference
                        ref_name = f"{parts[0]}.{parts[1]}"

                    relations.append(Relation(
                        source_id=entity_id,
                        target_id=f"unresolved::{ref_name}",
                        type=RelationType.CALLS,
                    ))

        # Recurse
        for child in node.children:
            self._extract_references(child, file_path, source_code, entity_id, relations)

    def _extract_doc_comment(self, node: Any, source_code: str) -> str | None:
        """Extract comment (# or //)."""
        return None


# Register the extractor
register_extractor("hcl", HCLExtractor)
