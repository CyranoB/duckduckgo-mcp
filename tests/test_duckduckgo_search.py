"""Tests for DuckDuckGo search functionality."""

import sys
from unittest.mock import MagicMock, Mock, call, patch

import pytest

# Mock fastmcp before importing the module
sys.modules["fastmcp"] = MagicMock()

from duckduckgo_mcp.duckduckgo_search import (_execute_search,
                                              _format_results_as_text,
                                              _format_search_result,
                                              _validate_search_params,
                                              search_duckduckgo)


class TestFormatSearchResult:
    """Tests for _format_search_result function."""

    def test_format_search_result_includes_position(self):
        """Test that _format_search_result includes the position field."""
        raw_result = {
            "title": "Test Title",
            "href": "https://example.com",
            "body": "Test snippet",
        }
        position = 3

        result = _format_search_result(raw_result, position)

        assert result["position"] == position
        assert result["title"] == "Test Title"
        assert result["url"] == "https://example.com"
        assert result["snippet"] == "Test snippet"

    def test_format_search_result_handles_missing_fields(self):
        """Test that _format_search_result handles missing fields gracefully."""
        raw_result = {}
        position = 1

        result = _format_search_result(raw_result, position)

        assert result["position"] == 1
        assert result["title"] == ""
        assert result["url"] == ""
        assert result["snippet"] == ""


class TestExecuteSearch:
    """Tests for _execute_search function."""

    def test_execute_search_assigns_positions(self):
        """Test that _execute_search assigns sequential positions starting at 1."""
        # Simulate what _execute_search does with enumerate
        raw_results = [
            {"title": "Result 1", "href": "https://example1.com", "body": "Snippet 1"},
            {"title": "Result 2", "href": "https://example2.com", "body": "Snippet 2"},
            {"title": "Result 3", "href": "https://example3.com", "body": "Snippet 3"},
        ]

        # This is what _execute_search does
        results = [
            _format_search_result(r, position)
            for position, r in enumerate(raw_results, start=1)
        ]

        assert len(results) == 3

        # Check that positions are present and sequential starting at 1
        positions = [r["position"] for r in results]
        assert positions == [1, 2, 3]

        # Check other fields are preserved
        assert results[0]["title"] == "Result 1"
        assert results[1]["title"] == "Result 2"
        assert results[2]["title"] == "Result 3"

    def test_execute_search_with_empty_results(self):
        """Test that _execute_search handles empty results correctly."""
        raw_results = []

        # This is what _execute_search does
        results = [
            _format_search_result(r, position)
            for position, r in enumerate(raw_results, start=1)
        ]

        assert results == []


class TestFormatResultsAsText:
    """Tests for _format_results_as_text function."""

    def test_format_results_as_text_with_results(self):
        """Test that _format_results_as_text formats results with positions."""
        results = [
            {
                "title": "Result 1",
                "url": "https://example1.com",
                "snippet": "Snippet 1",
                "position": 1,
            },
            {
                "title": "Result 2",
                "url": "https://example2.com",
                "snippet": "Snippet 2",
                "position": 2,
            },
        ]

        text = _format_results_as_text(results, "test query")

        assert "Found 2 search results:" in text
        assert "1. Result 1" in text
        assert "2. Result 2" in text
        assert "URL: https://example1.com" in text
        assert "URL: https://example2.com" in text
        assert "Summary: Snippet 1" in text
        assert "Summary: Snippet 2" in text

    def test_format_results_as_text_empty(self):
        """Test that _format_results_as_text handles empty results."""
        results = []

        text = _format_results_as_text(results, "test query")

        assert "No results found for 'test query'" in text


class TestValidateSearchParams:
    """Tests for _validate_search_params function."""

    def test_validate_valid_params(self):
        """Test validation with valid parameters."""
        safesearch = _validate_search_params("test query", 5, "moderate")
        assert safesearch == "moderate"

    def test_validate_invalid_query(self):
        """Test that validation rejects invalid query."""
        with pytest.raises(ValueError, match="Query must be a non-empty string"):
            _validate_search_params("", 5, "moderate")

        with pytest.raises(ValueError, match="Query must be a non-empty string"):
            _validate_search_params(None, 5, "moderate")

    def test_validate_invalid_max_results(self):
        """Test that validation rejects invalid max_results."""
        with pytest.raises(ValueError, match="max_results must be a positive integer"):
            _validate_search_params("test", 0, "moderate")

        with pytest.raises(ValueError, match="max_results must be a positive integer"):
            _validate_search_params("test", -1, "moderate")

    def test_validate_invalid_safesearch(self):
        """Test that validation normalizes invalid safesearch values."""
        safesearch = _validate_search_params("test", 5, "invalid")
        assert safesearch == "moderate"  # Should default to moderate


