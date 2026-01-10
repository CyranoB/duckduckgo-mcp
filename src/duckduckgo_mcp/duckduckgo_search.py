#!/usr/bin/env python3
"""
DuckDuckGo Search MCP Tool

This tool allows searching the web using DuckDuckGo through the MCP (Model Context Protocol) framework.
It integrates with the ddgs library to provide reliable search results.
"""

import logging
from typing import Dict, List, Optional, Union

from ddgs import DDGS
from ddgs.exceptions import DDGSException

from .exceptions import MCPError, NetworkError, RateLimitError, ServiceUnavailableError
from .exceptions import TimeoutError as MCPTimeoutError
from .exceptions import ValidationError
from .server import mcp

logger = logging.getLogger(__name__)


def _format_search_result(result: Dict) -> Dict[str, str]:
    """Transform a raw DuckDuckGo result to the standard format."""
    return {
        "title": result.get("title", ""),
        "url": result.get("href", ""),
        "snippet": result.get("body", ""),
    }


def _format_results_as_text(results: List[Dict[str, str]], query: str) -> str:
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


def _classify_search_error(
    error: Exception, query: Optional[str] = None, backend: Optional[str] = None
) -> MCPError:
    """
    Classify a search exception into a specific custom exception type.

    This function analyzes the type and content of a search exception to
    determine the most appropriate custom exception to raise, providing
    users with actionable guidance specific to their error.

    Args:
        error: The exception to classify (typically DDGSException)
        query: Optional search query (for error context)
        backend: Optional backend that was being used (for error context)

    Returns:
        An appropriate MCPError subclass instance with actionable guidance
    """
    error_str = str(error).lower()
    query_context = f" for query: '{query}'" if query else ""
    backend_context = f" using backend '{backend}'" if backend else ""

    # Detect rate limiting errors
    # DuckDuckGo rate limits manifest as various error messages
    rate_limit_indicators = [
        "rate",
        "ratelimit",
        "too many requests",
        "429",
        "blocked",
        "temporarily blocked",
        "please wait",
        "try again later",
        "exceeded",
        "throttle",
    ]
    if any(indicator in error_str for indicator in rate_limit_indicators):
        return RateLimitError(
            f"Rate limited{query_context}. DuckDuckGo has temporarily blocked requests.",
            guidance=(
                "DuckDuckGo has rate limited your requests. To resolve this:\n"
                "  • Wait 30-60 seconds before trying again\n"
                "  • Reduce the frequency of search requests\n"
                "  • Consider adding delays between consecutive searches\n"
                "  • If using automated scripts, implement backoff strategies\n"
                "The rate limit typically resets after a brief waiting period."
            ),
        )

    # Detect timeout errors
    timeout_indicators = ["timeout", "timed out", "time out", "request timeout"]
    if any(indicator in error_str for indicator in timeout_indicators):
        return MCPTimeoutError(
            f"Search timed out{query_context}{backend_context}. "
            "The search took too long to complete.",
            guidance=(
                "The search request timed out. This could be due to:\n"
                "  • Slow network connection\n"
                "  • DuckDuckGo servers under heavy load\n"
                "  • Complex or broad search query\n"
                "Try:\n"
                "  • Simplifying your search query\n"
                "  • Reducing max_results\n"
                "  • Waiting a moment and trying again"
            ),
        )

    # Detect network/connection errors
    network_indicators = [
        "connection",
        "network",
        "connect failed",
        "unable to connect",
        "no internet",
        "dns",
        "resolve",
        "unreachable",
        "refused",
    ]
    if any(indicator in error_str for indicator in network_indicators):
        return NetworkError(
            f"Network error{query_context}. Unable to connect to DuckDuckGo.",
            guidance=(
                "Could not connect to DuckDuckGo. Please check:\n"
                "  • Your internet connection is working\n"
                "  • DuckDuckGo is accessible from your network\n"
                "  • No firewall or proxy is blocking the connection\n"
                "Try again in a few moments."
            ),
        )

    # Detect service unavailable errors
    service_indicators = [
        "503",
        "service unavailable",
        "unavailable",
        "maintenance",
        "temporarily",
        "down",
    ]
    if any(indicator in error_str for indicator in service_indicators):
        return ServiceUnavailableError(
            f"Service unavailable{query_context}. DuckDuckGo is temporarily unavailable.",
            guidance=(
                "DuckDuckGo is temporarily unavailable. This could mean:\n"
                "  • The service is undergoing maintenance\n"
                "  • There's a temporary outage\n"
                "  • The service is experiencing high load\n"
                "Please try again in a few minutes."
            ),
        )

    # Detect backend-specific errors
    backend_indicators = ["backend", "search backend", "api error"]
    if any(indicator in error_str for indicator in backend_indicators):
        return NetworkError(
            f"Search backend error{query_context}{backend_context}.",
            guidance=(
                "The search backend encountered an error. The tool will attempt "
                "to use a fallback backend automatically.\n"
                "If the error persists:\n"
                "  • The query may be too complex\n"
                "  • DuckDuckGo may be experiencing issues\n"
                "  • Try rephrasing your search query"
            ),
        )

    # Detect empty results that might be errors (though these usually aren't exceptions)
    empty_indicators = ["no results", "empty", "nothing found"]
    if any(indicator in error_str for indicator in empty_indicators):
        return NetworkError(
            f"No results returned{query_context}.",
            guidance=(
                "The search returned no results. This could mean:\n"
                "  • The query is too specific or unusual\n"
                "  • DuckDuckGo couldn't find matching content\n"
                "  • There may be a temporary issue\n"
                "Try:\n"
                "  • Rephrasing your search query\n"
                "  • Using broader search terms\n"
                "  • Checking spelling"
            ),
        )

    # Generic search error for any other exception
    return NetworkError(
        f"Search error{query_context}{backend_context}: {str(error)}",
        guidance=(
            "An unexpected search error occurred. Please:\n"
            "  • Check your internet connection\n"
            "  • Try a different search query\n"
            "  • Wait a moment and try again\n"
            "If the problem persists, DuckDuckGo may be experiencing issues."
        ),
    )


def _execute_search(
    query: str,
    region: str,
    safesearch: str,
    max_results: int,
    timeout: int,
    backend: str,
) -> List[Dict[str, str]]:
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
    return [_format_search_result(r) for r in results]


def _try_fallback_search(
    query: str,
    region: str,
    safesearch: str,
    max_results: int,
    timeout: int,
    original_error: Exception,
) -> List[Dict[str, str]]:
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
) -> List[Dict[str, str]]:
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
) -> Union[List[Dict[str, str]], str]:
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
