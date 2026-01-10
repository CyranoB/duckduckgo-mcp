#!/usr/bin/env python3
"""
Tests for CLI error formatting and display.

This module tests:
- _format_error function for consistent CLI error output
- _classify_server_error function for classifying server startup errors
- Error output in normal vs debug mode
- Integration tests for common error scenarios
"""

import argparse
import sys
from io import StringIO
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from duckduckgo_mcp.cli import (
    _classify_server_error,
    _format_error,
    _handle_fetch,
    _handle_search,
    _handle_serve,
)
from duckduckgo_mcp.exceptions import (
    ConfigurationError,
    DependencyError,
    ErrorCategory,
    HTTPError,
    InvalidURLError,
    MCPError,
    NetworkError,
    PortBindingError,
    RateLimitError,
    ServerStartupError,
    ServiceUnavailableError,
    ValidationError,
)

# =============================================================================
# _format_error Tests - MCPError Formatting
# =============================================================================


class TestFormatErrorMCPError:
    """Tests for _format_error function with MCPError subclasses."""

    # -------------------------------------------------------------------------
    # Basic MCPError Formatting Tests
    # -------------------------------------------------------------------------

    def test_format_error_includes_category_label(self) -> None:
        """Test that formatted error includes category label in header."""
        error = NetworkError("Connection failed")
        result = _format_error(error)

        assert "NETWORK" in result

    def test_format_error_includes_error_code(self) -> None:
        """Test that formatted error includes error code in header."""
        error = NetworkError("Connection failed")
        result = _format_error(error)

        assert "NETWORK_ERROR" in result

    def test_format_error_includes_error_message(self) -> None:
        """Test that formatted error includes the error message."""
        error = NetworkError("Connection failed to remote server")
        result = _format_error(error)

        assert "Connection failed to remote server" in result

    def test_format_error_includes_guidance(self) -> None:
        """Test that formatted error includes actionable guidance."""
        error = NetworkError("Connection failed")
        result = _format_error(error)

        assert "What to do:" in result
        assert "internet connection" in result.lower()

    def test_format_error_header_format(self) -> None:
        """Test that header follows correct format [CATEGORY:ERROR_CODE]."""
        error = RateLimitError("Too many requests")
        result = _format_error(error)

        assert "Error [SERVICE:RATE_LIMIT]" in result

    # -------------------------------------------------------------------------
    # Various MCPError Subclass Tests
    # -------------------------------------------------------------------------

    def test_format_error_validation_error(self) -> None:
        """Test formatting of ValidationError."""
        error = ValidationError("Invalid parameter value")
        result = _format_error(error)

        assert "VALIDATION" in result
        assert "VALIDATION_ERROR" in result
        assert "Invalid parameter value" in result

    def test_format_error_http_error(self) -> None:
        """Test formatting of HTTPError."""
        error = HTTPError("Server error", status_code=500)
        result = _format_error(error)

        assert "SERVICE" in result
        assert "HTTP_ERROR" in result
        assert "Server error" in result

    def test_format_error_rate_limit_error(self) -> None:
        """Test formatting of RateLimitError."""
        error = RateLimitError("Rate limited", retry_after=30)
        result = _format_error(error)

        assert "SERVICE" in result
        assert "RATE_LIMIT" in result
        assert "30" in result

    def test_format_error_invalid_url_error(self) -> None:
        """Test formatting of InvalidURLError."""
        error = InvalidURLError("URL missing scheme", url="example.com")
        result = _format_error(error)

        assert "VALIDATION" in result
        assert "INVALID_URL" in result
        assert "URL missing scheme" in result

    def test_format_error_service_unavailable_error(self) -> None:
        """Test formatting of ServiceUnavailableError."""
        error = ServiceUnavailableError("Service down")
        result = _format_error(error)

        assert "SERVICE" in result
        assert "SERVICE_UNAVAILABLE" in result

    def test_format_error_server_startup_error(self) -> None:
        """Test formatting of ServerStartupError."""
        error = ServerStartupError("Failed to start")
        result = _format_error(error)

        assert "SERVICE" in result
        assert "SERVER_STARTUP_ERROR" in result

    def test_format_error_dependency_error(self) -> None:
        """Test formatting of DependencyError."""
        error = DependencyError("Missing module", package_name="fastmcp")
        result = _format_error(error)

        assert "SERVICE" in result
        assert "DEPENDENCY_ERROR" in result

    def test_format_error_configuration_error(self) -> None:
        """Test formatting of ConfigurationError."""
        error = ConfigurationError("Invalid config")
        result = _format_error(error)

        assert "SERVICE" in result
        assert "CONFIG_ERROR" in result

    def test_format_error_port_binding_error(self) -> None:
        """Test formatting of PortBindingError."""
        error = PortBindingError("Cannot bind", port=8080)
        result = _format_error(error)

        assert "NETWORK" in result
        assert "PORT_BINDING_ERROR" in result

    # -------------------------------------------------------------------------
    # Custom Guidance Tests
    # -------------------------------------------------------------------------

    def test_format_error_custom_guidance(self) -> None:
        """Test that custom guidance is displayed correctly."""
        custom_guidance = "Custom fix: Run pip install missing-package"
        error = MCPError("Generic error", guidance=custom_guidance)
        result = _format_error(error)

        assert "Custom fix" in result
        assert "pip install missing-package" in result

    def test_format_error_multiline_guidance(self) -> None:
        """Test that multiline guidance is indented properly."""
        guidance = "Step 1: Do this\nStep 2: Do that\nStep 3: Finish"
        error = NetworkError("Error", guidance=guidance)
        result = _format_error(error)

        # Each line should be indented
        assert "  Step 1: Do this" in result
        assert "  Step 2: Do that" in result


