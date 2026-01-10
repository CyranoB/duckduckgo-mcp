#!/usr/bin/env python3
"""
Custom Exception Classes for DuckDuckGo MCP

This module provides custom exception classes with actionable guidance to help users
understand what went wrong and how to fix it.
"""

from enum import Enum
from typing import Optional


class ErrorCategory(Enum):
    """Categories of errors for classification and user guidance."""

    NETWORK = "network"
    SERVICE = "service"
    VALIDATION = "validation"
    CONTENT = "content"
    UNKNOWN = "unknown"


class MCPError(Exception):
    """
    Base exception class for DuckDuckGo MCP errors.

    Provides structured error information including:
    - error_code: A short identifier for the error type
    - category: Classification of the error (network, service, validation, etc.)
    - guidance: Actionable advice for the user to resolve the issue
    """

    error_code: str = "MCP_ERROR"
    category: ErrorCategory = ErrorCategory.UNKNOWN
    default_guidance: str = "Please try again or check your configuration."

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        category: Optional[ErrorCategory] = None,
        guidance: Optional[str] = None,
    ) -> None:
        """
        Initialize the MCPError.

        Args:
            message: Human-readable error message describing what went wrong
            error_code: Optional short identifier for the error type (overrides class default)
            category: Optional error category (overrides class default)
            guidance: Optional actionable guidance (overrides class default)
        """
        self.message = message
        if error_code is not None:
            self.error_code = error_code
        if category is not None:
            self.category = category
        self._guidance = guidance
        super().__init__(message)

    @property
    def guidance(self) -> str:
        """Return the actionable guidance for this error."""
        return self._guidance if self._guidance is not None else self.default_guidance

    def __str__(self) -> str:
        """
        Format the error with category, message, and actionable guidance.

        Returns a user-friendly string that includes:
        - Error category and code
        - The error message
        - Actionable guidance for resolution
        """
        return (
            f"[{self.category.value.upper()}:{self.error_code}] {self.message}\n"
            f"Guidance: {self.guidance}"
        )

    def __repr__(self) -> str:
        """Return a detailed representation of the error."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"category={self.category!r}, "
            f"guidance={self.guidance!r})"
        )


# =============================================================================
# Network-Related Exceptions
# =============================================================================


class NetworkError(MCPError):
    """
    Base exception for network-related errors.

    Raised when there are issues with network connectivity, DNS resolution,
    timeouts, or other network-level problems.
    """

    error_code: str = "NETWORK_ERROR"
    category: ErrorCategory = ErrorCategory.NETWORK
    default_guidance: str = (
        "Check your internet connection and try again. "
        "If the problem persists, the remote server may be temporarily unavailable."
    )


class ConnectionError(NetworkError):
    """
    Exception for connection refused or reset errors.

    Raised when a TCP connection cannot be established because the remote
    server refused the connection or the connection was reset.
    """

    error_code: str = "CONNECTION_ERROR"
    default_guidance: str = (
        "The connection was refused or reset. This could mean:\n"
        "  • The server is not accepting connections\n"
        "  • A firewall is blocking the request\n"
        "  • The server is overloaded\n"
        "Try again in a few moments, or check if the service is available."
    )


class TimeoutError(NetworkError):
    """
    Exception for request timeout errors.

    Raised when a request takes too long to complete and exceeds
    the configured timeout threshold.
    """

    error_code: str = "TIMEOUT_ERROR"
    default_guidance: str = (
        "The request timed out waiting for a response. This could be due to:\n"
        "  • Slow network connection\n"
        "  • Server under heavy load\n"
        "  • Large response size\n"
        "Try again later, or check your network connection."
    )


class DNSError(NetworkError):
    """
    Exception for DNS resolution failures.

    Raised when the hostname cannot be resolved to an IP address,
    indicating either an invalid hostname or DNS configuration issues.
    """

    error_code: str = "DNS_ERROR"
    default_guidance: str = (
        "Could not resolve the hostname. Please check:\n"
        "  • The URL is spelled correctly\n"
        "  • Your DNS settings are working\n"
        "  • The domain exists and is accessible\n"
        "Try using a different DNS server or verify the URL."
    )


# =============================================================================
# Service-Related Exceptions
# =============================================================================


class HTTPError(MCPError):
    """
    Exception for generic HTTP status errors.

    Raised when an HTTP request returns a non-success status code.
    Tracks the status code for more specific error handling.
    """

    error_code: str = "HTTP_ERROR"
    category: ErrorCategory = ErrorCategory.SERVICE
    default_guidance: str = (
        "The server returned an error response. This may be a temporary issue.\n"
        "Try again in a few moments."
    )

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        category: Optional[ErrorCategory] = None,
        guidance: Optional[str] = None,
    ) -> None:
        """
        Initialize the HTTPError.

        Args:
            message: Human-readable error message
            status_code: HTTP status code that caused the error
            error_code: Optional short identifier for the error type
            category: Optional error category
            guidance: Optional actionable guidance
        """
        self.status_code = status_code
        super().__init__(message, error_code, category, guidance)

    def __str__(self) -> str:
        """Format the error with status code, message, and guidance."""
        status_info = f" (HTTP {self.status_code})" if self.status_code else ""
        return (
            f"[{self.category.value.upper()}:{self.error_code}]{status_info} {self.message}\n"
            f"Guidance: {self.guidance}"
        )

    def __repr__(self) -> str:
        """Return a detailed representation of the error."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code!r}, "
            f"error_code={self.error_code!r}, "
            f"category={self.category!r}, "
            f"guidance={self.guidance!r})"
        )


