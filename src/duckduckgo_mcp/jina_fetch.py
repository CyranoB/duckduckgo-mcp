#!/usr/bin/env python3
"""
Jina Reader URL Fetcher

This module provides functionality to fetch URLs and convert them to markdown or JSON
using the Jina Reader API. It supports different content types including HTML and PDFs.
"""

import json
import logging
from typing import Any, Dict, Optional, Union
from urllib.parse import quote, urlparse

import requests

from .exceptions import ConnectionError as MCPConnectionError
from .exceptions import (
    ContentParsingError,
    DNSError,
    HTTPError,
    InvalidURLError,
    MCPError,
    NetworkError,
    RateLimitError,
    ServiceUnavailableError,
)
from .exceptions import TimeoutError as MCPTimeoutError
from .server import mcp

logger = logging.getLogger(__name__)

# Jina Reader API base URL
JINA_READER_BASE_URL = "https://r.jina.ai/"


def _classify_request_error(
    error: requests.exceptions.RequestException, url: Optional[str] = None
) -> MCPError:
    """
    Classify a requests exception into a specific custom exception type.

    This function analyzes the type and content of a requests exception to
    determine the most appropriate custom exception to raise, providing
    users with actionable guidance specific to their error.

    Args:
        error: The requests exception to classify
        url: Optional URL that was being fetched (for error context)

    Returns:
        An appropriate MCPError subclass instance with actionable guidance
    """
    url_context = f" for URL: {url}" if url else ""

    # Handle timeout errors
    if isinstance(error, requests.exceptions.Timeout):
        return MCPTimeoutError(
            f"Request timed out{url_context}. The server took too long to respond."
        )

    # Handle SSL/TLS errors (must be checked before ConnectionError as SSLError inherits from it)
    if isinstance(error, requests.exceptions.SSLError):
        return NetworkError(
            f"SSL/TLS error{url_context}. Could not establish a secure connection.",
            guidance=(
                "There was a problem with the secure connection. This could mean:\n"
                "  • The server's SSL certificate is invalid or expired\n"
                "  • There's a certificate chain issue\n"
                "  • A proxy or firewall is interfering with the connection\n"
                "Verify the URL uses a valid SSL certificate."
            ),
        )

    # Handle connection errors (includes DNS errors)
    if isinstance(error, requests.exceptions.ConnectionError):
        error_str = str(error).lower()
        # Check for DNS resolution failures
        if any(
            indicator in error_str
            for indicator in [
                "nodename nor servname provided",
                "name or service not known",
                "getaddrinfo failed",
                "failed to resolve",
                "dns",
                "temporary failure in name resolution",
            ]
        ):
            return DNSError(
                f"Could not resolve hostname{url_context}. "
                "The domain name could not be found."
            )
        # Generic connection error
        return MCPConnectionError(
            f"Connection failed{url_context}. "
            "Unable to establish a connection to the server."
        )

    # Handle HTTP errors with status codes
    if isinstance(error, requests.exceptions.HTTPError):
        response = error.response
        status_code = response.status_code if response is not None else None

        if status_code == 429:
            # Rate limiting - check for Retry-After header
            retry_after = None
            if response is not None:
                retry_after_header = response.headers.get("Retry-After")
                if retry_after_header:
                    try:
                        retry_after = int(retry_after_header)
                    except ValueError:
                        pass
            return RateLimitError(
                f"Rate limited{url_context}. Too many requests to the service.",
                retry_after=retry_after,
                status_code=status_code,
            )

        if status_code == 503:
            return ServiceUnavailableError(
                f"Service unavailable{url_context}. The server is temporarily unavailable.",
                status_code=status_code,
            )

        if status_code == 404:
            return HTTPError(
                f"Not found{url_context}. The requested resource does not exist.",
                status_code=status_code,
                guidance=(
                    "The URL may be incorrect or the page may have been removed.\n"
                    "  • Verify the URL is correct\n"
                    "  • Check if the page has moved to a new location\n"
                    "  • Ensure the resource still exists"
                ),
            )

        if status_code == 403:
            return HTTPError(
                f"Access forbidden{url_context}. You don't have permission to access this resource.",
                status_code=status_code,
                guidance=(
                    "The server refused to grant access. This could mean:\n"
                    "  • The resource requires authentication\n"
                    "  • Your IP may be blocked\n"
                    "  • The site restricts automated access\n"
                    "Try accessing the URL directly in a browser to verify."
                ),
            )

        if status_code and 500 <= status_code < 600:
            return HTTPError(
                f"Server error{url_context}. The server encountered an internal error.",
                status_code=status_code,
                guidance=(
                    "The server experienced an error while processing the request.\n"
                    "  • Wait a few moments and try again\n"
                    "  • The issue is on the server side, not your request\n"
                    "  • Check if the service has a status page for outage information"
                ),
            )

        # Generic HTTP error
        return HTTPError(
            f"HTTP error{url_context}: {status_code}",
            status_code=status_code,
        )

    # Generic network error for any other RequestException
    return NetworkError(
        f"Network error{url_context}: {str(error)}",
        guidance=(
            "An unexpected network error occurred. Please:\n"
            "  • Check your internet connection\n"
            "  • Verify the URL is correct\n"
            "  • Try again in a few moments"
        ),
    )