# =============================================================================
# _format_error Tests - Debug Mode
# =============================================================================


class TestFormatErrorDebugMode:
    """Tests for _format_error function in debug mode."""

    def test_format_error_debug_shows_exception_type(self) -> None:
        """Test that debug mode shows exception type."""
        error = NetworkError("Connection failed")
        result = _format_error(error, debug=True)

        assert "Debug Information:" in result
        assert "Exception type: NetworkError" in result

    def test_format_error_debug_shows_error_code(self) -> None:
        """Test that debug mode shows error code."""
        error = RateLimitError("Too many requests")
        result = _format_error(error, debug=True)

        assert "Error code: RATE_LIMIT" in result

    def test_format_error_debug_shows_category_enum(self) -> None:
        """Test that debug mode shows category enum representation."""
        error = ValidationError("Invalid input")
        result = _format_error(error, debug=True)

        assert "Category:" in result
        assert "VALIDATION" in result

    def test_format_error_debug_includes_stack_trace(self) -> None:
        """Test that debug mode includes stack trace."""
        try:
            raise NetworkError("Test error")
        except NetworkError as e:
            result = _format_error(e, debug=True)

        assert "Stack trace:" in result
        assert "NetworkError" in result

    def test_format_error_debug_includes_file_info(self) -> None:
        """Test that debug mode stack trace includes file info."""
        try:
            raise ValidationError("Test error")
        except ValidationError as e:
            result = _format_error(e, debug=True)

        assert "Stack trace:" in result
        # Stack trace should have file references
        assert ".py" in result or "test_cli_errors" in result

    def test_format_error_normal_mode_no_debug_info(self) -> None:
        """Test that normal mode doesn't show debug information."""
        try:
            raise NetworkError("Test error")
        except NetworkError as e:
            result = _format_error(e, debug=False)

        assert "Debug Information:" not in result
        assert "Stack trace:" not in result
        assert "Exception type:" not in result


# =============================================================================
# _format_error Tests - Generic Exception Formatting
# =============================================================================


