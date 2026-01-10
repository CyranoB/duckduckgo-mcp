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
