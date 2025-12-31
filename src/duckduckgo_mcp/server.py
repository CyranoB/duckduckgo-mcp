#!/usr/bin/env python3
"""
MCP Server Instance

This module provides the single FastMCP server instance used by all tools.
Centralizing the MCP instance ensures all tools are registered to the same server.
"""

from fastmcp import FastMCP

# Create the single MCP server instance
# All tools should import this instance and use the @mcp.tool() decorator
mcp = FastMCP(name="duckduckgo_mcp")
