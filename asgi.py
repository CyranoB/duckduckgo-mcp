#!/usr/bin/env python3
"""
ASGI entry point for the DuckDuckGo MCP Server.
This file allows the MCP server to be run with ASGI servers like uvx.
"""

from fastmcp import FastMCP
from duckduckgo_search import mcp, search_duckduckgo

# Export the FastMCP server's HTTP app
app = mcp.http_app()

# The 'app' variable is what uvx will look for and run as an ASGI application