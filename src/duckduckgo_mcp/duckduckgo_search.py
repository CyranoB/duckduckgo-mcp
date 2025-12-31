#!/usr/bin/env python3
"""
DuckDuckGo Search MCP Tool

This tool allows searching the web using DuckDuckGo through the MCP (Model Context Protocol) framework.
It integrates with the duckduckgo_search library to provide reliable search results.
"""

import json
import logging
import argparse
from typing import Dict, List, Optional
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException

from .server import mcp

logger = logging.getLogger(__name__)


def _format_search_result(result: Dict) -> Dict[str, str]:
    """Transform a raw DuckDuckGo result to the standard format."""
    return {
        'title': result.get('title', ''),
        'url': result.get('href', ''),  # duckduckgo-search uses 'href' for the URL
        'snippet': result.get('body', '')  # duckduckgo-search uses 'body' for snippets
    }


def _select_backend(query: str) -> str:
    """Select the appropriate backend based on query length."""
    return "lite" if len(query) > 100 else "html"


def _execute_search(
    query: str,
    region: str,
    safesearch: str,
    max_results: int,
    timeout: int,
    backend: str
) -> List[Dict[str, str]]:
    """
    Execute a DuckDuckGo search with the specified parameters.

    Args:
        query: Search query string
        region: Region code for localized results
        safesearch: Safe search setting
        max_results: Maximum number of results
        timeout: Request timeout in seconds
        backend: Backend to use ('html' or 'lite')

    Returns:
        List of formatted search results
    """
    ddgs = DDGS(timeout=timeout)
    results = ddgs.text(
        keywords=query,
        region=region,
        safesearch=safesearch,
        max_results=max_results,
        backend=backend
    )
    return [_format_search_result(r) for r in results]


def _try_fallback_search(
    query: str,
    region: str,
    safesearch: str,
    max_results: int,
    timeout: int,
    original_error: Exception
) -> List[Dict[str, str]]:
    """
    Attempt a fallback search using the lite backend.

    Args:
        query: Search query string
        region: Region code for localized results
        safesearch: Safe search setting
        max_results: Maximum number of results
        timeout: Request timeout in seconds
        original_error: The original exception that triggered the fallback

    Returns:
        List of formatted search results, or empty list on failure
    """
    # Don't retry if the error was already about the backend
    if "backend" in str(original_error).lower():
        return []

    logger.info("Retrying with lite backend as fallback")
    try:
        return _execute_search(query, region, safesearch, max_results, timeout, "lite")
    except Exception as e:
        logger.error(f"Fallback search failed: {str(e)}")
        return []


def _validate_search_params(query: str, max_results: int, safesearch: str) -> str:
    """
    Validate search parameters and return normalized safesearch value.

    Args:
        query: Search query string
        max_results: Maximum number of results
        safesearch: Safe search setting

    Returns:
        Normalized safesearch value

    Raises:
        ValueError: If query or max_results is invalid
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")

    if not isinstance(max_results, int) or max_results <= 0:
        raise ValueError("max_results must be a positive integer")

    valid_safesearch = ["on", "moderate", "off"]
    if safesearch not in valid_safesearch:
        logger.warning(f"Invalid safesearch value: '{safesearch}'. Using 'moderate' instead.")
        return "moderate"

    return safesearch


def search_duckduckgo(
    query: str,
    max_results: int = 5,
    safesearch: str = "moderate",
    region: str = "wt-wt",
    timeout: int = 15
) -> List[Dict[str, str]]:
    """
    Search DuckDuckGo using the duckduckgo_search library and return parsed results.

    Args:
        query: The search query string
        max_results: Maximum number of results to return
        safesearch: Safe search setting ('on', 'moderate', 'off')
        region: Region code for localized results (default: wt-wt for no region)
        timeout: Request timeout in seconds

    Returns:
        List of dictionaries containing search results with title, url, and snippet
    """
    safesearch = _validate_search_params(query, max_results, safesearch)
    backend = _select_backend(query)

    try:
        return _execute_search(query, region, safesearch, max_results, timeout, backend)
    except DuckDuckGoSearchException as e:
        logger.error(f"DuckDuckGo search error: {str(e)}")
        return _try_fallback_search(query, region, safesearch, max_results, timeout, e)
    except Exception as e:
        logger.error(f"Unexpected error during search: {str(e)}")
        return []


@mcp.tool()
def duckduckgo_search(
    query: str,
    max_results: int = 5,
    safesearch: str = "moderate"
) -> List[Dict[str, str]]:
    """
    Search the web using DuckDuckGo.

    Args:
        query: The search query
        max_results: Maximum number of search results to return (default: 5)
        safesearch: Safe search setting ('on', 'moderate', 'off'; default: 'moderate')

    Returns:
        List of search results with title, URL, and snippet
    """
    if not query:
        raise ValueError("Missing required parameter: query")

    try:
        if not isinstance(max_results, int):
            max_results = int(max_results)
        if max_results <= 0:
            raise ValueError("max_results must be a positive integer")
    except (ValueError, TypeError):
        raise ValueError("max_results must be a valid positive integer")

    results = search_duckduckgo(query, max_results, safesearch)

    if not results:
        logger.warning(f"No results found for query: '{query}'")

    return results


def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(description="Search DuckDuckGo from the command line")
    parser.add_argument("query", help="The search query", nargs='+')
    parser.add_argument("--max-results", "-n", type=int, default=5,
                        help="Maximum number of results (default: 5)")
    parser.add_argument("--safesearch", choices=["on", "moderate", "off"],
                        default="moderate", help="Safe search setting (default: moderate)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    query = " ".join(args.query)
    results = search_duckduckgo(
        query=query,
        max_results=args.max_results,
        safesearch=args.safesearch
    )

    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
