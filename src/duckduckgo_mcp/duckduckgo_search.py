#!/usr/bin/env python3
"""
DuckDuckGo Search MCP Tool

This tool allows searching the web using DuckDuckGo through the MCP (Model Context Protocol) framework.
It integrates with the ddgs library to provide reliable search results.
"""

import logging
from typing import Dict, List, Union

from ddgs import DDGS
from ddgs.exceptions import DDGSException

from .server import mcp

logger = logging.getLogger(__name__)


def _format_search_result(result: Dict, position: int) -> Dict[str, Union[str, int]]:
    """Transform a raw DuckDuckGo result to the standard format."""
    return {
        "title": result.get("title", ""),
        "url": result.get("href", ""),
        "snippet": result.get("body", ""),
        "position": position,
    }


def _format_results_as_text(results: List[Dict[str, Union[str, int]]], query: str) -> str:
    """
    Format search results as LLM-friendly natural language text.

    Args:
        results: List of search result dictionaries
        query: The original search query (for context in error messages)

    Returns:
        Formatted string with numbered results
    """
    if not results:
        return (
            f"No results found for '{query}'. "
            "This could be due to DuckDuckGo rate limiting, the query returning no matches, "
            "or network issues. Try rephrasing your search or try again in a few minutes."
        )

    lines = [f"Found {len(results)} search results:\n"]

    for position, result in enumerate(results, start=1):
        lines.append(f"{position}. {result.get('title', 'No title')}")
        lines.append(f"   URL: {result.get('url', 'No URL')}")
        lines.append(f"   Summary: {result.get('snippet', 'No summary available')}")
        lines.append("")  # Empty line between results

    return "\n".join(lines)


def _execute_search(
    query: str,
    region: str,
    safesearch: str,
    max_results: int,
    timeout: int,
    backend: str,
) -> List[Dict[str, Union[str, int]]]:
    """
    Execute a search with the specified parameters.

    Args:
        query: Search query string
        region: Region code for localized results
        safesearch: Safe search setting
        max_results: Maximum number of results
        timeout: Request timeout in seconds
        backend: Backend to use ('auto', 'bing', 'brave', 'google', 'mojeek', etc.)

    Returns:
        List of formatted search results
    """
    ddgs = DDGS(timeout=timeout)
    results = ddgs.text(
        query=query,
        region=region,
        safesearch=safesearch,
        max_results=max_results,
        backend=backend,
    )
    return [_format_search_result(r, position) for position, r in enumerate(results, start=1)]


def _try_fallback_search(
    query: str,
    region: str,
    safesearch: str,
    max_results: int,
    timeout: int,
    original_error: Exception,
) -> List[Dict[str, Union[str, int]]]:
    """
    Attempt a fallback search using the brave backend.

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

    logger.info("Retrying with brave backend as fallback")
    try:
        return _execute_search(query, region, safesearch, max_results, timeout, "brave")
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
        logger.warning(
            f"Invalid safesearch value: '{safesearch}'. Using 'moderate' instead."
        )
        return "moderate"

    return safesearch


def search_duckduckgo(
    query: str,
    max_results: int = 5,
    safesearch: str = "moderate",
    region: str = "wt-wt",
    timeout: int = 15,
) -> List[Dict[str, Union[str, int]]]:
    """
    Search DuckDuckGo using the ddgs library and return parsed results.

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

    try:
        return _execute_search(
            query, region, safesearch, max_results, timeout, "duckduckgo"
        )
    except DDGSException as e:
        logger.error(f"DuckDuckGo search error: {str(e)}")
        return _try_fallback_search(query, region, safesearch, max_results, timeout, e)
    except Exception as e:
        logger.error(f"Unexpected error during search: {str(e)}")
        return []


@mcp.tool()
def duckduckgo_search(
    query: str,
    max_results: int = 5,
    safesearch: str = "moderate",
    output_format: str = "json",
) -> Union[List[Dict[str, Union[str, int]]], str]:
    """
    Search the web using DuckDuckGo.

    Args:
        query: The search query
        max_results: Maximum number of search results to return (default: 5)
        safesearch: Safe search setting ('on', 'moderate', 'off'; default: 'moderate')
        output_format: Output format - 'json' returns list of dicts, 'text' returns
                       LLM-friendly formatted string (default: 'json')

    Returns:
        List of search results (json) or formatted string (text)
    """
    # Type coercion for MCP clients that may pass strings
    if not isinstance(max_results, int):
        try:
            max_results = int(max_results)
        except (ValueError, TypeError):
            raise ValueError("max_results must be a valid positive integer")

    # Validate output_format
    output_format = output_format.lower() if output_format else "json"
    if output_format not in ("json", "text"):
        logger.warning(
            f"Invalid output_format: '{output_format}'. Using 'json' instead."
        )
        output_format = "json"

    results = search_duckduckgo(query, max_results, safesearch)

    if not results:
        logger.warning(f"No results found for query: '{query}'")

    # Return based on output format
    if output_format == "text":
        return _format_results_as_text(results, query)

    return results
