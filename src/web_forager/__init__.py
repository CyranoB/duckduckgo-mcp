"""Web Forager - A search-and-fetch toolkit for AI agents via MCP and standalone Agent Skills."""

from .duckduckgo_search import duckduckgo_search, search_duckduckgo
from .web_fetch import fetch_url, jina_fetch, web_fetch
from .server import mcp

try:
    # Get version from setuptools_scm-generated file
    from ._version import version as __version__
except ImportError:
    # Fallback when package is installed without setuptools_scm
    from importlib.metadata import version as _version

    __version__ = _version("web-forager")

__all__ = [
    "mcp",
    "duckduckgo_search",
    "search_duckduckgo",
    "web_fetch",
    "jina_fetch",
    "fetch_url",
    "__version__",
]