class RateLimitError(HTTPError):
    """
    Exception for rate limiting errors (HTTP 429).

    Raised when too many requests have been made in a short period
    and the service is throttling requests.
    """

    error_code: str = "RATE_LIMIT"
    default_guidance: str = (
        "You've made too many requests in a short period. Please:\n"
        "  • Wait 30-60 seconds before trying again\n"
        "  • Reduce the frequency of your requests\n"
        "  • Consider adding delays between consecutive requests\n"
        "The rate limit typically resets after a brief waiting period."
    )

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        category: Optional[ErrorCategory] = None,
        guidance: Optional[str] = None,
    ) -> None:
        """
        Initialize the RateLimitError.

        Args:
            message: Human-readable error message
            retry_after: Number of seconds to wait before retrying (from Retry-After header)
            status_code: HTTP status code (defaults to 429)
            error_code: Optional short identifier for the error type
            category: Optional error category
            guidance: Optional actionable guidance
        """
        self.retry_after = retry_after
        # Default status code to 429 if not provided
        if status_code is None:
            status_code = 429
        super().__init__(message, status_code, error_code, category, guidance)

    @property
    def guidance(self) -> str:
        """Return guidance with retry timing if available."""
        if self._guidance is not None:
            return self._guidance
        if self.retry_after is not None:
            return (
                f"You've been rate limited. Please wait {self.retry_after} seconds "
                f"before trying again.\n"
                "  • Reduce the frequency of your requests\n"
                "  • Consider adding delays between consecutive requests"
            )
        return self.default_guidance

    def __repr__(self) -> str:
        """Return a detailed representation of the error."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"retry_after={self.retry_after!r}, "
            f"status_code={self.status_code!r}, "
            f"error_code={self.error_code!r}, "
            f"category={self.category!r}, "
            f"guidance={self.guidance!r})"
        )


class ServiceUnavailableError(HTTPError):
    """
    Exception for service unavailable errors (HTTP 503).

    Raised when the external service is temporarily unavailable,
    typically due to maintenance or overload.
    """

    error_code: str = "SERVICE_UNAVAILABLE"
    default_guidance: str = (
        "The service is temporarily unavailable. This usually means:\n"
        "  • The service is undergoing maintenance\n"
        "  • The service is experiencing high load\n"
        "  • There's a temporary outage\n"
        "Please try again in a few minutes. If the problem persists, "
        "check the service's status page."
    )

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        category: Optional[ErrorCategory] = None,
        guidance: Optional[str] = None,
    ) -> None:
        """
        Initialize the ServiceUnavailableError.

        Args:
            message: Human-readable error message
            status_code: HTTP status code (defaults to 503)
            error_code: Optional short identifier for the error type
            category: Optional error category
            guidance: Optional actionable guidance
        """
        # Default status code to 503 if not provided
        if status_code is None:
            status_code = 503
        super().__init__(message, status_code, error_code, category, guidance)