class TestFormatErrorGenericException:
    """Tests for _format_error function with non-MCPError exceptions."""

    def test_format_generic_exception_shows_type(self) -> None:
        """Test that generic exception shows error type."""
        error = ValueError("Invalid value")
        result = _format_error(error)

        assert "Error [ValueError]" in result

    def test_format_generic_exception_shows_message(self) -> None:
        """Test that generic exception shows error message."""
        error = RuntimeError("Something went wrong")
        result = _format_error(error)

        assert "Something went wrong" in result

    def test_format_generic_exception_provides_guidance(self) -> None:
        """Test that generic exception provides default guidance."""
        error = Exception("Unknown error")
        result = _format_error(error)

        assert "What to do:" in result
        assert "--debug" in result

    def test_format_generic_exception_empty_message(self) -> None:
        """Test handling of exception with empty message."""
        error = Exception()
        result = _format_error(error)

        assert "unexpected error occurred" in result.lower()

    def test_format_generic_exception_debug_mode(self) -> None:
        """Test generic exception formatting in debug mode."""
        try:
            raise ValueError("Test value error")
        except ValueError as e:
            result = _format_error(e, debug=True)

        assert "Debug Information:" in result
        assert "Exception type: ValueError" in result
        assert "Stack trace:" in result

    def test_format_generic_exception_normal_mode_no_traceback(self) -> None:
        """Test that normal mode doesn't include traceback for generic exceptions."""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            result = _format_error(e, debug=False)

        assert "Stack trace:" not in result

    def test_format_various_builtin_exceptions(self) -> None:
        """Test formatting of various builtin exception types."""
        exceptions = [
            TypeError("Type error"),
            KeyError("key"),
            AttributeError("No attribute"),
            IOError("IO failure"),
        ]

        for error in exceptions:
            result = _format_error(error)
            assert f"Error [{type(error).__name__}]" in result
            assert "What to do:" in result


# =============================================================================
# _classify_server_error Tests
# =============================================================================


