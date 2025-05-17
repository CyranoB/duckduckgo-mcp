"""DuckDuckGo MCP Server - A Model Context Protocol server for web search."""

from .duckduckgo_search import duckduckgo_search, search_duckduckgo

try:
    # Get version from setuptools_scm-generated file
    from ._version import version as __version__
except ImportError:
    # Fallback for development or not installed with setuptools_scm
    try:
        # Use importlib.metadata when the package is installed
        from importlib.metadata import version as _version
        __version__ = _version("duckduckgo-mcp")
    except ImportError:
        # Fallback if importlib.metadata is not available (Python < 3.8)
        __version__ = "0.1.0"

__all__ = ["duckduckgo_search", "search_duckduckgo", "__version__"]
