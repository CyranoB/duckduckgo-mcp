#!/usr/bin/env python3
"""
Web Fetch — URL content retrieval with automatic fallback.

Tries a direct HTTP fetch with trafilatura for content extraction first.
Falls back to the Jina Reader API when direct fetch fails or returns
insufficient content (e.g., JavaScript-rendered pages, bot-blocked sites).
"""

import json
import logging
from typing import Any, Dict, Optional, Union
from urllib.parse import quote, urlparse

import requests
import trafilatura

from .server import mcp

logger = logging.getLogger(__name__)

# Jina Reader API base URL (used as fallback)
JINA_READER_BASE_URL = "https://r.jina.ai/"

# Minimum content length to consider a direct fetch successful.
# Shorter results likely mean the page blocked us or requires JavaScript.
MIN_CONTENT_LENGTH = 100

# User-Agent for direct fetches — identifies as a bot so sites can
# choose to serve simplified content rather than block outright.
DIRECT_USER_AGENT = (
    "Mozilla/5.0 (compatible; WebForager/3.0; "
    "+https://github.com/CyranoB/web-forager)"
)

# Direct fetch timeout — keep it short so we fall back to Jina quickly
# when a site is slow or unresponsive.
DIRECT_FETCH_TIMEOUT = 15

# Jina fetch timeout — Jina can be slower since it renders JavaScript
JINA_FETCH_TIMEOUT = 30


def _validate_url(url: str) -> None:
    """Validate that the URL is properly formatted and uses HTTP/HTTPS."""
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValueError("Invalid URL format")
    if parsed_url.scheme not in ("http", "https"):
        raise ValueError("Only HTTP/HTTPS URLs are supported")


def _truncate_content(content: str, max_length: Optional[int]) -> str:
    """Truncate content if it exceeds max_length."""
    if max_length and len(content) > max_length:
        return content[:max_length] + "... (content truncated)"
    return content


def _direct_fetch(
    url: str,
    output_format: str = "markdown",
    max_length: Optional[int] = None,
    with_images: bool = False,
) -> Optional[Union[str, Dict[str, Any]]]:
    """
    Fetch a URL directly via HTTP and extract content with trafilatura.

    Returns None if the fetch fails or content is too short, signaling
    that the caller should fall back to Jina Reader.
    """
    try:
        logger.debug(f"Attempting direct fetch: {url}")
        response = requests.get(
            url,
            headers={"User-Agent": DIRECT_USER_AGENT},
            timeout=DIRECT_FETCH_TIMEOUT,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.debug(f"Direct fetch failed for {url}: {e}")
        return None

    # Use trafilatura to extract the main content
    content = trafilatura.extract(
        response.text,
        output_format="markdown",
        include_links=True,
        include_tables=True,
        include_formatting=True,
        include_images=with_images,
        url=url,
    )

    if content is None or len(content) < MIN_CONTENT_LENGTH:
        logger.debug(
            f"Direct fetch returned insufficient content for {url} "
            f"({len(content) if content else 0} chars, minimum {MIN_CONTENT_LENGTH})"
        )
        return None

    logger.debug(f"Direct fetch successful for {url} ({len(content)} chars)")

    if output_format.lower() == "json":
        # Extract metadata for JSON format
        metadata = trafilatura.bare_extraction(
            response.text, url=url, with_metadata=True
        )
        title = getattr(metadata, "title", "") or "" if metadata else ""
        return {
            "url": url,
            "title": title,
            "content": _truncate_content(content, max_length),
        }

    return _truncate_content(content, max_length)


def _jina_fetch(
    url: str,
    output_format: str = "markdown",
    max_length: Optional[int] = None,
    with_images: bool = False,
) -> Union[str, Dict[str, Any]]:
    """Fetch a URL using the Jina Reader API."""
    headers = {"x-no-cache": "true"}

    if output_format.lower() == "json":
        headers["Accept"] = "application/json"

    if with_images:
        headers["X-With-Generated-Alt"] = "true"

    jina_url = f"{JINA_READER_BASE_URL}{quote(url)}"

    logger.debug(f"Fetching via Jina Reader: {url}")
    response = requests.get(jina_url, headers=headers, timeout=JINA_FETCH_TIMEOUT)
    response.raise_for_status()

    if output_format.lower() == "json":
        content = response.json()
        if max_length and content.get("content"):
            content["content"] = _truncate_content(content["content"], max_length)
        return content

    return _truncate_content(response.text, max_length)


def fetch_url(
    url: str,
    output_format: str = "markdown",
    max_length: Optional[int] = None,
    with_images: bool = False,
) -> Union[str, Dict[str, Any]]:
    """
    Fetch a URL and convert its content to markdown or JSON.

    Tries a direct HTTP fetch with trafilatura first. If that fails or
    returns insufficient content, falls back to the Jina Reader API.

    Args:
        url: The URL to fetch and convert
        output_format: Output format - "markdown" (default) or "json"
        max_length: Maximum content length to return (None for no limit)
        with_images: Whether to include images in the output

    Returns:
        The fetched content as markdown string or JSON dict

    Raises:
        ValueError: If the URL is invalid
        RuntimeError: If both direct fetch and Jina Reader fail
    """
    _validate_url(url)

    # Try direct fetch first
    result = _direct_fetch(url, output_format, max_length, with_images)
    if result is not None:
        return result

    # Fall back to Jina Reader
    try:
        return _jina_fetch(url, output_format, max_length, with_images)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error fetching URL ({url}): {str(e)}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error decoding JSON response: {str(e)}")


@mcp.tool()
def web_fetch(
    url: str,
    format: str = "markdown",
    max_length: Optional[int] = None,
    with_images: bool = False,
) -> Union[str, Dict[str, Any]]:
    """
    Fetch a URL and convert it to markdown or JSON.

    Tries direct HTTP fetch first for speed. Falls back to Jina Reader
    for JavaScript-heavy or bot-protected pages.

    Args:
        url: The URL to fetch and convert
        format: Output format - "markdown" or "json"
        max_length: Maximum content length to return (None for no limit)
        with_images: Whether to include images in the output

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

    return fetch_url(
        url, output_format=format, max_length=max_length, with_images=with_images
    )


# Backward compatibility alias
jina_fetch = web_fetch
