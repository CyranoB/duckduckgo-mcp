#!/usr/bin/env python3
"""
Command line interface for DuckDuckGo MCP Server.
This module provides the entry point for the `duckduckgo-mcp` command.
"""

import argparse
import json
import logging
import sys
import traceback
from typing import Callable, Dict, List, Union

from .duckduckgo_search import duckduckgo_search
from .exceptions import MCPError
from .jina_fetch import fetch_url
from .server import mcp


def _format_error(error: Exception, debug: bool = False) -> str:
    """
    Format an error for consistent CLI output.

    Provides user-friendly error display with actionable guidance in normal mode,
    and full details including traceback in debug mode.

    Args:
        error: The exception to format
        debug: If True, include full traceback and technical details

    Returns:
        Formatted error string ready for display to the user
    """
    lines = []

    if isinstance(error, MCPError):
        # For MCPError and subclasses, use the structured information
        category_label = error.category.value.upper()
        error_code = error.error_code

        # Build header with category and error code
        lines.append(f"Error [{category_label}:{error_code}]")
        lines.append("")

        # Add the main error message
        lines.append(f"  {error.message}")
        lines.append("")

        # Add actionable guidance
        lines.append("What to do:")
        # Indent each line of guidance for readability
        for guidance_line in error.guidance.split("\n"):
            lines.append(f"  {guidance_line}")

        if debug:
            lines.append("")
            lines.append("Debug Information:")
            lines.append(f"  Exception type: {type(error).__name__}")
            lines.append(f"  Error code: {error_code}")
            lines.append(f"  Category: {error.category}")
            lines.append("")
            lines.append("Stack trace:")
            # Get the traceback and indent each line
            tb_lines = traceback.format_exception(
                type(error), error, error.__traceback__
            )
            for tb_line in tb_lines:
                for sub_line in tb_line.rstrip().split("\n"):
                    lines.append(f"  {sub_line}")
    else:
        # For non-MCPError exceptions, provide generic formatting
        error_type = type(error).__name__
        error_message = str(error) if str(error) else "An unexpected error occurred"

        lines.append(f"Error [{error_type}]")
        lines.append("")
        lines.append(f"  {error_message}")
        lines.append("")

        if debug:
            lines.append("Debug Information:")
            lines.append(f"  Exception type: {error_type}")
            lines.append("")
            lines.append("Stack trace:")
            tb_lines = traceback.format_exception(
                type(error), error, error.__traceback__
            )
            for tb_line in tb_lines:
                for sub_line in tb_line.rstrip().split("\n"):
                    lines.append(f"  {sub_line}")
        else:
            # In normal mode, provide generic guidance for unexpected errors
            lines.append("What to do:")
            lines.append(
                "  Please try again. If the problem persists, run with --debug"
            )
            lines.append("  for more details, or report this issue.")

    return "\n".join(lines)


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
    debug = getattr(args, "debug", False)
    try:
        query = " ".join(args.query)
        output_format = getattr(args, "output_format", "json")
        results = duckduckgo_search(
            query=query,
            max_results=args.max_results,
            safesearch=args.safesearch,
            output_format=output_format,
        )

        if output_format == "text":
            print(results)
        else:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0
    except MCPError as e:
        # Format and display actionable error message
        print(_format_error(e, debug=debug), file=sys.stderr)
        logging.debug(f"Search MCPError: {type(e).__name__}: {e.message}")
        return 1
    except Exception as e:
        # Handle unexpected errors with generic formatting
        print(_format_error(e, debug=debug), file=sys.stderr)
        logging.error(f"Search error: {str(e)}")
        return 1


def _handle_fetch(args: argparse.Namespace) -> int:
    """Handle the fetch command."""
    debug = getattr(args, "debug", False)
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
    except MCPError as e:
        # Format and display actionable error message
        print(_format_error(e, debug=debug), file=sys.stderr)
        logging.debug(f"Fetch MCPError: {type(e).__name__}: {e.message}")
        return 1
    except Exception as e:
        # Handle unexpected errors with generic formatting
        print(_format_error(e, debug=debug), file=sys.stderr)
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
        query: str,
        max_results: int = 5,
        safesearch: str = "moderate",
        output_format: str = "json",
    ) -> Union[List[Dict[str, str]], str]:
        """Search DuckDuckGo for the given query."""
        logging.debug(
            f"Searching for: {query} (max_results: {max_results}, safesearch: {safesearch}, output_format: {output_format})"
        )
        results = duckduckgo_search(query, max_results, safesearch, output_format)
        if isinstance(results, list):
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
    search_parser.add_argument(
        "--output-format",
        choices=["json", "text"],
        default="json",
        dest="output_format",
        help="Output format: 'json' for structured data, 'text' for LLM-friendly (default: json)",
    )
    search_parser.add_argument(
        "--debug", action="store_true", help="Enable debug output with full traceback"
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
    fetch_parser.add_argument(
        "--debug", action="store_true", help="Enable debug output with full traceback"
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
