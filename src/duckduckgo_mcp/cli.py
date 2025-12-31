#!/usr/bin/env python3
"""
Command line interface for DuckDuckGo MCP Server.
This module provides the entry point for the `duckduckgo-mcp` command.
"""

import argparse
import json
import logging
import sys
from typing import Callable, Dict, List

from .duckduckgo_search import duckduckgo_search, search_duckduckgo
from .jina_fetch import fetch_url
from .server import mcp


def _handle_version(args: argparse.Namespace) -> int:
    """Handle the version command."""
    from . import __version__

    print(f"DuckDuckGo MCP Server v{__version__}")

    if not getattr(args, "debug", False):
        return 0

    # Show additional version information in debug mode
    import platform

    print(f"Python version: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")

    try:
        from ddgs import __version__ as ddgs_version

        print(f"ddgs version: {ddgs_version}")
    except ImportError:
        print("ddgs: not available")

    return 0


def _handle_search(args: argparse.Namespace) -> int:
    """Handle the search command."""
    try:
        query = " ".join(args.query)
        results = search_duckduckgo(
            query=query, max_results=args.max_results, safesearch=args.safesearch
        )
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        logging.error(f"Search error: {str(e)}")
        return 1


def _handle_fetch(args: argparse.Namespace) -> int:
    """Handle the fetch command."""
    try:
        result = fetch_url(
            url=args.url,
            output_format=args.format,
            max_length=args.max_length,
            with_images=args.with_images,
        )

        if args.format == "json":
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(result)
        return 0
    except Exception as e:
        logging.error(f"Fetch error: {str(e)}")
        return 1


def _handle_serve(args: argparse.Namespace) -> int:
    """Handle the serve command."""
    from . import __version__

    logging.info(f"Starting DuckDuckGo MCP Server v{__version__} (STDIO transport)")
    logging.info("Press Ctrl+C to stop the server")

    # Register "search" as an alias for "duckduckgo_search" for backward compatibility.
    # Some MCP clients may expect the shorter name. This simply delegates to the main tool.
    @mcp.tool()
    def search(
        query: str, max_results: int = 5, safesearch: str = "moderate"
    ) -> List[Dict[str, str]]:
        """Search DuckDuckGo for the given query."""
        logging.debug(
            f"Searching for: {query} (max_results: {max_results}, safesearch: {safesearch})"
        )
        results = duckduckgo_search(query, max_results, safesearch)
        logging.debug(f"Found {len(results)} results")
        return results

    try:
        mcp.run(transport="stdio")
        return 0
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
        return 0
    except Exception as e:
        logging.error(f"Error running MCP server: {e}")
        return 1


def _setup_parser() -> argparse.ArgumentParser:
    """Set up the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        description="DuckDuckGo MCP Server - Search and content retrieval via MCP protocol"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Serve command
    serve_parser = subparsers.add_parser(
        "serve", help="Start the MCP server over STDIO"
    )
    serve_parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging"
    )

    # Search command
    search_parser = subparsers.add_parser("search", help="Search DuckDuckGo directly")
    search_parser.add_argument("query", nargs="+", help="Search query")
    search_parser.add_argument(
        "--max-results", type=int, default=5, help="Maximum number of results to return"
    )
    search_parser.add_argument(
        "--safesearch",
        choices=["on", "moderate", "off"],
        default="moderate",
        help="Safe search setting (default: moderate)",
    )

    # Fetch command
    fetch_parser = subparsers.add_parser(
        "fetch", help="Fetch and convert content from a URL"
    )
    fetch_parser.add_argument("url", help="URL to fetch content from")
    fetch_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    fetch_parser.add_argument(
        "--max-length", type=int, help="Maximum length of content to return"
    )
    fetch_parser.add_argument(
        "--with-images", action="store_true", help="Generate alt text for images"
    )

    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    version_parser.add_argument(
        "--debug", action="store_true", help="Show detailed version information"
    )

    return parser


def main() -> int:
    """Main entry point for the command line interface."""
    parser = _setup_parser()
    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if getattr(args, "debug", False) else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Command dispatch
    handlers: Dict[str, Callable[[argparse.Namespace], int]] = {
        "version": _handle_version,
        "search": _handle_search,
        "fetch": _handle_fetch,
        "serve": _handle_serve,
    }

    handler = handlers.get(args.command)
    if handler:
        return handler(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
