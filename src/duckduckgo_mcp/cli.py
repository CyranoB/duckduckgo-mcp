#!/usr/bin/env python3
"""
Command line interface for DuckDuckGo MCP Server.
This module provides the entry point for the `duckduckgo-mcp` command.
"""

import json
import sys
import argparse
import logging
from typing import Optional, List
from .duckduckgo_search import duckduckgo_search, search_duckduckgo

def main() -> int:
    """Main entry point for the command line interface."""
    parser = argparse.ArgumentParser(
        description="DuckDuckGo MCP Server - Search DuckDuckGo via MCP protocol"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Serve command (STDIO only for first release)
    serve_parser = subparsers.add_parser("serve", help="Start the MCP server over STDIO")
    serve_parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    # Search command (for testing)
    search_parser = subparsers.add_parser("search", help="Search DuckDuckGo directly")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--max-results", type=int, default=5, help="Maximum number of results to return")
    
    # Version command
    subparsers.add_parser("version", help="Show version information")
    
    parsed_args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if getattr(parsed_args, 'debug', False) else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if parsed_args.command == 'version':
        from . import __version__
        print(f"DuckDuckGo MCP Server v{__version__}")
        return 0
        
    if parsed_args.command == 'search':
        results = duckduckgo_search(parsed_args.query, parsed_args.max_results)
        print(json.dumps(results, indent=2))
        return 0
        
    if parsed_args.command == 'serve':
        from fastmcp import FastMCP
        
        mcp = FastMCP(name="duckduckgo_search")
        
        @mcp.tool()
        def search(query: str, max_results: int = 5) -> list:
            """Search DuckDuckGo for the given query."""
            logging.debug(f"Searching for: {query} (max_results: {max_results})")
            try:
                results = duckduckgo_search(query, max_results)
                logging.debug(f"Found {len(results)} results")
                return results
            except Exception as e:
                logging.error(f"Error during search: {e}")
                raise
        
        logging.info("Starting DuckDuckGo MCP Server (STDIO transport)")
        logging.info("Press Ctrl+C to stop the server")
        
        # Start the MCP server with STDIO transport
        mcp.run(transport="stdio")
        print(f"DuckDuckGo MCP Server v{__version__}")
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
