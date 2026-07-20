"""Standalone MCP server runner.

NOTE: The external "mcp" PyPI package shares the same name as our local
"mcp/" directory, which shadows it during normal imports.  All FastMCP
usage is therefore deferred to runtime inside run_mcp_server() to avoid
namespace conflicts at module-import time.

Run this module directly to start an MCP server over SSE:
    python -m mcp.server

By default it listens on 127.0.0.1:8000.
"""

import argparse
import sys
import types


def _get_fastmcp():
    """Resolve the externally-installed ``mcp.server.fastmcp.FastMCP``
    by temporarily hiding our local ``mcp/`` package from ``sys.modules``.

    This allows ``from mcp.server.fastmcp import FastMCP`` to reach the
    real PyPI package rather than our local ``mcp`` directory.
    """
    saved: dict[str, types.ModuleType] = {}
    for key in list(sys.modules):
        if key == "mcp" or key.startswith("mcp."):
            saved[key] = sys.modules.pop(key)
    try:
        from mcp.server.fastmcp import FastMCP as _FastMCP  # type: ignore[import-unmapped]
        return _FastMCP
    finally:
        sys.modules.update(saved)


def run_mcp_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start an MCP server exposing calculator, datetime, and notes tools."""
    FastMCP = _get_fastmcp()

    # Import our tool functions – because tools.py no longer imports
    # from the external ``mcp`` package, this cannot trigger a circular
    # resolution.
    from mcp.tools import (  # noqa: C0415
        calculator,
        get_current_datetime,
        list_notes,
        read_note,
        save_note,
    )

    server = FastMCP("chatbot-mcp")
    server.tool()(calculator)
    server.tool()(get_current_datetime)
    server.tool()(save_note)
    server.tool()(read_note)
    server.tool()(list_notes)

    print(f"Starting MCP server on http://{host}:{port}/sse ...", flush=True)
    server.run(transport="sse", host=host, port=port)


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP Chatbot Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    args = parser.parse_args()
    run_mcp_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