class TestClassifyServerError:
    """Tests for the _classify_server_error helper function."""

    # -------------------------------------------------------------------------
    # ImportError / ModuleNotFoundError Tests
    # -------------------------------------------------------------------------

    def test_classify_import_error(self) -> None:
        """Test that ImportError is classified as DependencyError."""
        error = ImportError("No module named 'missing_pkg'")
        result = _classify_server_error(error)

        assert isinstance(result, DependencyError)
        assert result.category == ErrorCategory.SERVICE

    def test_classify_module_not_found_error(self) -> None:
        """Test that ModuleNotFoundError is classified as DependencyError."""
        error = ModuleNotFoundError("No module named 'some_module'")
        result = _classify_server_error(error)

        assert isinstance(result, DependencyError)

    def test_classify_import_error_extracts_package_name(self) -> None:
        """Test that package name is extracted from ImportError."""
        error = ModuleNotFoundError("No module named 'custom_package'")
        result = _classify_server_error(error)

        assert isinstance(result, DependencyError)
        assert result.package_name == "custom_package"

    def test_classify_import_error_fastmcp_provides_specific_guidance(self) -> None:
        """Test that fastmcp ImportError provides specific install guidance."""
        error = ModuleNotFoundError("No module named 'fastmcp'")
        result = _classify_server_error(error)

        assert isinstance(result, DependencyError)
        assert result.package_name == "fastmcp"
        assert "pip install fastmcp" in result.guidance

    def test_classify_import_error_mcp_provides_specific_guidance(self) -> None:
        """Test that mcp ImportError provides specific install guidance."""
        error = ModuleNotFoundError("No module named 'mcp'")
        result = _classify_server_error(error)

        assert isinstance(result, DependencyError)
        assert result.package_name == "mcp"
        assert "pip install fastmcp" in result.guidance

    def test_classify_import_error_ddgs_provides_specific_guidance(self) -> None:
        """Test that ddgs ImportError provides specific install guidance."""
        error = ModuleNotFoundError("No module named 'ddgs'")
        result = _classify_server_error(error)

        assert isinstance(result, DependencyError)
        assert result.package_name == "ddgs"
        assert "pip install ddgs" in result.guidance

    def test_classify_import_error_nested_module(self) -> None:
        """Test that nested module ImportError extracts root package."""
        error = ModuleNotFoundError("No module named 'package.submodule'")
        result = _classify_server_error(error)

        assert isinstance(result, DependencyError)
        assert result.package_name == "package"

    # -------------------------------------------------------------------------
    # OSError / Port Binding Tests
    # -------------------------------------------------------------------------

    def test_classify_address_already_in_use(self) -> None:
        """Test that 'address already in use' OSError is classified as PortBindingError."""
        error = OSError("[Errno 98] Address already in use")
        result = _classify_server_error(error)

        assert isinstance(result, PortBindingError)
        assert result.category == ErrorCategory.NETWORK

    def test_classify_oserror_with_errno_98(self) -> None:
        """Test that OSError with errno 98 is classified as PortBindingError."""
        error = OSError(98, "Address already in use")
        result = _classify_server_error(error)

        assert isinstance(result, PortBindingError)

    def test_classify_oserror_extracts_port(self) -> None:
        """Test that port number is extracted from OSError message."""
        error = OSError("Address already in use: port: 8080")
        result = _classify_server_error(error)

        assert isinstance(result, PortBindingError)
        assert result.port == 8080

    def test_classify_oserror_permission_denied(self) -> None:
        """Test that 'permission denied' OSError provides guidance."""
        error = OSError("[Errno 13] Permission denied")
        error.errno = 13
        result = _classify_server_error(error)

        assert isinstance(result, ServerStartupError)
        assert "permission" in result.guidance.lower()

    # -------------------------------------------------------------------------
    # PermissionError Tests
    # -------------------------------------------------------------------------

    def test_classify_permission_error(self) -> None:
        """Test that PermissionError is classified as ServerStartupError."""
        error = PermissionError("Cannot access file")
        result = _classify_server_error(error)

        assert isinstance(result, ServerStartupError)
        assert "permission" in result.guidance.lower()

    # -------------------------------------------------------------------------
    # AttributeError / TypeError Tests
    # -------------------------------------------------------------------------

    def test_classify_attribute_error(self) -> None:
        """Test that AttributeError is classified as ConfigurationError."""
        error = AttributeError("'NoneType' object has no attribute 'run'")
        result = _classify_server_error(error)

        assert isinstance(result, ConfigurationError)
        assert result.error_code == "CONFIG_ERROR"

    def test_classify_type_error(self) -> None:
        """Test that TypeError is classified as ConfigurationError."""
        error = TypeError("Expected str, got int")
        result = _classify_server_error(error)

        assert isinstance(result, ConfigurationError)

    def test_classify_configuration_error_has_guidance(self) -> None:
        """Test that ConfigurationError provides actionable guidance."""
        error = AttributeError("Invalid config")
        result = _classify_server_error(error)

        assert (
            "configuration" in result.guidance.lower()
            or "config" in result.message.lower()
        )

    # -------------------------------------------------------------------------
    # ValueError Tests
    # -------------------------------------------------------------------------

    def test_classify_value_error(self) -> None:
        """Test that ValueError is classified as ConfigurationError."""
        error = ValueError("Invalid port number")
        result = _classify_server_error(error)

        assert isinstance(result, ConfigurationError)

    def test_classify_value_error_guidance(self) -> None:
        """Test that ValueError ConfigurationError has relevant guidance."""
        error = ValueError("Invalid transport type")
        result = _classify_server_error(error)

        assert isinstance(result, ConfigurationError)
        # Guidance should mention transport or configuration
        assert (
            "transport" in result.guidance.lower()
            or "configuration" in result.message.lower()
        )

    # -------------------------------------------------------------------------
    # RuntimeError Tests
    # -------------------------------------------------------------------------

    def test_classify_runtime_error_event_loop(self) -> None:
        """Test that event loop RuntimeError is classified as ServerStartupError."""
        error = RuntimeError("There is no current event loop")
        result = _classify_server_error(error)

        assert isinstance(result, ServerStartupError)
        assert (
            "event loop" in result.guidance.lower()
            or "async" in result.guidance.lower()
        )

    def test_classify_runtime_error_asyncio(self) -> None:
        """Test that asyncio RuntimeError is classified as ServerStartupError."""
        error = RuntimeError("asyncio cannot run nested")
        result = _classify_server_error(error)

        assert isinstance(result, ServerStartupError)

    def test_classify_generic_runtime_error(self) -> None:
        """Test that generic RuntimeError gets default ServerStartupError."""
        error = RuntimeError("Some other runtime error")
        result = _classify_server_error(error)

        assert isinstance(result, ServerStartupError)

    # -------------------------------------------------------------------------
    # Unknown Exception Tests
    # -------------------------------------------------------------------------

    def test_classify_unknown_exception(self) -> None:
        """Test that unknown exceptions are classified as ServerStartupError."""
        error = Exception("Unknown error occurred")
        result = _classify_server_error(error)

        assert isinstance(result, ServerStartupError)
        assert "--debug" in result.guidance


