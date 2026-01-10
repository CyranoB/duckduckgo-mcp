#!/usr/bin/env python3
"""
Tests for error classification and handling in the duckduckgo_search module.

This module tests:
- _classify_search_error function for classifying search exceptions
- _validate_search_params function for parameter validation
- _try_fallback_search behavior
- search_duckduckgo error handling
- duckduckgo_search MCP tool error handling
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from ddgs.exceptions import DDGSException

from duckduckgo_mcp.duckduckgo_search import (
    _classify_search_error,
    _format_results_as_text,
    _try_fallback_search,
    _validate_search_params,
    duckduckgo_search,
    search_duckduckgo,
)
from duckduckgo_mcp.exceptions import (
    ErrorCategory,
    MCPError,
    NetworkError,
    RateLimitError,
    ServiceUnavailableError,
)
from duckduckgo_mcp.exceptions import TimeoutError as MCPTimeoutError
from duckduckgo_mcp.exceptions import (
    ValidationError,
)

# =============================================================================
# _classify_search_error Tests
# =============================================================================


class TestClassifySearchError:
    """Tests for the _classify_search_error helper function."""

    # -------------------------------------------------------------------------
    # Rate Limiting Detection Tests
    # -------------------------------------------------------------------------

    def test_rate_limit_detection_429(self) -> None:
        """Test that '429' in error message is classified as RateLimitError."""
        error = DDGSException("HTTP Error 429: Too Many Requests")
        result = _classify_search_error(error)

        assert isinstance(result, RateLimitError)
        assert result.category == ErrorCategory.SERVICE
        assert "rate" in result.message.lower() or "limit" in result.message.lower()

    def test_rate_limit_detection_blocked(self) -> None:
        """Test that 'blocked' in error message is classified as RateLimitError."""
        error = DDGSException("Request blocked by DuckDuckGo")
        result = _classify_search_error(error)

        assert isinstance(result, RateLimitError)

    def test_rate_limit_detection_temporarily_blocked(self) -> None:
        """Test that 'temporarily blocked' is classified as RateLimitError."""
        error = DDGSException("User has been temporarily blocked")
        result = _classify_search_error(error)

        assert isinstance(result, RateLimitError)

    def test_rate_limit_detection_throttle(self) -> None:
        """Test that 'throttle' in error message is classified as RateLimitError."""
        error = DDGSException("Request throttled, please slow down")
        result = _classify_search_error(error)

        assert isinstance(result, RateLimitError)

    def test_rate_limit_detection_too_many_requests(self) -> None:
        """Test that 'too many requests' is classified as RateLimitError."""
        error = DDGSException("Too many requests from this IP")
        result = _classify_search_error(error)

        assert isinstance(result, RateLimitError)

    def test_rate_limit_detection_please_wait(self) -> None:
        """Test that 'please wait' is classified as RateLimitError."""
        error = DDGSException("Please wait before trying again")
        result = _classify_search_error(error)

        assert isinstance(result, RateLimitError)

    def test_rate_limit_detection_exceeded(self) -> None:
        """Test that 'exceeded' is classified as RateLimitError."""
        error = DDGSException("Request limit exceeded")
        result = _classify_search_error(error)

        assert isinstance(result, RateLimitError)

    def test_rate_limit_detection_try_again_later(self) -> None:
        """Test that 'try again later' is classified as RateLimitError."""
        error = DDGSException("Please try again later")
        result = _classify_search_error(error)

        assert isinstance(result, RateLimitError)

    def test_rate_limit_has_actionable_guidance(self) -> None:
        """Test that RateLimitError includes actionable guidance."""
        error = DDGSException("429 Rate Limited")
        result = _classify_search_error(error)

        assert isinstance(result, RateLimitError)
        assert "wait" in result.guidance.lower()
        assert (
            "30-60 seconds" in result.guidance.lower()
            or "seconds" in result.guidance.lower()
        )

    # -------------------------------------------------------------------------
    # Timeout Detection Tests
    # -------------------------------------------------------------------------

    def test_timeout_detection(self) -> None:
        """Test that 'timeout' in error message is classified as TimeoutError."""
        error = DDGSException("Request timeout while waiting")
        result = _classify_search_error(error)

        assert isinstance(result, MCPTimeoutError)
        assert result.category == ErrorCategory.NETWORK

    def test_timeout_detection_timed_out(self) -> None:
        """Test that 'timed out' is classified as TimeoutError."""
        error = DDGSException("Connection timed out")
        result = _classify_search_error(error)

        assert isinstance(result, MCPTimeoutError)

    def test_timeout_detection_time_out(self) -> None:
        """Test that 'time out' is classified as TimeoutError."""
        error = DDGSException("Request time out")
        result = _classify_search_error(error)

        assert isinstance(result, MCPTimeoutError)

    def test_timeout_with_query_context(self) -> None:
        """Test that timeout error includes query context when provided."""
        error = DDGSException("Connection timed out")
        result = _classify_search_error(error, query="python tutorial")

        assert isinstance(result, MCPTimeoutError)
        assert "python tutorial" in result.message

    def test_timeout_with_backend_context(self) -> None:
        """Test that timeout error includes backend context when provided."""
        error = DDGSException("Connection timed out")
        result = _classify_search_error(error, backend="brave")

        assert isinstance(result, MCPTimeoutError)
        assert "brave" in result.message

    def test_timeout_has_actionable_guidance(self) -> None:
        """Test that TimeoutError includes actionable guidance."""
        error = DDGSException("Request timeout")
        result = _classify_search_error(error)

        assert isinstance(result, MCPTimeoutError)
        assert any(
            phrase in result.guidance.lower()
            for phrase in ["simplify", "reducing", "try again"]
        )

    # -------------------------------------------------------------------------
    # Network Error Detection Tests
    # -------------------------------------------------------------------------

    def test_network_error_detection_connection(self) -> None:
        """Test that 'connection' errors are classified as NetworkError."""
        error = DDGSException("Connection failed: Unable to connect")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)
        assert result.category == ErrorCategory.NETWORK

    def test_network_error_detection_refused(self) -> None:
        """Test that 'refused' is classified as NetworkError."""
        error = DDGSException("Connection refused by remote host")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)

    def test_network_error_detection_dns(self) -> None:
        """Test that 'dns' is classified as NetworkError."""
        error = DDGSException("DNS lookup failed")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)

    def test_network_error_detection_resolve(self) -> None:
        """Test that 'resolve' is classified as NetworkError."""
        error = DDGSException("Unable to resolve hostname")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)

    def test_network_error_detection_unreachable(self) -> None:
        """Test that 'unreachable' is classified as NetworkError."""
        error = DDGSException("Network unreachable")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)

    def test_network_error_detection_no_internet(self) -> None:
        """Test that 'no internet' is classified as NetworkError."""
        error = DDGSException("No internet connection")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)

    def test_network_error_with_query_context(self) -> None:
        """Test that network error includes query context when provided."""
        error = DDGSException("Connection failed")
        result = _classify_search_error(error, query="test search")

        assert isinstance(result, NetworkError)
        assert "test search" in result.message

    def test_network_error_has_actionable_guidance(self) -> None:
        """Test that NetworkError includes actionable guidance."""
        error = DDGSException("Connection failed")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)
        assert any(
            phrase in result.guidance.lower()
            for phrase in ["internet", "network", "try again"]
        )

    # -------------------------------------------------------------------------
    # Service Unavailable Detection Tests
    # -------------------------------------------------------------------------

    def test_service_unavailable_detection_503(self) -> None:
        """Test that '503' in error message is classified as ServiceUnavailableError."""
        error = DDGSException("HTTP Error 503: Service Unavailable")
        result = _classify_search_error(error)

        assert isinstance(result, ServiceUnavailableError)
        assert result.category == ErrorCategory.SERVICE

    def test_service_unavailable_detection_unavailable(self) -> None:
        """Test that 'unavailable' is classified as ServiceUnavailableError."""
        error = DDGSException("Service unavailable")
        result = _classify_search_error(error)

        assert isinstance(result, ServiceUnavailableError)

    def test_service_unavailable_detection_maintenance(self) -> None:
        """Test that 'maintenance' is classified as ServiceUnavailableError."""
        error = DDGSException("Service under maintenance")
        result = _classify_search_error(error)

        assert isinstance(result, ServiceUnavailableError)

    def test_service_unavailable_detection_down(self) -> None:
        """Test that 'down' is classified as ServiceUnavailableError."""
        error = DDGSException("Service is down")
        result = _classify_search_error(error)

        assert isinstance(result, ServiceUnavailableError)

    def test_service_unavailable_has_actionable_guidance(self) -> None:
        """Test that ServiceUnavailableError includes actionable guidance."""
        error = DDGSException("503 Service Unavailable")
        result = _classify_search_error(error)

        assert isinstance(result, ServiceUnavailableError)
        assert "try again" in result.guidance.lower()
        assert "minutes" in result.guidance.lower()

    # -------------------------------------------------------------------------
    # Backend Error Detection Tests
    # -------------------------------------------------------------------------

    def test_backend_error_detection(self) -> None:
        """Test that 'backend' errors are classified as NetworkError."""
        error = DDGSException("Search backend error")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)
        assert "backend" in result.message.lower()

    def test_backend_error_has_fallback_guidance(self) -> None:
        """Test that backend error guidance mentions fallback behavior."""
        error = DDGSException("Backend API error")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)
        assert (
            "fallback" in result.guidance.lower()
            or "backend" in result.guidance.lower()
        )

    # -------------------------------------------------------------------------
    # Empty Results Detection Tests
    # -------------------------------------------------------------------------

    def test_empty_results_detection_no_results(self) -> None:
        """Test that 'no results' is classified as NetworkError."""
        error = DDGSException("No results returned")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)
        assert "no results" in result.message.lower()

    def test_empty_results_detection_empty(self) -> None:
        """Test that 'empty' is classified as NetworkError."""
        error = DDGSException("Empty response")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)

    def test_empty_results_detection_nothing_found(self) -> None:
        """Test that 'nothing found' is classified as NetworkError."""
        error = DDGSException("Nothing found")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)

    def test_empty_results_has_actionable_guidance(self) -> None:
        """Test that empty results error has actionable guidance."""
        error = DDGSException("No results returned")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)
        assert any(
            phrase in result.guidance.lower()
            for phrase in ["rephras", "broader", "spelling"]
        )

    # -------------------------------------------------------------------------
    # Generic Error Tests
    # -------------------------------------------------------------------------

    def test_generic_error_classified_as_network_error(self) -> None:
        """Test that unknown errors are classified as generic NetworkError."""
        error = DDGSException("Some unknown error occurred")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)
        assert result.category == ErrorCategory.NETWORK

    def test_generic_error_includes_original_message(self) -> None:
        """Test that generic error includes the original error message."""
        error = DDGSException("Something went wrong")
        result = _classify_search_error(error)

        assert "Something went wrong" in result.message

    def test_generic_error_has_actionable_guidance(self) -> None:
        """Test that generic errors have actionable guidance."""
        error = DDGSException("Unknown error")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)
        assert any(
            phrase in result.guidance.lower()
            for phrase in ["internet", "try again", "query"]
        )

    # -------------------------------------------------------------------------
    # Non-DDGSException Tests
    # -------------------------------------------------------------------------

    def test_non_ddgs_exception_classified(self) -> None:
        """Test that non-DDGSException errors are also classified."""
        error = Exception("Generic Python exception")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)

    def test_value_error_classified(self) -> None:
        """Test that ValueError is classified appropriately."""
        error = ValueError("Invalid value")
        result = _classify_search_error(error)

        assert isinstance(result, NetworkError)


# =============================================================================
# _validate_search_params Tests
# =============================================================================


class TestValidateSearchParams:
    """Tests for the _validate_search_params function."""

    # -------------------------------------------------------------------------
    # Valid Parameters Tests
    # -------------------------------------------------------------------------

    def test_valid_params_return_normalized_safesearch(self) -> None:
        """Test that valid params return the normalized safesearch value."""
        result = _validate_search_params("test query", 5, "moderate")
        assert result == "moderate"

    def test_valid_params_all_safesearch_values(self) -> None:
        """Test all valid safesearch values are accepted."""
        assert _validate_search_params("query", 5, "on") == "on"
        assert _validate_search_params("query", 5, "moderate") == "moderate"
        assert _validate_search_params("query", 5, "off") == "off"

    def test_valid_params_various_max_results(self) -> None:
        """Test various valid max_results values."""
        _validate_search_params("query", 1, "moderate")  # min
        _validate_search_params("query", 10, "moderate")  # common
        _validate_search_params("query", 100, "moderate")  # large

    # -------------------------------------------------------------------------
    # Invalid Query Tests
    # -------------------------------------------------------------------------

    def test_empty_query_raises_validation_error(self) -> None:
        """Test that empty query raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            _validate_search_params("", 5, "moderate")

        assert exc_info.value.category == ErrorCategory.VALIDATION
        assert "query" in exc_info.value.message.lower()

    def test_none_query_raises_validation_error(self) -> None:
        """Test that None query raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            _validate_search_params(None, 5, "moderate")  # type: ignore

        assert "query" in exc_info.value.message.lower()

    def test_non_string_query_raises_validation_error(self) -> None:
        """Test that non-string query raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            _validate_search_params(123, 5, "moderate")  # type: ignore

        assert exc_info.value.category == ErrorCategory.VALIDATION

    # -------------------------------------------------------------------------
    # Invalid max_results Tests
    # -------------------------------------------------------------------------

    def test_zero_max_results_raises_validation_error(self) -> None:
        """Test that zero max_results raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            _validate_search_params("query", 0, "moderate")

        assert "max_results" in exc_info.value.message.lower()

    def test_negative_max_results_raises_validation_error(self) -> None:
        """Test that negative max_results raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            _validate_search_params("query", -5, "moderate")

        assert "max_results" in exc_info.value.message.lower()

    def test_non_int_max_results_raises_validation_error(self) -> None:
        """Test that non-integer max_results raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            _validate_search_params("query", "five", "moderate")  # type: ignore

        assert "max_results" in exc_info.value.message.lower()

    def test_max_results_validation_error_has_guidance(self) -> None:
        """Test that max_results validation error has actionable guidance."""
        with pytest.raises(ValidationError) as exc_info:
            _validate_search_params("query", -1, "moderate")

        assert any(
            phrase in exc_info.value.guidance.lower()
            for phrase in ["positive", "valid", "example"]
        )

    # -------------------------------------------------------------------------
    # Invalid safesearch Tests
    # -------------------------------------------------------------------------

    def test_invalid_safesearch_returns_moderate(self) -> None:
        """Test that invalid safesearch defaults to 'moderate'."""
        result = _validate_search_params("query", 5, "invalid_value")
        assert result == "moderate"

    def test_safesearch_case_sensitivity(self) -> None:
        """Test that safesearch is case-sensitive (returns moderate for uppercase)."""
        # Current implementation treats 'ON' as invalid and returns 'moderate'
        result = _validate_search_params("query", 5, "ON")
        assert result == "moderate"


# =============================================================================
# _format_results_as_text Tests
# =============================================================================


class TestFormatResultsAsText:
    """Tests for the _format_results_as_text function."""

    def test_empty_results_returns_helpful_message(self) -> None:
        """Test that empty results return a helpful message."""
        result = _format_results_as_text([], "test query")

        assert "no results" in result.lower()
        assert "test query" in result

    def test_empty_results_mentions_possible_causes(self) -> None:
        """Test that empty results message mentions possible causes."""
        result = _format_results_as_text([], "test query")

        assert any(
            phrase in result.lower()
            for phrase in ["rate limit", "no matches", "network"]
        )

    def test_results_formatted_with_numbers(self) -> None:
        """Test that results are formatted with numbers."""
        results = [
            {
                "title": "Result 1",
                "url": "https://example1.com",
                "snippet": "Snippet 1",
            },
            {
                "title": "Result 2",
                "url": "https://example2.com",
                "snippet": "Snippet 2",
            },
        ]
        result = _format_results_as_text(results, "query")

        assert "1. Result 1" in result
        assert "2. Result 2" in result

    def test_results_include_url_and_summary(self) -> None:
        """Test that results include URL and summary."""
        results = [
            {"title": "Title", "url": "https://example.com", "snippet": "Description"},
        ]
        result = _format_results_as_text(results, "query")

        assert "URL: https://example.com" in result
        assert "Summary: Description" in result

    def test_results_count_header(self) -> None:
        """Test that results include count header."""
        results = [
            {"title": "R1", "url": "u1", "snippet": "s1"},
            {"title": "R2", "url": "u2", "snippet": "s2"},
            {"title": "R3", "url": "u3", "snippet": "s3"},
        ]
        result = _format_results_as_text(results, "query")

        assert "Found 3 search results" in result


# =============================================================================
# _try_fallback_search Tests
# =============================================================================


class TestTryFallbackSearch:
    """Tests for the _try_fallback_search function."""

    def test_fallback_skipped_for_rate_limit_error(self) -> None:
        """Test that fallback is skipped for RateLimitError."""
        rate_limit_error = RateLimitError("Rate limited")

        with pytest.raises(RateLimitError):
            _try_fallback_search(
                query="test",
                region="wt-wt",
                safesearch="moderate",
                max_results=5,
                timeout=15,
                original_error=rate_limit_error,
            )

    def test_fallback_skipped_for_backend_error(self) -> None:
        """Test that fallback is skipped for backend-specific errors."""
        backend_error = NetworkError("Backend search error")

        with pytest.raises(NetworkError) as exc_info:
            _try_fallback_search(
                query="test",
                region="wt-wt",
                safesearch="moderate",
                max_results=5,
                timeout=15,
                original_error=backend_error,
            )

        # The original error should be re-raised
        assert "backend" in exc_info.value.message.lower()

    @patch("duckduckgo_mcp.duckduckgo_search._execute_search")
    def test_fallback_succeeds(self, mock_execute: MagicMock) -> None:
        """Test successful fallback search."""
        mock_execute.return_value = [{"title": "Result", "url": "url", "snippet": "s"}]
        original_error = NetworkError("Primary search failed")

        results = _try_fallback_search(
            query="test",
            region="wt-wt",
            safesearch="moderate",
            max_results=5,
            timeout=15,
            original_error=original_error,
        )

        assert len(results) == 1
        mock_execute.assert_called_once_with(
            "test", "wt-wt", "moderate", 5, 15, "brave"
        )

    @patch("duckduckgo_mcp.duckduckgo_search._execute_search")
    def test_fallback_failure_raises_combined_error(
        self, mock_execute: MagicMock
    ) -> None:
        """Test that fallback failure raises combined error."""
        mock_execute.side_effect = DDGSException("Fallback also failed")
        original_error = NetworkError("Primary search failed")

        with pytest.raises(NetworkError) as exc_info:
            _try_fallback_search(
                query="test",
                region="wt-wt",
                safesearch="moderate",
                max_results=5,
                timeout=15,
                original_error=original_error,
            )

        # Error message should mention both backends
        assert "both backends" in exc_info.value.message.lower()
        assert "primary" in exc_info.value.message.lower()
        assert "fallback" in exc_info.value.message.lower()


# =============================================================================
# search_duckduckgo Error Handling Tests
# =============================================================================


class TestSearchDuckduckgoErrors:
    """Tests for error handling in the search_duckduckgo function."""

    def test_invalid_query_raises_validation_error(self) -> None:
        """Test that empty query raises ValidationError."""
        with pytest.raises(ValidationError):
            search_duckduckgo("")

    def test_invalid_max_results_raises_validation_error(self) -> None:
        """Test that invalid max_results raises ValidationError."""
        with pytest.raises(ValidationError):
            search_duckduckgo("test", max_results=-1)

    @patch("duckduckgo_mcp.duckduckgo_search._execute_search")
    def test_ddgs_exception_triggers_fallback_for_empty_results(
        self, mock_execute: MagicMock
    ) -> None:
        """Test that DDGSException with 'no results' triggers fallback search.

        Note: Errors classified with backend context contain 'backend' in the message,
        which skips fallback. However, 'no results' errors don't include backend context,
        so they will trigger fallback.
        """
        # First call fails with "no results" error (doesn't include backend in message)
        # Second call (fallback) succeeds
        mock_execute.side_effect = [
            DDGSException("No results found"),
            [{"title": "Result", "url": "url", "snippet": "s"}],
        ]

        results = search_duckduckgo("test query")

        assert len(results) == 1
        assert mock_execute.call_count == 2

    @patch("duckduckgo_mcp.duckduckgo_search._execute_search")
    def test_generic_ddgs_exception_skips_fallback_due_to_backend_in_message(
        self, mock_execute: MagicMock
    ) -> None:
        """Test that generic DDGSException skips fallback due to 'backend' in message.

        When errors are classified as generic (not matching any specific indicator),
        the resulting error message contains 'using backend' which triggers the fallback
        skip logic.
        """
        # Use an error message that doesn't match any specific indicators
        # so it falls through to the generic case (which includes backend context)
        mock_execute.side_effect = DDGSException("Something unexpected happened xyz123")

        with pytest.raises(NetworkError) as exc_info:
            search_duckduckgo("test query")

        # Should only have one call (no fallback due to 'backend' in classified message)
        assert mock_execute.call_count == 1
        assert "backend" in exc_info.value.message.lower()

    @patch("duckduckgo_mcp.duckduckgo_search._execute_search")
    def test_rate_limit_error_propagates(self, mock_execute: MagicMock) -> None:
        """Test that rate limit error propagates without fallback."""
        mock_execute.side_effect = DDGSException("429 Rate Limited")

        with pytest.raises(RateLimitError):
            search_duckduckgo("test query")

        # Should only have one call (no fallback for rate limits)
        assert mock_execute.call_count == 1

    @patch("duckduckgo_mcp.duckduckgo_search._execute_search")
    def test_mcp_error_reraises(self, mock_execute: MagicMock) -> None:
        """Test that MCPError subclasses are re-raised as-is."""
        mock_execute.side_effect = ValidationError("Already validated error")

        with pytest.raises(ValidationError):
            search_duckduckgo("test query")

    @patch("duckduckgo_mcp.duckduckgo_search._execute_search")
    def test_unexpected_exception_classified(self, mock_execute: MagicMock) -> None:
        """Test that unexpected exceptions are classified and raised."""
        mock_execute.side_effect = RuntimeError("Unexpected error")

        with pytest.raises(MCPError):
            search_duckduckgo("test query")


# =============================================================================
# duckduckgo_search MCP Tool Error Handling Tests
# =============================================================================


class TestDuckduckgoSearchToolErrors:
    """Tests for error handling in the duckduckgo_search MCP tool.

    Note: duckduckgo_search is wrapped by @mcp.tool() decorator, so we access
    the underlying function via duckduckgo_search.fn to test it directly.
    """

    def test_missing_query_raises_validation_error(self) -> None:
        """Test that missing query raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            duckduckgo_search.fn(query="")

        assert "query" in exc_info.value.message.lower()
        assert exc_info.value.category == ErrorCategory.VALIDATION

    def test_missing_query_has_actionable_guidance(self) -> None:
        """Test that missing query error has actionable guidance."""
        with pytest.raises(ValidationError) as exc_info:
            duckduckgo_search.fn(query="")

        assert "example" in exc_info.value.guidance.lower()

    def test_invalid_max_results_string_raises_validation_error(self) -> None:
        """Test that non-convertible max_results string raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            duckduckgo_search.fn(query="test", max_results="not_a_number")  # type: ignore

        assert "max_results" in exc_info.value.message.lower()

    def test_max_results_string_number_coerced(self) -> None:
        """Test that string number max_results is coerced to int."""
        with patch("duckduckgo_mcp.duckduckgo_search.search_duckduckgo") as mock_search:
            mock_search.return_value = []
            # This should work - "5" should be converted to 5
            duckduckgo_search.fn(query="test", max_results="5")  # type: ignore
            mock_search.assert_called_once()

    def test_zero_max_results_raises_validation_error(self) -> None:
        """Test that zero max_results raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            duckduckgo_search.fn(query="test", max_results=0)

        assert "max_results" in exc_info.value.message.lower()

    def test_negative_max_results_raises_validation_error(self) -> None:
        """Test that negative max_results raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            duckduckgo_search.fn(query="test", max_results=-5)

        assert "max_results" in exc_info.value.message.lower()

    def test_invalid_output_format_raises_validation_error(self) -> None:
        """Test that invalid output_format raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            duckduckgo_search.fn(query="test", output_format="xml")

        assert "output_format" in exc_info.value.message.lower()
        assert "json" in exc_info.value.guidance.lower()
        assert "text" in exc_info.value.guidance.lower()

    def test_invalid_output_format_shows_provided_value(self) -> None:
        """Test that invalid output_format error shows the provided value."""
        with pytest.raises(ValidationError) as exc_info:
            duckduckgo_search.fn(query="test", output_format="invalid_format")

        assert "invalid_format" in exc_info.value.guidance

    @patch("duckduckgo_mcp.duckduckgo_search.search_duckduckgo")
    def test_mcp_error_propagates(self, mock_search: MagicMock) -> None:
        """Test that MCPError exceptions propagate."""
        mock_search.side_effect = RateLimitError("Rate limited")

        with pytest.raises(RateLimitError):
            duckduckgo_search.fn(query="test")

    @patch("duckduckgo_mcp.duckduckgo_search.search_duckduckgo")
    def test_network_error_propagates(self, mock_search: MagicMock) -> None:
        """Test that NetworkError propagates."""
        mock_search.side_effect = NetworkError("Network issue")

        with pytest.raises(NetworkError):
            duckduckgo_search.fn(query="test")

    @patch("duckduckgo_mcp.duckduckgo_search.search_duckduckgo")
    def test_successful_json_output(self, mock_search: MagicMock) -> None:
        """Test successful search returns JSON format by default."""
        mock_search.return_value = [
            {"title": "Result", "url": "https://example.com", "snippet": "desc"}
        ]

        result = duckduckgo_search.fn(query="test")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Result"

    @patch("duckduckgo_mcp.duckduckgo_search.search_duckduckgo")
    def test_successful_text_output(self, mock_search: MagicMock) -> None:
        """Test successful search returns text format when specified."""
        mock_search.return_value = [
            {"title": "Result", "url": "https://example.com", "snippet": "desc"}
        ]

        result = duckduckgo_search.fn(query="test", output_format="text")

        assert isinstance(result, str)
        assert "Result" in result


