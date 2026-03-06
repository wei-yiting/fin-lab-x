"""Tests for the central tool registry."""

from backend.agent_engine.tools.registry import (
    ToolRegistry,
    register_tool,
    get_tool,
    get_tools_by_names,
    clear_registry,
)


def test_tool_registry_initialization():
    """Test tool registry can be initialized."""
    registry = ToolRegistry()
    assert registry is not None


def test_register_and_get_tool():
    """Test registering and retrieving a tool."""
    from langchain_core.tools import tool

    clear_registry()

    @tool("test_tool")
    def sample_tool(x: int) -> int:
        """A test tool."""
        return x * 2

    register_tool("test_tool", sample_tool)
    retrieved = get_tool("test_tool")

    assert retrieved is not None
    assert retrieved.name == "test_tool"


def test_get_tools_by_names():
    """Test getting multiple tools by names."""
    from langchain_core.tools import tool

    clear_registry()

    @tool("tool_a")
    def tool_a(x: int) -> int:
        """Tool A for testing."""
        return x

    @tool("tool_b")
    def tool_b(x: int) -> int:
        """Tool B for testing."""
        return x * 2

    register_tool("tool_a", tool_a)
    register_tool("tool_b", tool_b)

    tools = get_tools_by_names(["tool_a", "tool_b"])
    assert len(tools) == 2