# =============================================================================
# CLI Handler Error Output Tests
# =============================================================================


class TestHandleSearchErrors:
    """Tests for error handling in _handle_search."""

    def _make_args(
        self,
        query: list[str],
        max_results: int = 5,
        safesearch: str = "moderate",
        output_format: str = "json",
        debug: bool = False,
    ) -> argparse.Namespace:
        """Create argparse.Namespace for search command."""
        return argparse.Namespace(
            query=query,
            max_results=max_results,
            safesearch=safesearch,
            output_format=output_format,
            debug=debug,
        )

    @patch("duckduckgo_mcp.cli.duckduckgo_search")
    def test_handle_search_mcp_error_returns_1(self, mock_search: MagicMock) -> None:
        """Test that MCPError causes return code 1."""
        mock_search.side_effect = RateLimitError("Rate limited")
        args = self._make_args(["test", "query"])

        with patch("sys.stderr", new_callable=StringIO):
            result = _handle_search(args)

        assert result == 1

    @patch("duckduckgo_mcp.cli.duckduckgo_search")
    def test_handle_search_mcp_error_outputs_to_stderr(
        self, mock_search: MagicMock
    ) -> None:
        """Test that MCPError output goes to stderr."""
        mock_search.side_effect = NetworkError("Connection failed")
        args = self._make_args(["test"])

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            _handle_search(args)
            output = mock_stderr.getvalue()

        assert "NETWORK" in output
        assert "Connection failed" in output

    @patch("duckduckgo_mcp.cli.duckduckgo_search")
    def test_handle_search_generic_error_outputs_to_stderr(
        self, mock_search: MagicMock
    ) -> None:
        """Test that generic exception output goes to stderr."""
        mock_search.side_effect = Exception("Unexpected error")
        args = self._make_args(["test"])

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            _handle_search(args)
            output = mock_stderr.getvalue()

        assert "Error" in output
        assert "Unexpected error" in output

    @patch("duckduckgo_mcp.cli.duckduckgo_search")
    def test_handle_search_debug_mode_shows_traceback(
        self, mock_search: MagicMock
    ) -> None:
        """Test that debug mode shows full traceback."""
        mock_search.side_effect = ValidationError("Invalid param")
        args = self._make_args(["test"], debug=True)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            _handle_search(args)
            output = mock_stderr.getvalue()

        assert "Debug Information:" in output
        assert "Stack trace:" in output

    @patch("duckduckgo_mcp.cli.duckduckgo_search")
    def test_handle_search_normal_mode_no_traceback(
        self, mock_search: MagicMock
    ) -> None:
        """Test that normal mode hides traceback."""
        mock_search.side_effect = ValidationError("Invalid param")
        args = self._make_args(["test"], debug=False)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            _handle_search(args)
            output = mock_stderr.getvalue()

        assert "Stack trace:" not in output


