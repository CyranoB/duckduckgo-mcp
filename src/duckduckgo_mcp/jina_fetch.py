#!/usr/bin/env python3
"""
Jina Reader URL Fetcher

This module provides functionality to fetch URLs and convert them to markdown or JSON
using the Jina Reader API. It supports different content types including HTML and PDFs.
"""

import logging
import requests
import json
from typing import Dict, Any, Optional, Union
from urllib.parse import urlparse, quote

from .server import mcp

logger = logging.getLogger(__name__)

# Jina Reader API base URL
JINA_READER_BASE_URL = "https://r.jina.ai/"


def _validate_url(url: str) -> None:
    """
    Validate that the URL is properly formatted and uses HTTP/HTTPS.

    Args:
        url: The URL to validate

    Raises:
        ValueError: If the URL is invalid or uses unsupported scheme
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValueError("Invalid URL format")
    if parsed_url.scheme not in ('http', 'https'):
        raise ValueError("Only HTTP/HTTPS URLs are supported")


def _build_headers(output_format: str, with_images: bool) -> Dict[str, str]:
    """
    Build request headers based on options.

    Args:
        output_format: Desired output format ("markdown" or "json")
        with_images: Whether to include image alt text generation

    Returns:
        Dictionary of HTTP headers
    """
    headers = {"x-no-cache": "true"}

    if output_format.lower() == "json":
        headers["Accept"] = "application/json"
    elif output_format.lower() != "markdown":
        logger.warning(f"Unsupported format: {output_format}. Using markdown as default.")

    if with_images:
        headers["X-With-Generated-Alt"] = "true"

    return headers


def _truncate_content(content: str, max_length: Optional[int]) -> str:
    """Truncate content if it exceeds max_length."""
    if max_length and len(content) > max_length:
        return content[:max_length] + "... (content truncated)"
    return content


def _process_response(
    response: requests.Response,
    output_format: str,
    max_length: Optional[int]
) -> Union[str, Dict[str, Any]]:
    """
    Process the HTTP response based on output format.

    Args:
        response: The HTTP response object
        output_format: Desired output format
        max_length: Maximum content length (None for unlimited)

    Returns:
        Processed content as string or dict
    """
    if output_format.lower() == "json":
        content = response.json()
        if max_length and content.get("content"):
            content["content"] = _truncate_content(content["content"], max_length)
        return content

    # Default is markdown
    return _truncate_content(response.text, max_length)


def fetch_url(
    url: str,
    output_format: str = "markdown",
    max_length: Optional[int] = None,
    with_images: bool = False
) -> Union[str, Dict[str, Any]]:
    """
    Fetch a URL and convert its content using Jina Reader API.

    Args:
        url: The URL to fetch and convert
        output_format: Output format - "markdown" (default) or "json"
        max_length: Maximum content length to return (None for no limit)
        with_images: Whether to include image alt text generation

    Returns:
        The fetched content as markdown string or JSON dict depending on output_format

    Raises:
        ValueError: If the URL is invalid
        RuntimeError: If there is an error fetching or processing the content
    """
    _validate_url(url)
    headers = _build_headers(output_format, with_images)
    jina_url = f"{JINA_READER_BASE_URL}{quote(url)}"

    try:
        logger.debug(f"Fetching URL: {url} via Jina Reader")
        response = requests.get(jina_url, headers=headers, timeout=30)
        response.raise_for_status()
        return _process_response(response, output_format, max_length)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error fetching URL ({url}): {str(e)}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error decoding JSON response: {str(e)}")


@mcp.tool()
def jina_fetch(
    url: str,
    format: str = "markdown",
    max_length: Optional[int] = None,
    with_images: bool = False
) -> Union[str, Dict[str, Any]]:
    """
    Fetch a URL and convert it to markdown or JSON using Jina Reader.

    Args:
        url: The URL to fetch and convert
        format: Output format - "markdown" or "json"
        max_length: Maximum content length to return (None for no limit)
        with_images: Whether to include image alt text generation

    Returns:
        The fetched content in the specified format (markdown string or JSON object)
    """
    if not url:
        raise ValueError("Missing required parameter: url")

    if format and format.lower() not in ["markdown", "json"]:
        raise ValueError("Format must be either 'markdown' or 'json'")

    if max_length is not None:
        try:
            max_length = int(max_length)
            if max_length <= 0:
                raise ValueError("max_length must be a positive integer")
        except (ValueError, TypeError):
            raise ValueError("max_length must be a positive integer")

    return fetch_url(url, output_format=format, max_length=max_length, with_images=with_images)


if __name__ == "__main__":
    # Simple command-line test if run directly
    import sys
    if len(sys.argv) > 1:
        try:
            result = fetch_url(sys.argv[1], output_format="markdown", with_images=True)
            print(result)
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
    else:
        print("Usage: python jina_fetch.py <url>")
        sys.exit(1)
