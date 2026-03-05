#!/usr/bin/env python3
"""
DuckDuckGo News Search MCP Tool

This tool allows searching for recent news using DuckDuckGo through the MCP framework.
It integrates with the ddgs library's news() method to provide time-sorted news results.
"""

import logging
from typing import Any, Dict, List, Union

from ddgs import DDGS
from ddgs.exceptions import DDGSException

from .server import mcp

logger = logging.getLogger(__name__)


def _format_news_result(result: Dict[str, Any]) -> Dict[str, str]:
    """Transform a raw DuckDuckGo news result to the standard format."""
    return {
        "title": result.get("title", ""),
        "url": result.get("url", ""),
        "snippet": result.get("body", ""),
        "date": result.get("date", ""),
        "source": result.get("source", ""),
    }


def _format_news_as_text(results: List[Dict[str, str]], query: str) -> str:
    """Format news results as LLM-friendly natural language text."""
    if not results:
        return (
            f"No news results found for '{query}'. "
            "Try broadening your search terms or check back later."
        )

    lines = [f"Found {len(results)} news results:\n"]

    for position, result in enumerate(results, start=1):
        lines.append(f"{position}. {result.get('title', 'No title')}")
        lines.append(f"   URL: {result.get('url', 'No URL')}")
        lines.append(f"   Date: {result.get('date', 'Unknown')}")
        lines.append(f"   Source: {result.get('source', 'Unknown')}")
        lines.append(f"   Summary: {result.get('snippet', 'No summary available')}")
        lines.append("")

    return "\n".join(lines)


def search_duckduckgo_news(
    query: str,
    max_results: int = 10,
    safesearch: str = "moderate",
    region: str = "wt-wt",
    timeout: int = 30,
) -> List[Dict[str, str]]:
    """
    Search DuckDuckGo news using the ddgs library and return parsed results.

    Args:
        query: The search query string
        max_results: Maximum number of results to return
        safesearch: Safe search setting ('on', 'moderate', 'off')
        region: Region code for localized results (default: wt-wt for no region)
        timeout: Request timeout in seconds

    Returns:
        List of dictionaries containing news results with title, url, snippet,
        date, and source
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
        safesearch = "moderate"

    try:
        ddgs = DDGS(timeout=timeout)
        results = ddgs.news(
            query=query,
            region=region,
            safesearch=safesearch,
            max_results=max_results,
        )
        return [_format_news_result(r) for r in results]
    except DDGSException as e:
        logger.error(f"DuckDuckGo news search error: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error during news search: {str(e)}")
        return []


@mcp.tool()
def duckduckgo_news_search(
    query: str,
    max_results: int = 10,
    safesearch: str = "moderate",
    output_format: str = "json",
) -> Union[List[Dict[str, str]], str]:
    """
    Search DuckDuckGo for recent news articles.

    Returns news results sorted by date, each with title, URL, publication date,
    source outlet, and snippet. Use this instead of regular search when the user
    wants recent news, developments, or time-sensitive information.

    Args:
        query: The news search query
        max_results: Maximum number of news results to return (default: 10)
        safesearch: Safe search setting ('on', 'moderate', 'off'; default: 'moderate')
        output_format: Output format - 'json' returns list of dicts, 'text' returns
                       LLM-friendly formatted string (default: 'json')

    Returns:
        List of news results (json) or formatted string (text)
    """
    if not isinstance(max_results, int):
        try:
            max_results = int(max_results)
        except (ValueError, TypeError):
            raise ValueError("max_results must be a valid positive integer")

    output_format = output_format.lower() if output_format else "json"
    if output_format not in ("json", "text"):
        logger.warning(
            f"Invalid output_format: '{output_format}'. Using 'json' instead."
        )
        output_format = "json"

    results = search_duckduckgo_news(query, max_results, safesearch)

    if not results:
        logger.warning(f"No news results found for query: '{query}'")

    if output_format == "text":
        return _format_news_as_text(results, query)

    return results