class TestHandleFetchErrors:
    """Tests for error handling in _handle_fetch."""

    def _make_args(
        self,
        url: str,
        format: str = "markdown",
        max_length: Optional[int] = None,
        with_images: bool = False,
        debug: bool = False,
    ) -> argparse.Namespace:
        """Create argparse.Namespace for fetch command."""
        return argparse.Namespace(
            url=url,
            format=format,
            max_length=max_length,
            with_images=with_images,
            debug=debug,
        )

    @patch("duckduckgo_mcp.cli.fetch_url")
    def test_handle_fetch_mcp_error_returns_1(self, mock_fetch: MagicMock) -> None:
        """Test that MCPError causes return code 1."""
        mock_fetch.side_effect = InvalidURLError("Invalid URL")
        args = self._make_args("bad-url")

        with patch("sys.stderr", new_callable=StringIO):
            result = _handle_fetch(args)

        assert result == 1

    @patch("duckduckgo_mcp.cli.fetch_url")
    def test_handle_fetch_mcp_error_outputs_to_stderr(
        self, mock_fetch: MagicMock
    ) -> None:
        """Test that MCPError output goes to stderr."""
        mock_fetch.side_effect = InvalidURLError(
            "URL missing scheme", url="example.com"
        )
        args = self._make_args("example.com")

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            _handle_fetch(args)
            output = mock_stderr.getvalue()

        assert "VALIDATION" in output
        assert "INVALID_URL" in output

    @patch("duckduckgo_mcp.cli.fetch_url")
    def test_handle_fetch_network_error_output(self, mock_fetch: MagicMock) -> None:
        """Test network error formatting in fetch command."""
        mock_fetch.side_effect = NetworkError("Connection refused")
        args = self._make_args("https://example.com")

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            _handle_fetch(args)
            output = mock_stderr.getvalue()

        assert "NETWORK" in output
        assert "What to do:" in output

    @patch("duckduckgo_mcp.cli.fetch_url")
    def test_handle_fetch_debug_mode_shows_traceback(
        self, mock_fetch: MagicMock
    ) -> None:
        """Test that debug mode shows full traceback."""
        mock_fetch.side_effect = HTTPError("Server error", status_code=500)
        args = self._make_args("https://example.com", debug=True)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            _handle_fetch(args)
            output = mock_stderr.getvalue()

        assert "Debug Information:" in output
        assert "Stack trace:" in output


class TestHandleServeErrors:
    """Tests for error handling in _handle_serve."""

    def _make_args(self, debug: bool = False) -> argparse.Namespace:
        """Create argparse.Namespace for serve command."""
        return argparse.Namespace(debug=debug)

    @patch("duckduckgo_mcp.cli.mcp")
    def test_handle_serve_import_error_classified(self, mock_mcp: MagicMock) -> None:
        """Test that ImportError is classified and formatted properly."""
        mock_mcp.run.side_effect = ImportError("No module named 'missing'")
        mock_mcp.tool = MagicMock(return_value=lambda f: f)
        args = self._make_args()

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            result = _handle_serve(args)
            output = mock_stderr.getvalue()

        assert result == 1
        assert "DEPENDENCY_ERROR" in output

    @patch("duckduckgo_mcp.cli.mcp")
    def test_handle_serve_oserror_classified(self, mock_mcp: MagicMock) -> None:
        """Test that OSError is classified and formatted properly."""
        mock_mcp.run.side_effect = OSError("[Errno 98] Address already in use")
        mock_mcp.tool = MagicMock(return_value=lambda f: f)
        args = self._make_args()

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            result = _handle_serve(args)
            output = mock_stderr.getvalue()

        assert result == 1
        assert "PORT_BINDING_ERROR" in output or "SERVER_STARTUP_ERROR" in output

    @patch("duckduckgo_mcp.cli.mcp")
    def test_handle_serve_keyboard_interrupt_returns_0(
        self, mock_mcp: MagicMock
    ) -> None:
        """Test that KeyboardInterrupt returns 0 (normal shutdown)."""
        mock_mcp.run.side_effect = KeyboardInterrupt()
        mock_mcp.tool = MagicMock(return_value=lambda f: f)
        args = self._make_args()

        result = _handle_serve(args)

        assert result == 0

    @patch("duckduckgo_mcp.cli.mcp")
    def test_handle_serve_mcp_error_passes_through(self, mock_mcp: MagicMock) -> None:
        """Test that MCPError is formatted directly without classification."""
        mock_mcp.run.side_effect = ConfigurationError("Invalid config")
        mock_mcp.tool = MagicMock(return_value=lambda f: f)
        args = self._make_args()

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            result = _handle_serve(args)
            output = mock_stderr.getvalue()

        assert result == 1
        assert "CONFIG_ERROR" in output


# =============================================================================
# Integration Tests - Error Flow
# =============================================================================