def _validate_url(url: str) -> None:
    """
    Validate that the URL is properly formatted and uses HTTP/HTTPS.

    Args:
        url: The URL to validate

    Raises:
        InvalidURLError: If the URL is invalid or uses unsupported scheme
    """
    # Check for empty or non-string URL
    if not url or not isinstance(url, str):
        raise InvalidURLError(
            "URL must be a non-empty string.",
            url=str(url) if url is not None else None,
            guidance=(
                "Please provide a valid URL as a string. For example:\n"
                "  • https://example.com\n"
                "  • https://www.example.com/page"
            ),
        )

    # Strip whitespace and check again
    url_stripped = url.strip()
    if not url_stripped:
        raise InvalidURLError(
            "URL cannot be empty or contain only whitespace.",
            url=url,
            guidance=(
                "Please provide a valid URL. For example:\n"
                "  • https://example.com\n"
                "  • https://www.example.com/page"
            ),
        )

    # Check for spaces in URL (common mistake)
    if " " in url_stripped:
        raise InvalidURLError(
            f"URL contains spaces: '{url_stripped}'",
            url=url_stripped,
            guidance=(
                "URLs cannot contain spaces. If the URL has spaces, try:\n"
                "  • Replacing spaces with %20 (URL encoding)\n"
                "  • Removing the spaces entirely\n"
                "  • Checking if you copied the full URL correctly"
            ),
        )

    parsed_url = urlparse(url_stripped)

    # Check for missing scheme (common mistake: "example.com" instead of "https://example.com")
    if not parsed_url.scheme:
        raise InvalidURLError(
            f"URL is missing the scheme (http:// or https://): '{url_stripped}'",
            url=url_stripped,
            guidance=(
                "URLs must start with http:// or https://. Did you mean:\n"
                f"  • https://{url_stripped}\n"
                "Example valid URLs:\n"
                "  • https://example.com\n"
                "  • http://localhost:8080"
            ),
        )

    # Check for unsupported scheme (e.g., ftp://, file://, mailto:)
    if parsed_url.scheme not in ("http", "https"):
        raise InvalidURLError(
            f"Unsupported URL scheme: '{parsed_url.scheme}'. Only HTTP and HTTPS are supported.",
            url=url_stripped,
            guidance=(
                f"The scheme '{parsed_url.scheme}://' is not supported. Please use:\n"
                "  • https:// (recommended for secure connections)\n"
                "  • http:// (for non-secure connections)\n"
                "Example: https://example.com"
            ),
        )

    # Check for missing domain/netloc (e.g., "https:///path" or "https://")
    if not parsed_url.netloc:
        raise InvalidURLError(
            f"URL is missing the domain name: '{url_stripped}'",
            url=url_stripped,
            guidance=(
                "The URL must include a valid domain name after the scheme. For example:\n"
                "  • https://example.com (domain is 'example.com')\n"
                "  • https://www.example.com/page (domain is 'www.example.com')\n"
                "Make sure the URL follows this format: https://domain.com/path"
            ),
        )


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
        logger.warning(
            f"Unsupported format: {output_format}. Using markdown as default."
        )

    if with_images:
        headers["X-With-Generated-Alt"] = "true"

    return headers


def _truncate_content(content: str, max_length: Optional[int]) -> str:
    """Truncate content if it exceeds max_length."""
    if max_length and len(content) > max_length:
        return content[:max_length] + "... (content truncated)"
    return content


def _process_response(
    response: requests.Response, output_format: str, max_length: Optional[int]
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
    with_images: bool = False,
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
        InvalidURLError: If the URL is invalid (missing scheme, invalid format, etc.)
        MCPError: If there is a network, service, or other error fetching the content.
            Specific subclasses include:
            - TimeoutError: Request timed out
            - ConnectionError: Could not connect to server
            - DNSError: Could not resolve hostname
            - HTTPError: Server returned an error status code
            - RateLimitError: Too many requests (HTTP 429)
            - ServiceUnavailableError: Service temporarily unavailable (HTTP 503)
        ContentParsingError: If the response content cannot be parsed (e.g., invalid JSON)
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
        # Classify the request exception into a specific error type with actionable guidance
        raise _classify_request_error(e, url=url) from e
    except json.JSONDecodeError as e:
        raise ContentParsingError(
            f"Failed to decode JSON response for URL: {url}",
            content_type="json",
            guidance=(
                "The server returned a response that could not be parsed as JSON. "
                "This could mean:\n"
                "  • The URL does not return valid JSON\n"
                "  • The response was truncated or corrupted\n"
                "  • Try using format='markdown' instead of 'json'\n"
                "  • Verify the URL returns the expected content type"
            ),
        ) from e


@mcp.tool()
def jina_fetch(
    url: str,
    format: str = "markdown",
    max_length: Optional[int] = None,
    with_images: bool = False,
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

    return fetch_url(
        url, output_format=format, max_length=max_length, with_images=with_images
    )
