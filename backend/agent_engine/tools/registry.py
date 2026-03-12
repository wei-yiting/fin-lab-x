"""Central registry for FinLab-X tools."""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Global tool registry
TOOL_REGISTRY: dict[str, Any] = {}


def register_tool(name: str, tool: Any) -> None:
    """Register a tool in the global registry.

    Args:
        name: Unique name for the tool
        tool: LangChain tool object
    """
    TOOL_REGISTRY[name] = tool


def get_tool(name: str) -> Optional[Any]:
    """Get a tool by name from the registry.

    Args:
        name: Tool name to retrieve

    Returns:
        Tool object if found, None otherwise
    """
    return TOOL_REGISTRY.get(name)


def get_tools_by_names(tool_names: list[str]) -> list[Any]:
    """Get multiple tools by their names.

    Args:
        tool_names: List of tool names to retrieve

    Returns:
        List of tool objects (only those found in registry)
    """
    tools = []
    for name in tool_names:
        tool = get_tool(name)
        if tool is not None:
            tools.append(tool)
        else:
            logger.warning("Tool '%s' not found in registry, skipping", name)
    return tools


def list_registered_tools() -> list[str]:
    """List all registered tool names.

    Returns:
        List of tool names in the registry
    """
    return list(TOOL_REGISTRY.keys())


def clear_registry() -> None:
    """Clear all tools from the registry (for testing)."""
    TOOL_REGISTRY.clear()
