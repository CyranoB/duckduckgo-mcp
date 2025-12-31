"""DuckDuckGo MCP Server - A Model Context Protocol server for web search and content retrieval."""

from .duckduckgo_search import duckduckgo_search, search_duckduckgo
from .jina_fetch import fetch_url, jina_fetch
from .server import mcp

try:
    # Get version from setuptools_scm-generated file
    from ._version import version as __version__
except ImportError:
    # Fallback when package is installed without setuptools_scm
    from importlib.metadata import version as _version

    __version__ = _version("duckduckgo-mcp")

__all__ = [
    "mcp",
    "duckduckgo_search",
    "search_duckduckgo",
    "jina_fetch",
    "fetch_url",
    "__version__",
]
