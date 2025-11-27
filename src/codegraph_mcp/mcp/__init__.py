"""
MCP Interface Module

Model Context Protocol interface components:
- Tools: 14 tools for code analysis
- Resources: 4 resource types
- Prompts: 6 prompt templates

Requirements: REQ-TLS-001 ~ REQ-TLS-014, REQ-RSC-001 ~ REQ-RSC-004, REQ-PRM-001 ~ REQ-PRM-006
Design Reference: design-mcp-interface.md
"""

from codegraph_mcp.mcp.prompts import register as register_prompts
from codegraph_mcp.mcp.resources import register as register_resources
from codegraph_mcp.mcp.tools import register as register_tools


__all__ = [
    "register_prompts",
    "register_resources",
    "register_tools",
]
