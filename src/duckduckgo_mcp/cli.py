#!/usr/bin/env python3
"""
Command line interface for DuckDuckGo MCP Server.
This module provides the entry point for the `duckduckgo-mcp` command.
"""

import json
import sys
import argparse
import logging
from typing import Optional, List, Dict
from .duckduckgo_search import duckduckgo_search, search_duckduckgo, mcp

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
    search_parser.add_argument("query", nargs="+", help="Search query")
    search_parser.add_argument("--max-results", type=int, default=5, 
                              help="Maximum number of results to return")
    search_parser.add_argument("--safesearch", choices=["on", "moderate", "off"],
                              default="moderate", help="Safe search setting (default: moderate)")
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    version_parser.add_argument("--debug", action="store_true", help="Show detailed version information")
    
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
        
        # In debug mode, show additional version information
        if getattr(parsed_args, 'debug', False):
            import platform
            from duckduckgo_search import __version__ as ddgs_version
            print(f"Python version: {platform.python_version()}")
            print(f"Platform: {platform.platform()}")
            print(f"duckduckgo_search version: {ddgs_version}")
        return 0
        
    if parsed_args.command == 'search':
        try:
            # Join query arguments to handle quotes properly
            query = " ".join(parsed_args.query)
            
            # Perform search
            results = search_duckduckgo(
                query=query, 
                max_results=parsed_args.max_results,
                safesearch=parsed_args.safesearch
            )
            print(json.dumps(results, indent=2, ensure_ascii=False))
        except Exception as e:
            logging.error(f"Search error: {str(e)}")
            return 1
        return 0
        
    if parsed_args.command == 'serve':
        # Print version information first
        from . import __version__
        logging.info(f"Starting DuckDuckGo MCP Server v{__version__} (STDIO transport)")
        logging.info("Press Ctrl+C to stop the server")
        
        # Register search tool alias for backward compatibility
        @mcp.tool()
        def search(query: str, max_results: int = 5, safesearch: str = "moderate") -> List[Dict[str, str]]:
            """Search DuckDuckGo for the given query."""
            logging.debug(f"Searching for: {query} (max_results: {max_results}, safesearch: {safesearch})")
            try:
                results = duckduckgo_search(query, max_results, safesearch)
                logging.debug(f"Found {len(results)} results")
                return results
            except Exception as e:
                logging.error(f"Error during search: {e}")
                raise
        
        # Start the MCP server with STDIO transport
        try:
            mcp.run(transport="stdio")
        except KeyboardInterrupt:
            logging.info("Server stopped by user")
        except Exception as e:
            logging.error(f"Error running MCP server: {e}")
            return 1
        
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
