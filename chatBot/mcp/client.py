"""MCP-to-LangChain adapter.

Convert MCP tool definitions (from tools.py) into LangChain
StructuredTool instances that can be bound to a LangGraph agent.
"""

from langchain_core.tools import StructuredTool

from mcp.tools import (
    calculator,
    get_current_datetime,
    list_notes,
    read_note,
    save_note,
)


def get_mcp_langchain_tools() -> dict[str, StructuredTool]:
    """Return a dict of {tool_name: StructuredTool} for all MCP tools."""
    return {
        "calculator": StructuredTool.from_function(
            name="calculator",
            description="Evaluate a mathematical expression. Supports +, -, *, /, %, **, parentheses, pi, e.",
            func=calculator,
        ),
        "get_current_datetime": StructuredTool.from_function(
            name="get_current_datetime",
            description="Get the current system date and time in the requested format (iso, date, time, unix).",
            func=get_current_datetime,
        ),
        "save_note": StructuredTool.from_function(
            name="save_note",
            description="Save or update a note with a key and content string.",
            func=save_note,
        ),
        "read_note": StructuredTool.from_function(
            name="read_note",
            description="Read a previously saved note by its key.",
            func=read_note,
        ),
        "list_notes": StructuredTool.from_function(
            name="list_notes",
            description="List all saved note keys.",
            func=list_notes,
        ),
    }


def get_mcp_langchain_tools_as_list() -> list[StructuredTool]:
    """Return a flat list of StructuredTool for all MCP tools."""
    return list(get_mcp_langchain_tools().values())
