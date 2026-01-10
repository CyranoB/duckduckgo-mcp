#!/usr/bin/env python3
"""
Tests for custom exception classes in DuckDuckGo MCP.

This module tests all exception classes defined in exceptions.py,
including initialization, string formatting, inheritance hierarchy,
and special attributes.
"""

import pytest

from duckduckgo_mcp.exceptions import (
    ConfigurationError,
    ConnectionError,
    ContentParsingError,
    DependencyError,
    DNSError,
    ErrorCategory,
    HTTPError,
    InvalidURLError,
    MCPError,
    NetworkError,
    PortBindingError,
    RateLimitError,
    ServerStartupError,
    ServiceUnavailableError,
    TimeoutError,
    ValidationError,
)

# =============================================================================
# ErrorCategory Enum Tests
# =============================================================================


class TestErrorCategory:
    """Tests for the ErrorCategory enum."""

    def test_category_values(self) -> None:
        """Test that all expected categories exist with correct values."""
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.SERVICE.value == "service"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.CONTENT.value == "content"
        assert ErrorCategory.UNKNOWN.value == "unknown"

    def test_all_categories_present(self) -> None:
        """Test that all expected categories are present."""
        expected = {"NETWORK", "SERVICE", "VALIDATION", "CONTENT", "UNKNOWN"}
        actual = {cat.name for cat in ErrorCategory}
        assert actual == expected


# =============================================================================
# MCPError Base Class Tests
# =============================================================================