class TestCLIErrorIntegration:
    """Integration tests for CLI error handling flow."""

    def test_format_error_roundtrip_mcp_error(self) -> None:
        """Test complete error formatting flow for MCPError."""
        # Simulate creating and formatting an error
        error = RateLimitError(
            message="Request rate exceeded",
            retry_after=45,
        )

        result = _format_error(error)

        # Should have all components
        assert "SERVICE" in result  # Category
        assert "RATE_LIMIT" in result  # Error code
        assert "Request rate exceeded" in result  # Message
        assert "What to do:" in result  # Guidance header
        assert "45" in result  # Retry time

    def test_format_error_roundtrip_generic_error(self) -> None:
        """Test complete error formatting flow for generic exception."""
        error = ValueError("Some validation failed")

        result = _format_error(error)

        # Should have all components for generic error
        assert "ValueError" in result
        assert "Some validation failed" in result
        assert "What to do:" in result
        assert "--debug" in result

    def test_classify_and_format_server_error(self) -> None:
        """Test classifying and formatting server startup error."""
        original_error = ModuleNotFoundError("No module named 'fastmcp'")

        classified = _classify_server_error(original_error)
        result = _format_error(classified)

        # Should be properly classified
        assert isinstance(classified, DependencyError)
        # Should be properly formatted
        assert "DEPENDENCY_ERROR" in result
        assert "fastmcp" in result
        assert "pip install" in result

    def test_error_format_consistency_across_types(self) -> None:
        """Test that error format is consistent across different error types."""
        errors = [
            NetworkError("Network issue"),
            ValidationError("Invalid input"),
            RateLimitError("Too many requests"),
            ServerStartupError("Failed to start"),
        ]

        for error in errors:
            result = _format_error(error)

            # All should have consistent structure
            assert "Error [" in result  # Header start
            assert "]" in result  # Header end
            assert "What to do:" in result  # Guidance section
            assert error.message in result  # Message included

    def test_debug_info_consistency_across_types(self) -> None:
        """Test that debug info is consistent across error types."""
        errors = [
            NetworkError("Network issue"),
            ValidationError("Invalid input"),
            ValueError("Generic value error"),
        ]

        for error in errors:
            try:
                raise error
            except Exception as e:
                result = _format_error(e, debug=True)

            # All should have debug info
            assert "Debug Information:" in result
            assert "Exception type:" in result
            assert "Stack trace:" in result


# =============================================================================
# Edge Cases and Special Scenarios
# =============================================================================


class TestErrorFormattingEdgeCases:
    """Tests for edge cases in error formatting."""

    def test_empty_guidance(self) -> None:
        """Test handling of error with empty guidance."""
        # Create error with minimal info
        error = MCPError("Test error")
        result = _format_error(error)

        # Should still have What to do section with default guidance
        assert "What to do:" in result

    def test_special_characters_in_message(self) -> None:
        """Test handling of special characters in error message."""
        error = NetworkError("Error: <script>alert('xss')</script> & more")
        result = _format_error(error)

        # Special characters should be preserved (not escaped for CLI)
        assert "<script>" in result
        assert "&" in result

    def test_unicode_in_message(self) -> None:
        """Test handling of unicode characters in error message."""
        error = NetworkError("Error: 日本語 emoji 🚀")
        result = _format_error(error)

        assert "日本語" in result
        assert "🚀" in result

    def test_very_long_message(self) -> None:
        """Test handling of very long error message."""
        long_message = "Error: " + "x" * 1000
        error = NetworkError(long_message)
        result = _format_error(error)

        # Should contain the long message
        assert "x" * 100 in result

    def test_very_long_guidance(self) -> None:
        """Test handling of very long guidance."""
        long_guidance = "Step: " + "y" * 500
        error = MCPError("Error", guidance=long_guidance)
        result = _format_error(error)

        # Should contain the long guidance
        assert "y" * 100 in result

    def test_error_with_none_traceback(self) -> None:
        """Test formatting error that was created without being raised."""
        error = NetworkError("Not raised error")
        # Error.__traceback__ will be None since it wasn't raised
        result = _format_error(error, debug=True)

        # Should still format without crashing
        assert "Debug Information:" in result
        assert "NetworkError" in result

    def test_nested_exception_chain(self) -> None:
        """Test formatting error with exception chain."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise NetworkError("Wrapped error") from e
        except NetworkError as e:
            result = _format_error(e, debug=True)

        # Should include outer exception info
        assert "NetworkError" in result
        assert "Wrapped error" in result
