"""MCP service tool definitions.

Each function implements a standalone MCP-compatible service.
They are wrapped as LangChain tools in client.py and optionally
exposed through a FastMCP server in server.py.
"""

import math
import re
from datetime import datetime, timezone
from typing import Annotated


# Calculator -------------------------------------------------------

def _safe_eval(expression: str) -> str:
    """Evaluate a safe subset of mathematical expressions."""
    allowed = re.compile(r"^[\d\s+\-*/().,%^epi]+$", re.IGNORECASE)
    cleaned = expression.strip().replace("^", "**")
    if not allowed.match(cleaned):
        return "Error: expression contains disallowed characters"
    try:
        ns = {"__builtins__": {}, "math": math, "pi": math.pi, "e": math.e}
        return str(eval(cleaned, ns))
    except Exception as exc:
        return f"Error: {exc}"


def calculator(expression: str) -> str:
    """Evaluate a mathematical expression.
    Supports: +, -, *, /, %, ** (power), parentheses, pi, e."""
    return _safe_eval(expression)


# Date / Time -----------------------------------------------------

def get_current_datetime(format: str = "iso") -> str:
    """Get the current UTC date and time.
    Formats: iso (default), date, time, unix (epoch seconds)."""
    now = datetime.now(timezone.utc)
    if format == "iso":
        return now.isoformat()
    elif format == "date":
        return now.strftime("%Y-%m-%d")
    elif format == "time":
        return now.strftime("%H:%M:%S") + " UTC"
    elif format == "unix":
        return str(now.timestamp())
    return "Unknown format; use iso, date, time, or unix"


# Notes (in-memory) ------------------------------------------------

_notes: dict[str, str] = {}


def save_note(key: str, content: str) -> str:
    """Save or update a note by key."""
    _notes[key.strip()] = content.strip()
    return f"Note '{key}' saved."


def read_note(key: str) -> str:
    """Read a previously saved note by its key."""
    val = _notes.get(key.strip())
    return val if val is not None else f"Note '{key}' not found."


def list_notes() -> str:
    """List all saved note keys."""
    if not _notes:
        return "No notes saved."
    return "\\n".join(f"- {k}" for k in sorted(_notes.keys()))


def get_mcp_tool_schemas():
    """List tool metadata."""
    return [
        {"name": "calculator", "description": calculator.__doc__},
        {"name": "get_current_datetime", "description": get_current_datetime.__doc__},
        {"name": "save_note", "description": save_note.__doc__},
        {"name": "read_note", "description": read_note.__doc__},
        {"name": "list_notes", "description": list_notes.__doc__},
    ]