class TestMCPError:
    """Tests for the base MCPError class."""

    def test_basic_initialization(self) -> None:
        """Test basic MCPError initialization with message only."""
        error = MCPError("Test error message")
        assert error.message == "Test error message"
        assert error.error_code == "MCP_ERROR"
        assert error.category == ErrorCategory.UNKNOWN
        assert error.guidance == "Please try again or check your configuration."

    def test_initialization_with_all_params(self) -> None:
        """Test MCPError initialization with all parameters."""
        error = MCPError(
            message="Custom message",
            error_code="CUSTOM_CODE",
            category=ErrorCategory.NETWORK,
            guidance="Custom guidance",
        )
        assert error.message == "Custom message"
        assert error.error_code == "CUSTOM_CODE"
        assert error.category == ErrorCategory.NETWORK
        assert error.guidance == "Custom guidance"

    def test_str_format(self) -> None:
        """Test __str__ produces expected format."""
        error = MCPError("Test message")
        result = str(error)
        assert "[UNKNOWN:MCP_ERROR]" in result
        assert "Test message" in result
        assert "Guidance:" in result
        assert "Please try again" in result

    def test_str_format_with_custom_category(self) -> None:
        """Test __str__ with custom category shows correct category."""
        error = MCPError(
            "Test message",
            category=ErrorCategory.NETWORK,
        )
        result = str(error)
        assert "[NETWORK:MCP_ERROR]" in result

    def test_repr_format(self) -> None:
        """Test __repr__ produces detailed representation."""
        error = MCPError("Test message")
        result = repr(error)
        assert "MCPError(" in result
        assert "message='Test message'" in result
        assert "error_code='MCP_ERROR'" in result
        assert "category=<ErrorCategory.UNKNOWN:" in result
        assert "guidance=" in result

    def test_inherits_from_exception(self) -> None:
        """Test MCPError inherits from Exception."""
        error = MCPError("Test")
        assert isinstance(error, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        """Test MCPError can be raised and caught."""
        with pytest.raises(MCPError) as exc_info:
            raise MCPError("Test error")
        assert exc_info.value.message == "Test error"


# =============================================================================
# Network-Related Exception Tests
# =============================================================================


class TestNetworkError:
    """Tests for NetworkError and its subclasses."""

    def test_basic_initialization(self) -> None:
        """Test NetworkError basic initialization."""
        error = NetworkError("Network issue occurred")
        assert error.message == "Network issue occurred"
        assert error.error_code == "NETWORK_ERROR"
        assert error.category == ErrorCategory.NETWORK
        assert "internet connection" in error.guidance

    def test_inherits_from_mcp_error(self) -> None:
        """Test NetworkError inherits from MCPError."""
        error = NetworkError("Test")
        assert isinstance(error, MCPError)
        assert isinstance(error, Exception)


class TestConnectionError:
    """Tests for ConnectionError class."""

    def test_basic_initialization(self) -> None:
        """Test ConnectionError basic initialization."""
        error = ConnectionError("Connection refused")
        assert error.message == "Connection refused"
        assert error.error_code == "CONNECTION_ERROR"
        assert error.category == ErrorCategory.NETWORK
        assert "connection was refused" in error.guidance

    def test_inherits_from_network_error(self) -> None:
        """Test ConnectionError inherits from NetworkError."""
        error = ConnectionError("Test")
        assert isinstance(error, NetworkError)
        assert isinstance(error, MCPError)

    def test_str_format(self) -> None:
        """Test __str__ format shows network category."""
        error = ConnectionError("Connection reset by peer")
        result = str(error)
        assert "[NETWORK:CONNECTION_ERROR]" in result
        assert "Connection reset by peer" in result


class TestTimeoutError:
    """Tests for TimeoutError class."""

    def test_basic_initialization(self) -> None:
        """Test TimeoutError basic initialization."""
        error = TimeoutError("Request timed out")
        assert error.message == "Request timed out"
        assert error.error_code == "TIMEOUT_ERROR"
        assert error.category == ErrorCategory.NETWORK
        assert "timed out" in error.guidance

    def test_inherits_from_network_error(self) -> None:
        """Test TimeoutError inherits from NetworkError."""
        error = TimeoutError("Test")
        assert isinstance(error, NetworkError)
        assert isinstance(error, MCPError)

    def test_custom_guidance(self) -> None:
        """Test custom guidance overrides default."""
        error = TimeoutError("Timeout", guidance="Try waiting longer")
        assert error.guidance == "Try waiting longer"


class TestDNSError:
    """Tests for DNSError class."""

    def test_basic_initialization(self) -> None:
        """Test DNSError basic initialization."""
        error = DNSError("Could not resolve hostname")
        assert error.message == "Could not resolve hostname"
        assert error.error_code == "DNS_ERROR"
        assert error.category == ErrorCategory.NETWORK
        assert "resolve the hostname" in error.guidance

    def test_inherits_from_network_error(self) -> None:
        """Test DNSError inherits from NetworkError."""
        error = DNSError("Test")
        assert isinstance(error, NetworkError)
        assert isinstance(error, MCPError)


# =============================================================================
# Service-Related Exception Tests
# =============================================================================


class TestHTTPError:
    """Tests for HTTPError class."""

    def test_basic_initialization(self) -> None:
        """Test HTTPError basic initialization."""
        error = HTTPError("Server error occurred")
        assert error.message == "Server error occurred"
        assert error.error_code == "HTTP_ERROR"
        assert error.category == ErrorCategory.SERVICE
        assert error.status_code is None

    def test_initialization_with_status_code(self) -> None:
        """Test HTTPError initialization with status code."""
        error = HTTPError("Not Found", status_code=404)
        assert error.status_code == 404
        assert error.message == "Not Found"

    def test_str_format_with_status_code(self) -> None:
        """Test __str__ includes status code when provided."""
        error = HTTPError("Not Found", status_code=404)
        result = str(error)
        assert "[SERVICE:HTTP_ERROR]" in result
        assert "(HTTP 404)" in result
        assert "Not Found" in result

    def test_str_format_without_status_code(self) -> None:
        """Test __str__ format without status code."""
        error = HTTPError("Server error")
        result = str(error)
        assert "[SERVICE:HTTP_ERROR]" in result
        assert "(HTTP" not in result

    def test_repr_includes_status_code(self) -> None:
        """Test __repr__ includes status_code."""
        error = HTTPError("Error", status_code=500)
        result = repr(error)
        assert "HTTPError(" in result
        assert "status_code=500" in result

    def test_inherits_from_mcp_error(self) -> None:
        """Test HTTPError inherits from MCPError."""
        error = HTTPError("Test")
        assert isinstance(error, MCPError)


class TestRateLimitError:
    """Tests for RateLimitError class."""

    def test_basic_initialization(self) -> None:
        """Test RateLimitError basic initialization."""
        error = RateLimitError("Too many requests")
        assert error.message == "Too many requests"
        assert error.error_code == "RATE_LIMIT"
        assert error.category == ErrorCategory.SERVICE
        assert error.status_code == 429  # Default
        assert error.retry_after is None

    def test_initialization_with_retry_after(self) -> None:
        """Test RateLimitError with retry_after parameter."""
        error = RateLimitError("Rate limited", retry_after=60)
        assert error.retry_after == 60
        assert "wait 60 seconds" in error.guidance

    def test_guidance_with_retry_after(self) -> None:
        """Test guidance includes retry timing."""
        error = RateLimitError("Rate limited", retry_after=30)
        assert "wait 30 seconds" in error.guidance
        assert "Reduce the frequency" in error.guidance

    def test_guidance_without_retry_after(self) -> None:
        """Test default guidance when no retry_after."""
        error = RateLimitError("Rate limited")
        assert "30-60 seconds" in error.guidance

    def test_custom_status_code(self) -> None:
        """Test custom status code overrides default."""
        error = RateLimitError("Rate limited", status_code=503)
        assert error.status_code == 503

    def test_inherits_from_http_error(self) -> None:
        """Test RateLimitError inherits from HTTPError."""
        error = RateLimitError("Test")
        assert isinstance(error, HTTPError)
        assert isinstance(error, MCPError)

    def test_repr_includes_retry_after(self) -> None:
        """Test __repr__ includes retry_after."""
        error = RateLimitError("Error", retry_after=60)
        result = repr(error)
        assert "RateLimitError(" in result
        assert "retry_after=60" in result


class TestServiceUnavailableError:
    """Tests for ServiceUnavailableError class."""

    def test_basic_initialization(self) -> None:
        """Test ServiceUnavailableError basic initialization."""
        error = ServiceUnavailableError("Service down")
        assert error.message == "Service down"
        assert error.error_code == "SERVICE_UNAVAILABLE"
        assert error.category == ErrorCategory.SERVICE
        assert error.status_code == 503  # Default
        assert "temporarily unavailable" in error.guidance

    def test_custom_status_code(self) -> None:
        """Test custom status code overrides default."""
        error = ServiceUnavailableError("Service down", status_code=502)
        assert error.status_code == 502

    def test_inherits_from_http_error(self) -> None:
        """Test ServiceUnavailableError inherits from HTTPError."""
        error = ServiceUnavailableError("Test")
        assert isinstance(error, HTTPError)
        assert isinstance(error, MCPError)


# =============================================================================
# Validation-Related Exception Tests
# =============================================================================


class TestValidationError:
    """Tests for ValidationError class."""

    def test_basic_initialization(self) -> None:
        """Test ValidationError basic initialization."""
        error = ValidationError("Invalid input")
        assert error.message == "Invalid input"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.category == ErrorCategory.VALIDATION
        assert "invalid" in error.guidance.lower()

    def test_inherits_from_mcp_error(self) -> None:
        """Test ValidationError inherits from MCPError."""
        error = ValidationError("Test")
        assert isinstance(error, MCPError)

    def test_str_format(self) -> None:
        """Test __str__ format shows validation category."""
        error = ValidationError("Missing required field")
        result = str(error)
        assert "[VALIDATION:VALIDATION_ERROR]" in result
        assert "Missing required field" in result


class TestInvalidURLError:
    """Tests for InvalidURLError class."""

    def test_basic_initialization(self) -> None:
        """Test InvalidURLError basic initialization."""
        error = InvalidURLError("URL is malformed")
        assert error.message == "URL is malformed"
        assert error.error_code == "INVALID_URL"
        assert error.category == ErrorCategory.VALIDATION
        assert error.url is None
        assert "http://" in error.guidance
        assert "https://" in error.guidance

    def test_initialization_with_url(self) -> None:
        """Test InvalidURLError with url parameter."""
        error = InvalidURLError("Invalid URL", url="not-a-url")
        assert error.url == "not-a-url"

    def test_inherits_from_validation_error(self) -> None:
        """Test InvalidURLError inherits from ValidationError."""
        error = InvalidURLError("Test")
        assert isinstance(error, ValidationError)
        assert isinstance(error, MCPError)

    def test_repr_includes_url(self) -> None:
        """Test __repr__ includes url."""
        error = InvalidURLError("Invalid", url="bad-url")
        result = repr(error)
        assert "InvalidURLError(" in result
        assert "url='bad-url'" in result

    def test_guidance_includes_examples(self) -> None:
        """Test guidance includes valid URL examples."""
        error = InvalidURLError("Bad URL")
        assert "example.com" in error.guidance


# =============================================================================
# Content-Related Exception Tests
# =============================================================================


class TestContentParsingError:
    """Tests for ContentParsingError class."""

    def test_basic_initialization(self) -> None:
        """Test ContentParsingError basic initialization."""
        error = ContentParsingError("Failed to parse response")
        assert error.message == "Failed to parse response"
        assert error.error_code == "CONTENT_PARSE_ERROR"
        assert error.category == ErrorCategory.CONTENT
        assert error.content_type is None
        assert "parse" in error.guidance.lower()

    def test_initialization_with_content_type(self) -> None:
        """Test ContentParsingError with content_type parameter."""
        error = ContentParsingError("JSON parse error", content_type="json")
        assert error.content_type == "json"

    def test_inherits_from_mcp_error(self) -> None:
        """Test ContentParsingError inherits from MCPError."""
        error = ContentParsingError("Test")
        assert isinstance(error, MCPError)

    def test_repr_includes_content_type(self) -> None:
        """Test __repr__ includes content_type."""
        error = ContentParsingError("Parse error", content_type="xml")
        result = repr(error)
        assert "ContentParsingError(" in result
        assert "content_type='xml'" in result

    def test_str_format(self) -> None:
        """Test __str__ format shows content category."""
        error = ContentParsingError("Parse failed")
        result = str(error)
        assert "[CONTENT:CONTENT_PARSE_ERROR]" in result
        assert "Parse failed" in result


# =============================================================================
# Server-Related Exception Tests
# =============================================================================


class TestServerStartupError:
    """Tests for ServerStartupError class."""

    def test_basic_initialization(self) -> None:
        """Test ServerStartupError basic initialization."""
        error = ServerStartupError("Server failed to start")
        assert error.message == "Server failed to start"
        assert error.error_code == "SERVER_STARTUP_ERROR"
        assert error.category == ErrorCategory.SERVICE
        assert "server failed to start" in error.guidance.lower()

    def test_inherits_from_mcp_error(self) -> None:
        """Test ServerStartupError inherits from MCPError."""
        error = ServerStartupError("Test")
        assert isinstance(error, MCPError)


class TestDependencyError:
    """Tests for DependencyError class."""

    def test_basic_initialization(self) -> None:
        """Test DependencyError basic initialization."""
        error = DependencyError("Missing package")
        assert error.message == "Missing package"
        assert error.error_code == "DEPENDENCY_ERROR"
        assert error.category == ErrorCategory.SERVICE
        assert error.package_name is None
        assert "pip install" in error.guidance

    def test_initialization_with_package_name(self) -> None:
        """Test DependencyError with package_name parameter."""
        error = DependencyError("Missing requests", package_name="requests")
        assert error.package_name == "requests"

    def test_inherits_from_server_startup_error(self) -> None:
        """Test DependencyError inherits from ServerStartupError."""
        error = DependencyError("Test")
        assert isinstance(error, ServerStartupError)
        assert isinstance(error, MCPError)

    def test_repr_includes_package_name(self) -> None:
        """Test __repr__ includes package_name."""
        error = DependencyError("Missing", package_name="fastmcp")
        result = repr(error)
        assert "DependencyError(" in result
        assert "package_name='fastmcp'" in result


class TestConfigurationError:
    """Tests for ConfigurationError class."""

    def test_basic_initialization(self) -> None:
        """Test ConfigurationError basic initialization."""
        error = ConfigurationError("Invalid config")
        assert error.message == "Invalid config"
        assert error.error_code == "CONFIG_ERROR"
        assert error.category == ErrorCategory.SERVICE
        assert "configuration" in error.guidance.lower()

    def test_inherits_from_server_startup_error(self) -> None:
        """Test ConfigurationError inherits from ServerStartupError."""
        error = ConfigurationError("Test")
        assert isinstance(error, ServerStartupError)
        assert isinstance(error, MCPError)


class TestPortBindingError:
    """Tests for PortBindingError class."""

    def test_basic_initialization(self) -> None:
        """Test PortBindingError basic initialization."""
        error = PortBindingError("Cannot bind to port")
        assert error.message == "Cannot bind to port"
        assert error.error_code == "PORT_BINDING_ERROR"
        assert error.category == ErrorCategory.NETWORK
        assert error.port is None
        assert "bind" in error.guidance.lower()

    def test_initialization_with_port(self) -> None:
        """Test PortBindingError with port parameter."""
        error = PortBindingError("Port in use", port=8080)
        assert error.port == 8080

    def test_guidance_with_port(self) -> None:
        """Test guidance includes port-specific information."""
        error = PortBindingError("Port in use", port=8080)
        assert "8080" in error.guidance
        assert "lsof -i :8080" in error.guidance

    def test_guidance_without_port(self) -> None:
        """Test default guidance without port."""
        error = PortBindingError("Port in use")
        assert "lsof -i :<port>" in error.guidance

    def test_custom_guidance_overrides_port_guidance(self) -> None:
        """Test custom guidance takes precedence over port-specific guidance."""
        error = PortBindingError("Error", port=8080, guidance="Custom guidance")
        assert error.guidance == "Custom guidance"

    def test_inherits_from_server_startup_error(self) -> None:
        """Test PortBindingError inherits from ServerStartupError."""
        error = PortBindingError("Test")
        assert isinstance(error, ServerStartupError)
        assert isinstance(error, MCPError)

    def test_repr_includes_port(self) -> None:
        """Test __repr__ includes port."""
        error = PortBindingError("Bind failed", port=3000)
        result = repr(error)
        assert "PortBindingError(" in result
        assert "port=3000" in result


# =============================================================================
# Inheritance Hierarchy Tests
# =============================================================================


class TestInheritanceHierarchy:
    """Tests for complete inheritance hierarchy."""

    def test_network_error_hierarchy(self) -> None:
        """Test network error inheritance chain."""
        # NetworkError -> MCPError -> Exception
        assert issubclass(NetworkError, MCPError)
        assert issubclass(NetworkError, Exception)

        # ConnectionError -> NetworkError -> MCPError
        assert issubclass(ConnectionError, NetworkError)
        assert issubclass(ConnectionError, MCPError)

        # TimeoutError -> NetworkError -> MCPError
        assert issubclass(TimeoutError, NetworkError)
        assert issubclass(TimeoutError, MCPError)

        # DNSError -> NetworkError -> MCPError
        assert issubclass(DNSError, NetworkError)
        assert issubclass(DNSError, MCPError)

    def test_http_error_hierarchy(self) -> None:
        """Test HTTP error inheritance chain."""
        # HTTPError -> MCPError -> Exception
        assert issubclass(HTTPError, MCPError)
        assert issubclass(HTTPError, Exception)

        # RateLimitError -> HTTPError -> MCPError
        assert issubclass(RateLimitError, HTTPError)
        assert issubclass(RateLimitError, MCPError)

        # ServiceUnavailableError -> HTTPError -> MCPError
        assert issubclass(ServiceUnavailableError, HTTPError)
        assert issubclass(ServiceUnavailableError, MCPError)

    def test_validation_error_hierarchy(self) -> None:
        """Test validation error inheritance chain."""
        # ValidationError -> MCPError -> Exception
        assert issubclass(ValidationError, MCPError)
        assert issubclass(ValidationError, Exception)

        # InvalidURLError -> ValidationError -> MCPError
        assert issubclass(InvalidURLError, ValidationError)
        assert issubclass(InvalidURLError, MCPError)

    def test_server_error_hierarchy(self) -> None:
        """Test server error inheritance chain."""
        # ServerStartupError -> MCPError -> Exception
        assert issubclass(ServerStartupError, MCPError)
        assert issubclass(ServerStartupError, Exception)

        # DependencyError -> ServerStartupError -> MCPError
        assert issubclass(DependencyError, ServerStartupError)
        assert issubclass(DependencyError, MCPError)

        # ConfigurationError -> ServerStartupError -> MCPError
        assert issubclass(ConfigurationError, ServerStartupError)
        assert issubclass(ConfigurationError, MCPError)

        # PortBindingError -> ServerStartupError -> MCPError
        assert issubclass(PortBindingError, ServerStartupError)
        assert issubclass(PortBindingError, MCPError)

    def test_content_error_hierarchy(self) -> None:
        """Test content error inheritance chain."""
        # ContentParsingError -> MCPError -> Exception
        assert issubclass(ContentParsingError, MCPError)
        assert issubclass(ContentParsingError, Exception)


# =============================================================================
# Exception Catching Tests
# =============================================================================


class TestExceptionCatching:
    """Tests for proper exception catching behavior."""

    def test_catch_mcp_error_catches_all_subclasses(self) -> None:
        """Test that catching MCPError catches all custom exceptions."""
        exceptions_to_test = [
            NetworkError("test"),
            ConnectionError("test"),
            TimeoutError("test"),
            DNSError("test"),
            HTTPError("test"),
            RateLimitError("test"),
            ServiceUnavailableError("test"),
            ValidationError("test"),
            InvalidURLError("test"),
            ContentParsingError("test"),
            ServerStartupError("test"),
            DependencyError("test"),
            ConfigurationError("test"),
            PortBindingError("test"),
        ]

        for exc in exceptions_to_test:
            with pytest.raises(MCPError):
                raise exc

    def test_catch_network_error_catches_network_subclasses(self) -> None:
        """Test NetworkError catches its subclasses."""
        network_exceptions = [
            ConnectionError("test"),
            TimeoutError("test"),
            DNSError("test"),
        ]

        for exc in network_exceptions:
            with pytest.raises(NetworkError):
                raise exc

    def test_catch_http_error_catches_http_subclasses(self) -> None:
        """Test HTTPError catches its subclasses."""
        http_exceptions = [
            RateLimitError("test"),
            ServiceUnavailableError("test"),
        ]

        for exc in http_exceptions:
            with pytest.raises(HTTPError):
                raise exc

    def test_catch_validation_error_catches_url_error(self) -> None:
        """Test ValidationError catches InvalidURLError."""
        with pytest.raises(ValidationError):
            raise InvalidURLError("test")

    def test_catch_server_startup_error_catches_subclasses(self) -> None:
        """Test ServerStartupError catches its subclasses."""
        server_exceptions = [
            DependencyError("test"),
            ConfigurationError("test"),
            PortBindingError("test"),
        ]

        for exc in server_exceptions:
            with pytest.raises(ServerStartupError):
                raise exc


# =============================================================================
# Edge Cases and Special Behavior Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and special behaviors."""

    def test_empty_message(self) -> None:
        """Test exception with empty message."""
        error = MCPError("")
        assert error.message == ""
        assert str(error).startswith("[")

    def test_unicode_message(self) -> None:
        """Test exception with unicode characters in message."""
        error = MCPError("Error with unicode: \u2022 \u2714 \u2718")
        assert "\u2022" in error.message
        assert "\u2022" in str(error)

    def test_very_long_message(self) -> None:
        """Test exception with very long message."""
        long_message = "x" * 10000
        error = MCPError(long_message)
        assert error.message == long_message
        assert long_message in str(error)

    def test_newlines_in_message(self) -> None:
        """Test exception with newlines in message."""
        error = MCPError("Line 1\nLine 2\nLine 3")
        assert "\n" in error.message

    def test_guidance_property_returns_custom_over_default(self) -> None:
        """Test guidance property returns custom guidance when set."""
        error = MCPError("test", guidance="Custom guidance here")
        assert error.guidance == "Custom guidance here"

    def test_guidance_property_returns_default_when_none(self) -> None:
        """Test guidance property returns default when _guidance is None."""
        error = MCPError("test")
        assert error._guidance is None
        assert error.guidance == error.default_guidance

    def test_rate_limit_error_none_retry_after_default_guidance(self) -> None:
        """Test RateLimitError uses default guidance when retry_after is None."""
        error = RateLimitError("Rate limited", retry_after=None)
        assert "30-60 seconds" in error.guidance

    def test_port_binding_error_none_port_default_guidance(self) -> None:
        """Test PortBindingError uses default guidance when port is None."""
        error = PortBindingError("Bind failed", port=None)
        assert "<port>" in error.guidance

    def test_exception_args_preserved(self) -> None:
        """Test that Exception.args contains the message."""
        error = MCPError("Test message")
        assert error.args == ("Test message",)
