#!/usr/bin/env python3
"""
Tests for error classification and handling in the jina_fetch module.

This module tests:
- _classify_request_error function for classifying requests exceptions
- _validate_url function for URL validation error messages
- Various HTTP error scenarios in fetch operations
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from duckduckgo_mcp.exceptions import ConnectionError as MCPConnectionError
from duckduckgo_mcp.exceptions import (
    ContentParsingError,
    DNSError,
    ErrorCategory,
    HTTPError,
    InvalidURLError,
    MCPError,
    NetworkError,
    RateLimitError,
    ServiceUnavailableError,
)
from duckduckgo_mcp.exceptions import TimeoutError as MCPTimeoutError
from duckduckgo_mcp.exceptions import (
    ValidationError,
)
from duckduckgo_mcp.jina_fetch import (
    _classify_request_error,
    _validate_url,
    fetch_url,
    jina_fetch,
)

# =============================================================================
# _classify_request_error Tests
# =============================================================================


class TestClassifyRequestError:
    """Tests for the _classify_request_error helper function."""

    # -------------------------------------------------------------------------
    # Timeout Error Tests
    # -------------------------------------------------------------------------

    def test_timeout_error_classification(self) -> None:
        """Test that requests Timeout is classified as MCPTimeoutError."""
        error = requests.exceptions.Timeout("Connection timed out")
        result = _classify_request_error(error)

        assert isinstance(result, MCPTimeoutError)
        assert result.category == ErrorCategory.NETWORK
        assert "timed out" in result.message.lower()

    def test_timeout_error_with_url_context(self) -> None:
        """Test timeout error includes URL context when provided."""
        error = requests.exceptions.Timeout("Connection timed out")
        result = _classify_request_error(error, url="https://example.com")

        assert isinstance(result, MCPTimeoutError)
        assert "https://example.com" in result.message

    def test_read_timeout_classification(self) -> None:
        """Test that ReadTimeout is classified as MCPTimeoutError."""
        error = requests.exceptions.ReadTimeout("Read timed out")
        result = _classify_request_error(error)

        assert isinstance(result, MCPTimeoutError)

    def test_connect_timeout_classification(self) -> None:
        """Test that ConnectTimeout is classified as MCPTimeoutError."""
        error = requests.exceptions.ConnectTimeout("Connect timed out")
        result = _classify_request_error(error)

        assert isinstance(result, MCPTimeoutError)

    # -------------------------------------------------------------------------
    # SSL Error Tests
    # -------------------------------------------------------------------------

    def test_ssl_error_classification(self) -> None:
        """Test that SSLError is classified as NetworkError with SSL guidance."""
        error = requests.exceptions.SSLError("SSL certificate verify failed")
        result = _classify_request_error(error)

        assert isinstance(result, NetworkError)
        assert "SSL" in result.message or "TLS" in result.message
        assert "certificate" in result.guidance.lower()

    def test_ssl_error_with_url_context(self) -> None:
        """Test SSL error includes URL context when provided."""
        error = requests.exceptions.SSLError("SSL handshake failed")
        result = _classify_request_error(error, url="https://example.com")

        assert isinstance(result, NetworkError)
        assert "https://example.com" in result.message

    # -------------------------------------------------------------------------
    # DNS Error Tests
    # -------------------------------------------------------------------------

    def test_connection_error_with_dns_nodename_classified_as_dns_error(self) -> None:
        """Test connection error with 'nodename' indicator is classified as DNSError."""
        error = requests.exceptions.ConnectionError(
            "Max retries exceeded: nodename nor servname provided"
        )
        result = _classify_request_error(error)

        assert isinstance(result, DNSError)
        assert result.category == ErrorCategory.NETWORK
        assert (
            "resolve" in result.message.lower() or "hostname" in result.message.lower()
        )

    def test_connection_error_with_name_not_known_classified_as_dns_error(self) -> None:
        """Test connection error with 'name or service not known' is DNSError."""
        error = requests.exceptions.ConnectionError("Failed: Name or service not known")
        result = _classify_request_error(error)

        assert isinstance(result, DNSError)

    def test_connection_error_with_getaddrinfo_classified_as_dns_error(self) -> None:
        """Test connection error with 'getaddrinfo failed' is DNSError."""
        error = requests.exceptions.ConnectionError("getaddrinfo failed: No address")
        result = _classify_request_error(error)

        assert isinstance(result, DNSError)

    def test_connection_error_with_failed_to_resolve_classified_as_dns_error(
        self,
    ) -> None:
        """Test connection error with 'failed to resolve' is DNSError."""
        error = requests.exceptions.ConnectionError("Failed to resolve host")
        result = _classify_request_error(error)

        assert isinstance(result, DNSError)

    def test_connection_error_with_temporary_failure_classified_as_dns_error(
        self,
    ) -> None:
        """Test connection error with 'temporary failure in name resolution'."""
        error = requests.exceptions.ConnectionError(
            "Temporary failure in name resolution"
        )
        result = _classify_request_error(error)

        assert isinstance(result, DNSError)

    def test_dns_error_with_url_context(self) -> None:
        """Test DNS error includes URL context when provided."""
        error = requests.exceptions.ConnectionError("nodename nor servname provided")
        result = _classify_request_error(error, url="https://nonexistent.invalid")

        assert isinstance(result, DNSError)
        assert "nonexistent.invalid" in result.message

    # -------------------------------------------------------------------------
    # Connection Error Tests
    # -------------------------------------------------------------------------

    def test_generic_connection_error_classification(self) -> None:
        """Test generic connection error is classified as MCPConnectionError."""
        error = requests.exceptions.ConnectionError("Connection refused")
        result = _classify_request_error(error)

        assert isinstance(result, MCPConnectionError)
        assert result.category == ErrorCategory.NETWORK

    def test_connection_reset_error_classification(self) -> None:
        """Test connection reset error is classified as MCPConnectionError."""
        error = requests.exceptions.ConnectionError("Connection reset by peer")
        result = _classify_request_error(error)

        assert isinstance(result, MCPConnectionError)

    def test_connection_error_with_url_context(self) -> None:
        """Test connection error includes URL context when provided."""
        error = requests.exceptions.ConnectionError("Connection refused")
        result = _classify_request_error(error, url="https://example.com:8080")

        assert isinstance(result, MCPConnectionError)
        assert "example.com:8080" in result.message

    # -------------------------------------------------------------------------
    # HTTP Error Tests - Rate Limiting
    # -------------------------------------------------------------------------

    def test_http_429_classified_as_rate_limit_error(self) -> None:
        """Test HTTP 429 status is classified as RateLimitError."""
        response = Mock()
        response.status_code = 429
        response.headers = {}
        error = requests.exceptions.HTTPError(response=response)

        result = _classify_request_error(error)

        assert isinstance(result, RateLimitError)
        assert result.status_code == 429
        assert result.category == ErrorCategory.SERVICE

    def test_http_429_with_retry_after_header(self) -> None:
        """Test HTTP 429 with Retry-After header preserves retry time."""
        response = Mock()
        response.status_code = 429
        response.headers = {"Retry-After": "60"}
        error = requests.exceptions.HTTPError(response=response)

        result = _classify_request_error(error)

        assert isinstance(result, RateLimitError)
        assert result.retry_after == 60

    def test_http_429_with_invalid_retry_after_header(self) -> None:
        """Test HTTP 429 with invalid Retry-After header handles gracefully."""
        response = Mock()
        response.status_code = 429
        response.headers = {"Retry-After": "not-a-number"}
        error = requests.exceptions.HTTPError(response=response)

        result = _classify_request_error(error)

        assert isinstance(result, RateLimitError)
        assert result.retry_after is None

    # -------------------------------------------------------------------------
    # HTTP Error Tests - Service Unavailable
    # -------------------------------------------------------------------------

    def test_http_503_classified_as_service_unavailable(self) -> None:
        """Test HTTP 503 status is classified as ServiceUnavailableError."""
        response = Mock()
        response.status_code = 503
        error = requests.exceptions.HTTPError(response=response)

        result = _classify_request_error(error)

        assert isinstance(result, ServiceUnavailableError)
        assert result.status_code == 503
        assert result.category == ErrorCategory.SERVICE

    # -------------------------------------------------------------------------
    # HTTP Error Tests - Not Found (404)
    # -------------------------------------------------------------------------

    def test_http_404_classified_as_http_error(self) -> None:
        """Test HTTP 404 status is classified as HTTPError with guidance."""
        response = Mock()
        response.status_code = 404
        error = requests.exceptions.HTTPError(response=response)

        result = _classify_request_error(error)

        assert isinstance(result, HTTPError)
        assert result.status_code == 404
        assert "not found" in result.message.lower()
        assert "verify the url" in result.guidance.lower()

    def test_http_404_with_url_context(self) -> None:
        """Test HTTP 404 includes URL context when provided."""
        response = Mock()
        response.status_code = 404
        error = requests.exceptions.HTTPError(response=response)

        result = _classify_request_error(error, url="https://example.com/missing")

        assert isinstance(result, HTTPError)
        assert "example.com/missing" in result.message

    # -------------------------------------------------------------------------
    # HTTP Error Tests - Forbidden (403)
    # -------------------------------------------------------------------------

    def test_http_403_classified_as_http_error(self) -> None:
        """Test HTTP 403 status is classified as HTTPError with guidance."""
        response = Mock()
        response.status_code = 403
        error = requests.exceptions.HTTPError(response=response)

        result = _classify_request_error(error)

        assert isinstance(result, HTTPError)
        assert result.status_code == 403
        assert "forbidden" in result.message.lower()
        assert (
            "permission" in result.guidance.lower()
            or "authentication" in result.guidance.lower()
        )

    # -------------------------------------------------------------------------
    # HTTP Error Tests - Server Errors (5xx)
    # -------------------------------------------------------------------------

    def test_http_500_classified_as_http_error(self) -> None:
        """Test HTTP 500 status is classified as HTTPError with server guidance."""
        response = Mock()
        response.status_code = 500
        error = requests.exceptions.HTTPError(response=response)

        result = _classify_request_error(error)

        assert isinstance(result, HTTPError)
        assert result.status_code == 500
        assert "server error" in result.message.lower()

    def test_http_502_classified_as_http_error(self) -> None:
        """Test HTTP 502 status is classified as HTTPError."""
        response = Mock()
        response.status_code = 502
        error = requests.exceptions.HTTPError(response=response)

        result = _classify_request_error(error)

        assert isinstance(result, HTTPError)
        assert result.status_code == 502

    # -------------------------------------------------------------------------
    # HTTP Error Tests - Generic
    # -------------------------------------------------------------------------

    def test_http_error_without_response(self) -> None:
        """Test HTTP error without response object is handled gracefully."""
        error = requests.exceptions.HTTPError()
        error.response = None

        result = _classify_request_error(error)

        assert isinstance(result, HTTPError)
        assert result.status_code is None

    def test_http_400_classified_as_generic_http_error(self) -> None:
        """Test HTTP 400 (Bad Request) is classified as generic HTTPError."""
        response = Mock()
        response.status_code = 400
        error = requests.exceptions.HTTPError(response=response)

        result = _classify_request_error(error)

        assert isinstance(result, HTTPError)
        assert result.status_code == 400

    # -------------------------------------------------------------------------
    # Generic RequestException Tests
    # -------------------------------------------------------------------------

    def test_generic_request_exception_classified_as_network_error(self) -> None:
        """Test generic RequestException is classified as NetworkError."""
        error = requests.exceptions.RequestException("Unknown error")
        result = _classify_request_error(error)

        assert isinstance(result, NetworkError)
        assert result.category == ErrorCategory.NETWORK

    def test_chunked_encoding_error_classified_as_network_error(self) -> None:
        """Test ChunkedEncodingError is classified as NetworkError."""
        error = requests.exceptions.ChunkedEncodingError("Incomplete read")
        result = _classify_request_error(error)

        assert isinstance(result, NetworkError)

    def test_content_decoding_error_classified_as_network_error(self) -> None:
        """Test ContentDecodingError is classified as NetworkError."""
        error = requests.exceptions.ContentDecodingError("Decode failed")
        result = _classify_request_error(error)

        assert isinstance(result, NetworkError)


# =============================================================================
# _validate_url Tests
# =============================================================================


class TestValidateUrl:
    """Tests for the _validate_url function."""

    # -------------------------------------------------------------------------
    # Valid URL Tests
    # -------------------------------------------------------------------------

    def test_valid_https_url_passes(self) -> None:
        """Test that a valid HTTPS URL passes validation."""
        # Should not raise
        _validate_url("https://example.com")

    def test_valid_http_url_passes(self) -> None:
        """Test that a valid HTTP URL passes validation."""
        # Should not raise
        _validate_url("http://example.com")

    def test_valid_url_with_path_passes(self) -> None:
        """Test that a URL with path passes validation."""
        _validate_url("https://example.com/path/to/resource")

    def test_valid_url_with_query_passes(self) -> None:
        """Test that a URL with query string passes validation."""
        _validate_url("https://example.com/search?q=test")

    def test_valid_url_with_port_passes(self) -> None:
        """Test that a URL with port number passes validation."""
        _validate_url("https://example.com:8080/api")

    def test_valid_localhost_url_passes(self) -> None:
        """Test that localhost URLs pass validation."""
        _validate_url("http://localhost:3000")

    # -------------------------------------------------------------------------
    # Empty/None URL Tests
    # -------------------------------------------------------------------------

    def test_none_url_raises_invalid_url_error(self) -> None:
        """Test that None URL raises InvalidURLError."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url(None)  # type: ignore

        assert "non-empty string" in exc_info.value.message.lower()
        assert exc_info.value.category == ErrorCategory.VALIDATION

    def test_empty_string_url_raises_invalid_url_error(self) -> None:
        """Test that empty string URL raises InvalidURLError."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url("")

        assert exc_info.value.category == ErrorCategory.VALIDATION

    def test_whitespace_only_url_raises_invalid_url_error(self) -> None:
        """Test that whitespace-only URL raises InvalidURLError."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url("   ")

        assert (
            "empty" in exc_info.value.message.lower()
            or "whitespace" in exc_info.value.message.lower()
        )

    def test_non_string_url_raises_invalid_url_error(self) -> None:
        """Test that non-string URL raises InvalidURLError."""
        with pytest.raises(InvalidURLError):
            _validate_url(12345)  # type: ignore

    # -------------------------------------------------------------------------
    # Missing Scheme Tests
    # -------------------------------------------------------------------------

    def test_url_without_scheme_raises_error(self) -> None:
        """Test that URL without scheme raises InvalidURLError."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url("example.com")

        assert "scheme" in exc_info.value.message.lower()
        assert (
            "http://" in exc_info.value.guidance
            or "https://" in exc_info.value.guidance
        )

    def test_url_without_scheme_suggests_https(self) -> None:
        """Test that URL without scheme suggests adding https://."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url("example.com/path")

        # Guidance should suggest the correct URL
        assert "https://example.com" in exc_info.value.guidance

    def test_url_starting_with_www_without_scheme_raises_error(self) -> None:
        """Test www. URL without scheme raises error with helpful guidance."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url("www.example.com")

        assert "scheme" in exc_info.value.message.lower()

    # -------------------------------------------------------------------------
    # Unsupported Scheme Tests
    # -------------------------------------------------------------------------

    def test_ftp_scheme_raises_error(self) -> None:
        """Test that FTP scheme raises InvalidURLError."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url("ftp://files.example.com")

        assert "ftp" in exc_info.value.message.lower()
        assert "unsupported" in exc_info.value.message.lower()

    def test_file_scheme_raises_error(self) -> None:
        """Test that file:// scheme raises InvalidURLError."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url("file:///home/user/document.txt")

        assert "file" in exc_info.value.message.lower()

    def test_mailto_scheme_raises_error(self) -> None:
        """Test that mailto: scheme raises InvalidURLError."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url("mailto:user@example.com")

        assert "mailto" in exc_info.value.message.lower()

    def test_javascript_scheme_raises_error(self) -> None:
        """Test that javascript: scheme raises InvalidURLError."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url("javascript:alert('test')")

        assert "javascript" in exc_info.value.message.lower()

    # -------------------------------------------------------------------------
    # Missing Domain Tests
    # -------------------------------------------------------------------------

    def test_url_with_scheme_but_no_domain_raises_error(self) -> None:
        """Test URL with scheme but no domain raises error."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url("https://")

        assert "domain" in exc_info.value.message.lower()

    def test_url_with_scheme_only_path_raises_error(self) -> None:
        """Test URL with scheme and path but no domain raises error."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url("https:///path/to/file")

        assert "domain" in exc_info.value.message.lower()

    # -------------------------------------------------------------------------
    # URL with Spaces Tests
    # -------------------------------------------------------------------------

    def test_url_with_spaces_raises_error(self) -> None:
        """Test that URL with spaces raises InvalidURLError."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url("https://example.com/path with spaces")

        assert "space" in exc_info.value.message.lower()

    def test_url_with_spaces_suggests_encoding(self) -> None:
        """Test that URL with spaces suggests URL encoding."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url("https://example.com/my file.pdf")

        assert "%20" in exc_info.value.guidance

    # -------------------------------------------------------------------------
    # Error Message Quality Tests
    # -------------------------------------------------------------------------

    def test_invalid_url_error_has_guidance(self) -> None:
        """Test that InvalidURLError always includes guidance."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url("not-a-url")

        assert exc_info.value.guidance is not None
        assert len(exc_info.value.guidance) > 0

    def test_invalid_url_error_includes_example_urls(self) -> None:
        """Test that InvalidURLError guidance includes example valid URLs."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url("example.com")

        assert (
            "example.com" in exc_info.value.guidance
            or "https://" in exc_info.value.guidance
        )

    def test_invalid_url_stores_url_attribute(self) -> None:
        """Test that InvalidURLError stores the invalid URL."""
        with pytest.raises(InvalidURLError) as exc_info:
            _validate_url("ftp://example.com")

        assert exc_info.value.url == "ftp://example.com"


# =============================================================================
# fetch_url Error Handling Tests
# =============================================================================


class TestFetchUrlErrors:
    """Tests for error handling in the fetch_url function."""

    def test_fetch_url_raises_invalid_url_error_for_bad_url(self) -> None:
        """Test fetch_url raises InvalidURLError for invalid URL."""
        with pytest.raises(InvalidURLError):
            fetch_url("not-a-valid-url")

    def test_fetch_url_raises_invalid_url_error_for_empty_url(self) -> None:
        """Test fetch_url raises InvalidURLError for empty URL."""
        with pytest.raises(InvalidURLError):
            fetch_url("")

    @patch("duckduckgo_mcp.jina_fetch.requests.get")
    def test_fetch_url_classifies_timeout_error(self, mock_get: MagicMock) -> None:
        """Test fetch_url raises MCPTimeoutError for timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        with pytest.raises(MCPTimeoutError) as exc_info:
            fetch_url("https://example.com")

        assert exc_info.value.category == ErrorCategory.NETWORK

    @patch("duckduckgo_mcp.jina_fetch.requests.get")
    def test_fetch_url_classifies_connection_error(self, mock_get: MagicMock) -> None:
        """Test fetch_url raises MCPConnectionError for connection issues."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        with pytest.raises(MCPConnectionError) as exc_info:
            fetch_url("https://example.com")

        assert exc_info.value.category == ErrorCategory.NETWORK

    @patch("duckduckgo_mcp.jina_fetch.requests.get")
    def test_fetch_url_classifies_dns_error(self, mock_get: MagicMock) -> None:
        """Test fetch_url raises DNSError for DNS resolution failures."""
        mock_get.side_effect = requests.exceptions.ConnectionError(
            "nodename nor servname provided"
        )

        with pytest.raises(DNSError) as exc_info:
            fetch_url("https://nonexistent.invalid")

        assert exc_info.value.category == ErrorCategory.NETWORK

    @patch("duckduckgo_mcp.jina_fetch.requests.get")
    def test_fetch_url_classifies_rate_limit_error(self, mock_get: MagicMock) -> None:
        """Test fetch_url raises RateLimitError for HTTP 429."""
        response = Mock()
        response.status_code = 429
        response.headers = {"Retry-After": "30"}
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=response
        )
        mock_get.return_value = response

        with pytest.raises(RateLimitError) as exc_info:
            fetch_url("https://example.com")

        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after == 30

    @patch("duckduckgo_mcp.jina_fetch.requests.get")
    def test_fetch_url_classifies_service_unavailable_error(
        self, mock_get: MagicMock
    ) -> None:
        """Test fetch_url raises ServiceUnavailableError for HTTP 503."""
        response = Mock()
        response.status_code = 503
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=response
        )
        mock_get.return_value = response

        with pytest.raises(ServiceUnavailableError) as exc_info:
            fetch_url("https://example.com")

        assert exc_info.value.status_code == 503

    @patch("duckduckgo_mcp.jina_fetch.requests.get")
    def test_fetch_url_classifies_not_found_error(self, mock_get: MagicMock) -> None:
        """Test fetch_url raises HTTPError for HTTP 404."""
        response = Mock()
        response.status_code = 404
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=response
        )
        mock_get.return_value = response

        with pytest.raises(HTTPError) as exc_info:
            fetch_url("https://example.com/missing")

        assert exc_info.value.status_code == 404

    @patch("duckduckgo_mcp.jina_fetch.requests.get")
    def test_fetch_url_raises_content_parsing_error_for_invalid_json(
        self, mock_get: MagicMock
    ) -> None:
        """Test fetch_url raises ContentParsingError for invalid JSON."""
        import json

        response = Mock()
        response.status_code = 200
        response.raise_for_status.return_value = None
        # json.JSONDecodeError requires specific arguments
        response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_get.return_value = response

        with pytest.raises(ContentParsingError) as exc_info:
            fetch_url("https://example.com", output_format="json")

        assert exc_info.value.content_type == "json"
        assert exc_info.value.category == ErrorCategory.CONTENT

    @patch("duckduckgo_mcp.jina_fetch.requests.get")
    def test_fetch_url_preserves_exception_chain(self, mock_get: MagicMock) -> None:
        """Test fetch_url preserves the original exception in the chain."""
        original_error = requests.exceptions.Timeout("Original timeout")
        mock_get.side_effect = original_error

        with pytest.raises(MCPTimeoutError) as exc_info:
            fetch_url("https://example.com")

        # The __cause__ should be the original exception
        assert exc_info.value.__cause__ is original_error


# =============================================================================
# jina_fetch Tool Error Handling Tests
# =============================================================================


class TestJinaFetchToolErrors:
    """Tests for error handling in the jina_fetch MCP tool.

    Note: jina_fetch decorated with @mcp.tool() is a regular function.
    """

    def test_jina_fetch_raises_validation_error_for_missing_url(self) -> None:
        """Test jina_fetch raises ValidationError for missing URL."""
        with pytest.raises(ValidationError) as exc_info:
            jina_fetch(url="")

        assert "url" in exc_info.value.message.lower()
        assert exc_info.value.category == ErrorCategory.VALIDATION

    def test_jina_fetch_raises_validation_error_for_invalid_format(self) -> None:
        """Test jina_fetch raises ValidationError for invalid format."""
        with pytest.raises(ValidationError) as exc_info:
            jina_fetch(url="https://example.com", format="xml")

        assert "format" in exc_info.value.message.lower()
        assert "markdown" in exc_info.value.guidance
        assert "json" in exc_info.value.guidance

    def test_jina_fetch_raises_validation_error_for_negative_max_length(self) -> None:
        """Test jina_fetch raises ValidationError for negative max_length."""
        with pytest.raises(ValidationError) as exc_info:
            jina_fetch(url="https://example.com", max_length=-100)

        assert "max_length" in exc_info.value.message.lower()
        assert "positive" in exc_info.value.guidance.lower()

    def test_jina_fetch_raises_validation_error_for_zero_max_length(self) -> None:
        """Test jina_fetch raises ValidationError for zero max_length."""
        with pytest.raises(ValidationError) as exc_info:
            jina_fetch(url="https://example.com", max_length=0)

        assert "max_length" in exc_info.value.message.lower()

    def test_jina_fetch_raises_validation_error_for_non_numeric_max_length(
        self,
    ) -> None:
        """Test jina_fetch raises ValidationError for non-numeric max_length."""
        with pytest.raises(ValidationError) as exc_info:
            jina_fetch(url="https://example.com", max_length="abc")  # type: ignore

        assert "max_length" in exc_info.value.message.lower()
        assert "number" in exc_info.value.guidance.lower()

    def test_jina_fetch_raises_invalid_url_error_for_bad_url(self) -> None:
        """Test jina_fetch raises InvalidURLError for invalid URL format."""
        with pytest.raises(InvalidURLError):
            jina_fetch(url="not-a-valid-url")

    @patch("duckduckgo_mcp.jina_fetch.fetch_url")
    def test_jina_fetch_propagates_mcp_error(self, mock_fetch: MagicMock) -> None:
        """Test jina_fetch re-raises MCPError exceptions."""
        mock_fetch.side_effect = MCPTimeoutError("Request timed out")

        with pytest.raises(MCPTimeoutError):
            jina_fetch(url="https://example.com")

    @patch("duckduckgo_mcp.jina_fetch.fetch_url")
    def test_jina_fetch_propagates_rate_limit_error(
        self, mock_fetch: MagicMock
    ) -> None:
        """Test jina_fetch re-raises RateLimitError exceptions."""
        mock_fetch.side_effect = RateLimitError("Too many requests", retry_after=60)

        with pytest.raises(RateLimitError) as exc_info:
            jina_fetch(url="https://example.com")

        assert exc_info.value.retry_after == 60


# =============================================================================
# Error Context and Guidance Tests
# =============================================================================


class TestErrorContextAndGuidance:
    """Tests for error context and actionable guidance."""

    def test_timeout_error_has_actionable_guidance(self) -> None:
        """Test timeout error provides actionable guidance."""
        error = requests.exceptions.Timeout("Timeout")
        result = _classify_request_error(error, url="https://example.com")

        assert (
            "timed out" in result.guidance.lower()
            or "timeout" in result.guidance.lower()
        )

    def test_connection_error_has_actionable_guidance(self) -> None:
        """Test connection error provides actionable guidance."""
        error = requests.exceptions.ConnectionError("Connection refused")
        result = _classify_request_error(error, url="https://example.com")

        # Guidance should mention possible causes
        assert any(
            phrase in result.guidance.lower()
            for phrase in ["connection", "server", "try again"]
        )

    def test_rate_limit_error_has_actionable_guidance(self) -> None:
        """Test rate limit error provides actionable guidance with timing."""
        response = Mock()
        response.status_code = 429
        response.headers = {"Retry-After": "45"}
        error = requests.exceptions.HTTPError(response=response)

        result = _classify_request_error(error)

        assert isinstance(result, RateLimitError)
        assert "45" in result.guidance or "wait" in result.guidance.lower()

    def test_dns_error_has_actionable_guidance(self) -> None:
        """Test DNS error provides actionable guidance."""
        error = requests.exceptions.ConnectionError("nodename nor servname provided")
        result = _classify_request_error(error)

        assert any(
            phrase in result.guidance.lower()
            for phrase in ["dns", "hostname", "url", "spelled"]
        )

    def test_not_found_error_has_actionable_guidance(self) -> None:
        """Test 404 error provides actionable guidance."""
        response = Mock()
        response.status_code = 404
        error = requests.exceptions.HTTPError(response=response)

        result = _classify_request_error(error)

        # Guidance should suggest checking URL
        assert any(
            phrase in result.guidance.lower()
            for phrase in ["url", "verify", "check", "removed"]
        )

    def test_forbidden_error_has_actionable_guidance(self) -> None:
        """Test 403 error provides actionable guidance."""
        response = Mock()
        response.status_code = 403
        error = requests.exceptions.HTTPError(response=response)

        result = _classify_request_error(error)

        # Guidance should mention access/permission
        assert any(
            phrase in result.guidance.lower()
            for phrase in ["permission", "access", "authentication", "blocked"]
        )


# =============================================================================
# SSL Error Priority Tests (Regression Test)
# =============================================================================


class TestSSLErrorPriority:
    """
    Tests to verify SSL errors are checked before ConnectionError.

    This is a regression test for the gotcha: SSLError is a subclass of
    ConnectionError in the requests library. If we check ConnectionError first,
    SSL errors will be misclassified.
    """

    def test_ssl_error_not_classified_as_connection_error(self) -> None:
        """Test SSLError is NOT classified as ConnectionError."""
        error = requests.exceptions.SSLError("Certificate verify failed")
        result = _classify_request_error(error)

        # Should be NetworkError (with SSL context), not ConnectionError
        assert not isinstance(result, MCPConnectionError)
        assert isinstance(result, NetworkError)
        assert "ssl" in result.message.lower() or "tls" in result.message.lower()

    def test_ssl_error_has_certificate_guidance(self) -> None:
        """Test SSLError provides certificate-related guidance."""
        error = requests.exceptions.SSLError("CERTIFICATE_VERIFY_FAILED")
        result = _classify_request_error(error)

        assert "certificate" in result.guidance.lower()