# =============================================================================
# Error Context and Guidance Tests
# =============================================================================


class TestSearchErrorContextAndGuidance:
    """Tests for error context and actionable guidance in search errors."""

    def test_classify_error_with_all_context(self) -> None:
        """Test error classification with all context provided."""
        error = DDGSException("Connection timed out")
        result = _classify_search_error(
            error, query="python tutorial", backend="duckduckgo"
        )

        assert "python tutorial" in result.message
        assert "duckduckgo" in result.message

    def test_rate_limit_guidance_is_actionable(self) -> None:
        """Test that rate limit guidance provides actionable steps."""
        error = DDGSException("429 Too Many Requests")
        result = _classify_search_error(error)

        # Should have multiple actionable items
        assert result.guidance.count("•") >= 3 or result.guidance.count("-") >= 3

    def test_timeout_guidance_is_actionable(self) -> None:
        """Test that timeout guidance provides actionable steps."""
        error = DDGSException("Request timed out")
        result = _classify_search_error(error)

        # Should mention possible causes and solutions
        assert "try" in result.guidance.lower()

    def test_network_error_guidance_mentions_internet(self) -> None:
        """Test that network error guidance mentions checking internet."""
        error = DDGSException("Connection failed")
        result = _classify_search_error(error)

        assert "internet" in result.guidance.lower()

    def test_service_unavailable_guidance_mentions_retry(self) -> None:
        """Test that service unavailable guidance mentions retry."""
        error = DDGSException("503 Service Unavailable")
        result = _classify_search_error(error)

        assert (
            "try again" in result.guidance.lower() or "retry" in result.guidance.lower()
        )


