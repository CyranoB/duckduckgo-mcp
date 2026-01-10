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
    original_error: MCPError,
) -> List[Dict[str, str]]:
    """
    Attempt a fallback search using the brave backend.

    Args:
        query: Search query string
        region: Region code for localized results
        safesearch: Safe search setting
        max_results: Maximum number of results
        timeout: Request timeout in seconds
        original_error: The classified exception that triggered the fallback

    Returns:
        List of formatted search results

    Raises:
        MCPError: If both primary and fallback searches fail, with context about both attempts
    """
    # Don't retry if the error was already about the backend or rate limiting
    # Rate limiting typically affects all backends from the same IP
    if isinstance(original_error, RateLimitError):
        logger.warning(
            f"Skipping fallback search due to rate limiting: {original_error.message}"
        )
        raise original_error

    if "backend" in original_error.message.lower():
        logger.warning("Skipping fallback - original error was backend-specific")
        raise original_error

    logger.info("Primary search failed, retrying with brave backend as fallback")
    try:
        results = _execute_search(
            query, region, safesearch, max_results, timeout, "brave"
        )
        logger.debug(f"Fallback search succeeded with {len(results)} results")
        return results
    except DDGSException as fallback_e:
        fallback_error = _classify_search_error(fallback_e, query, "brave")
        logger.warning(
            f"Fallback search also failed: {fallback_error.message}. "
            f"Original error: {original_error.message}"
        )
        # Raise a combined error with context about both attempts
        raise NetworkError(
            f"Search failed with both backends. "
            f"Primary (duckduckgo): {original_error.message}. "
            f"Fallback (brave): {fallback_error.message}",
            guidance=(
                "Both search backends failed. This could indicate:\n"
                "  • DuckDuckGo may be experiencing widespread issues\n"
                "  • Your network connection may be unstable\n"
                "  • You may be rate limited across backends\n"
                "Please try:\n"
                "  • Waiting a few minutes before trying again\n"
                "  • Checking your internet connection\n"
                "  • Simplifying your search query"
            ),
        ) from fallback_e
    except Exception as fallback_e:
        fallback_error = _classify_search_error(fallback_e, query, "brave")
        logger.error(
            f"Unexpected fallback error: {fallback_error.message}. "
            f"Original error: {original_error.message}"
        )
        raise NetworkError(
            f"Search failed unexpectedly. "
            f"Primary error: {original_error.message}. "
            f"Fallback error: {str(fallback_e)}",
            guidance=(
                "An unexpected error occurred during search. Please:\n"
                "  • Check your internet connection\n"
                "  • Wait a moment and try again\n"
                "  • Try a different search query\n"
                "If the problem persists, DuckDuckGo may be experiencing issues."
            ),
        ) from fallback_e


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
        ValidationError: If query or max_results is invalid
    """
    if not query or not isinstance(query, str):
        raise ValidationError(
            "Search query is required and must be a non-empty string.",
            guidance=(
                "Please provide a valid search query:\n"
                "  • The query must be a text string\n"
                "  • The query cannot be empty\n"
                "Example: 'python web scraping tutorial'"
            ),
        )

    if not isinstance(max_results, int) or max_results <= 0:
        raise ValidationError(
            f"Invalid max_results value: {max_results!r}. Must be a positive integer.",
            guidance=(
                "The max_results parameter must be a positive integer:\n"
                "  • Valid values: 1, 5, 10, 20, etc.\n"
                "  • Default value is 5 if not specified\n"
                "Example: max_results=10"
            ),
        )

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

    Raises:
        MCPError: If search fails with actionable guidance for the user
        ValidationError: If search parameters are invalid
    """
    safesearch = _validate_search_params(query, max_results, safesearch)

    try:
        logger.debug(
            f"Executing search: query='{query}', max_results={max_results}, "
            f"safesearch={safesearch}, region={region}"
        )
        results = _execute_search(
            query, region, safesearch, max_results, timeout, "duckduckgo"
        )
        logger.debug(f"Search completed successfully with {len(results)} results")
        return results
    except DDGSException as e:
        # Classify the error for actionable guidance
        classified_error = _classify_search_error(e, query, "duckduckgo")

        # Log with appropriate level based on error type
        if isinstance(classified_error, RateLimitError):
            logger.warning(f"Rate limited: {classified_error.message}")
        elif isinstance(classified_error, (MCPTimeoutError, NetworkError)):
            logger.warning(f"Network issue: {classified_error.message}")
        else:
            logger.error(f"Search error: {classified_error.message}")

        # Attempt fallback search (will raise if both fail)
        return _try_fallback_search(
            query, region, safesearch, max_results, timeout, classified_error
        )
    except MCPError:
        # Re-raise our custom exceptions as-is
        raise
    except Exception as e:
        # Classify unexpected errors and raise with guidance
        classified_error = _classify_search_error(e, query, "duckduckgo")
        logger.error(f"Unexpected search error: {classified_error.message}")
        raise classified_error from e


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

    Raises:
        ValidationError: If parameters are invalid (invalid query, max_results, or output_format)
        MCPError: If there's a network, service, or rate limiting error during search
    """
    # Validate 'query' parameter
    if not query:
        raise ValidationError(
            "Missing required parameter: query",
            guidance=(
                "The 'query' parameter is required. Please provide a search query.\n"
                "Example: duckduckgo_search(query='python web scraping tutorial')"
            ),
        )

    # Type coercion for MCP clients that may pass strings
    if not isinstance(max_results, int):
        try:
            max_results = int(max_results)
        except (ValueError, TypeError):
            raise ValidationError(
                f"Invalid max_results: '{max_results}'. max_results must be a positive integer.",
                guidance=(
                    "The 'max_results' parameter must be a valid positive integer.\n"
                    "  • Valid values: 1, 5, 10, 20, etc.\n"
                    "  • Default value is 5 if not specified\n"
                    f"You provided: '{max_results}' (type: {type(max_results).__name__})"
                ),
            )

    # Validate max_results range
    if max_results <= 0:
        raise ValidationError(
            f"Invalid max_results: {max_results}. max_results must be a positive integer.",
            guidance=(
                "The 'max_results' parameter must be a positive integer.\n"
                "  • Valid values: 1, 5, 10, 20, etc.\n"
                "  • Default value is 5 if not specified\n"
                f"You provided: {max_results}"
            ),
        )

    # Validate output_format
    output_format = output_format.lower() if output_format else "json"
    if output_format not in ("json", "text"):
        raise ValidationError(
            f"Invalid output_format: '{output_format}'. output_format must be 'json' or 'text'.",
            guidance=(
                "The 'output_format' parameter accepts two values:\n"
                "  • 'json' (default) - Returns results as a list of dictionaries\n"
                "  • 'text' - Returns results as LLM-friendly formatted text\n"
                f"You provided: '{output_format}'"
            ),
        )

    # Log the request at debug level
    logger.debug(
        f"duckduckgo_search called: query={query!r}, max_results={max_results!r}, "
        f"safesearch={safesearch!r}, output_format={output_format!r}"
    )

    try:
        results = search_duckduckgo(query, max_results, safesearch)

        if not results:
            logger.warning(
                f"No results found for query: '{query}' with safesearch={safesearch}, "
                f"max_results={max_results}"
            )
        else:
            logger.debug(
                f"duckduckgo_search successful: {len(results)} results for query '{query}'"
            )

        # Return based on output format
        if output_format == "text":
            return _format_results_as_text(results, query)

        return results

    except MCPError as e:
        # Log the error with appropriate level based on category
        if e.category.value == "network":
            logger.warning(f"Network error searching for '{query}': {e.message}")
        elif e.category.value == "service":
            logger.warning(f"Service error searching for '{query}': {e.message}")
        elif e.category.value == "validation":
            logger.info(f"Validation error for search '{query}': {e.message}")
        else:
            logger.error(f"Error searching for '{query}': {e.message}")
        # Re-raise to propagate the actionable error message
        raise
    except Exception as e:
        # Log unexpected errors at error level with full context
        logger.error(
            f"Unexpected error searching for '{query}' "
            f"(max_results={max_results}, safesearch={safesearch}): {e}"
        )
        raise