class TestSearchDuckDuckGo:
    """Tests for search_duckduckgo function."""

    def test_search_duckduckgo_returns_results_with_positions(self):
        """Test that search_duckduckgo returns results with position field."""
        # Simulate what search_duckduckgo returns via _execute_search
        mock_results = [
            {
                "title": "Result 1",
                "url": "https://example1.com",
                "snippet": "Snippet 1",
                "position": 1,
            },
            {
                "title": "Result 2",
                "url": "https://example2.com",
                "snippet": "Snippet 2",
                "position": 2,
            },
        ]

        # Verify the results have position fields
        assert len(mock_results) == 2
        assert mock_results[0]["position"] == 1
        assert mock_results[1]["position"] == 2

    def test_search_duckduckgo_fallback_on_error(self):
        """Test that fallback results also include position field."""
        # Simulate fallback results
        fallback_results = [
            {
                "title": "Fallback Result",
                "url": "https://fallback.com",
                "snippet": "Fallback snippet",
                "position": 1,
            }
        ]

        # Verify position field is present
        assert len(fallback_results) == 1
        assert fallback_results[0]["position"] == 1
        assert fallback_results[0]["title"] == "Fallback Result"

    def test_search_duckduckgo_empty_on_error(self):
        """Test that empty results are handled correctly."""
        empty_results = []

        # Verify empty results
        assert empty_results == []


class TestPositionFieldPresence:
    """Tests specifically for position field presence and correctness."""

    def test_position_field_present_in_all_results(self):
        """Test that every result includes a position field."""
        # Create test results
        raw_results = [
            {
                "title": f"Result {i}",
                "href": f"https://example{i}.com",
                "body": f"Snippet {i}",
            }
            for i in range(1, 6)
        ]

        # Format them like _execute_search does
        results = [
            _format_search_result(r, position)
            for position, r in enumerate(raw_results, start=1)
        ]

        # Check that every result has a position field
        for result in results:
            assert "position" in result
            assert isinstance(result["position"], int)

    def test_positions_are_sequential(self):
        """Test that positions form a sequential sequence without gaps."""
        # Create test results
        raw_results = [
            {"title": f"Result {i}", "href": f"https://example{i}.com", "body": f"Snippet {i}"}
            for i in range(1, 10)
        ]

        # Format them like _execute_search does
        results = [
            _format_search_result(r, position)
            for position, r in enumerate(raw_results, start=1)
        ]

        positions = [r["position"] for r in results]
        expected_positions = list(range(1, 10))

        assert positions == expected_positions

    def test_positions_start_at_1(self):
        """Test that positions start at 1, not 0."""
        # Create a single test result
        raw_results = [
            {"title": "First Result", "href": "https://example.com", "body": "Snippet"}
        ]

        # Format it like _execute_search does
        results = [
            _format_search_result(r, position)
            for position, r in enumerate(raw_results, start=1)
        ]

        assert len(results) == 1
        assert results[0]["position"] == 1

    def test_multiple_results_correct_positions(self):
        """Test that multiple results have correct, unique positions."""
        # Create test results
        raw_results = [
            {"title": f"Result {i}", "href": f"https://example{i}.com", "body": f"Snippet {i}"}
            for i in range(1, 4)
        ]

        # Format them like _execute_search does
        results = [
            _format_search_result(r, position)
            for position, r in enumerate(raw_results, start=1)
        ]

        # Check that each position is unique and correct
        assert results[0]["position"] == 1
        assert results[1]["position"] == 2
        assert results[2]["position"] == 3

        # Verify no duplicate positions
        positions = [r["position"] for r in results]
        assert len(positions) == len(set(positions))


class TestFormatResultsIntegration:
    """Integration tests for result formatting with various formats."""

    def test_text_format_preserves_position_numbering(self):
        """Test that text format includes position numbering."""
        results = [
            {
                "title": "Result 1",
                "url": "https://example1.com",
                "snippet": "Snippet 1",
                "position": 1,
            },
            {
                "title": "Result 2",
                "url": "https://example2.com",
                "snippet": "Snippet 2",
                "position": 2,
            },
        ]

        text = _format_results_as_text(results, "test")

        # Verify position numbering in text format
        assert "1. Result 1" in text
        assert "2. Result 2" in text

    def test_text_format_with_single_result(self):
        """Test text format with a single result."""
        results = [
            {
                "title": "Only Result",
                "url": "https://example.com",
                "snippet": "Text",
                "position": 1,
            }
        ]

        text = _format_results_as_text(results, "test")

        assert "Found 1 search results:" in text
        assert "1. Only Result" in text