# =============================================================================
# Integration Tests
# =============================================================================


class TestSearchErrorIntegration:
    """Integration tests for error handling flow."""

    @patch("duckduckgo_mcp.duckduckgo_search._execute_search")
    def test_full_error_flow_from_ddgs_to_mcp_error(
        self, mock_execute: MagicMock
    ) -> None:
        """Test the full error flow from DDGS exception to MCPError."""
        mock_execute.side_effect = DDGSException("429 Rate Limited")

        with pytest.raises(MCPError) as exc_info:
            duckduckgo_search.fn(query="test")

        # Should be a RateLimitError with proper category
        assert isinstance(exc_info.value, RateLimitError)
        assert exc_info.value.category == ErrorCategory.SERVICE
        # Should have actionable guidance
        assert len(exc_info.value.guidance) > 0

    @patch("duckduckgo_mcp.duckduckgo_search._execute_search")
    def test_fallback_error_flow(self, mock_execute: MagicMock) -> None:
        """Test error flow when both primary and fallback fail.

        Uses 'no results' errors which don't include backend in the message,
        allowing fallback to be attempted.
        """
        # Both calls fail with "no results" errors (triggers fallback, no 'backend' in message)
        mock_execute.side_effect = [
            DDGSException("No results returned"),
            DDGSException("No results from fallback"),
        ]

        with pytest.raises(NetworkError) as exc_info:
            search_duckduckgo("test query")

        # Should mention both backends
        assert "both backends" in exc_info.value.message.lower()
        # Should have combined guidance
        assert len(exc_info.value.guidance) > 0

    def test_validation_errors_prevent_search(self) -> None:
        """Test that validation errors prevent search from being executed."""
        with patch("duckduckgo_mcp.duckduckgo_search._execute_search") as mock:
            with pytest.raises(ValidationError):
                duckduckgo_search.fn(query="")

            # Search should never be called due to validation failure
            mock.assert_not_called()
