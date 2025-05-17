# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a DuckDuckGo Model Context Protocol (MCP) server that allows searching the web using DuckDuckGo. The server implements the MCP protocol, enabling LLMs to perform web searches through a standardized interface.

The implementation uses the FastMCP library to create an MCP server that communicates via STDIO or HTTP transport in a clean, Pythonic way.

## Commands

### Installation

```bash
# Install dependencies for development
uv pip install -e .

# With uvx support
uv pip install -e ".[uvx]"

# With development tools
uv pip install -e ".[dev]"
```

### Running the MCP Server

```bash
# Run the MCP server with the CLI (preferred method)
duckduckgo-mcp serve

# Run with debug logging
duckduckgo-mcp serve --debug

# Run with UVX (HTTP transport)
uvx

# Add to Claude Code
claude mcp add duckduckgo -- uvx --python=3.10 duckduckgo-mcp serve
```

### Testing

```bash
# Test the search functionality from the command line
duckduckgo-mcp search "your search query" --max-results 5

# Display version information
duckduckgo-mcp version

# Run tests with pytest (if tests are added)
pytest
```

### Development Tasks

```bash
# Format code with black
black src

# Sort imports
isort src

# Run type checking
mypy src

# Run test coverage
pytest --cov=duckduckgo_mcp
```

## Architecture

The project has a simple architecture:

1. **CLI Entry Point**: `cli.py` provides the command-line interface with subcommands for serving, searching, and displaying version information.

2. **Search Implementation**: `duckduckgo_search.py` contains:
   - `search_duckduckgo()`: Core function that formats queries, makes HTTP requests to DuckDuckGo's HTML interface, parses results using BeautifulSoup, and returns structured data
   - `duckduckgo_search()`: MCP-decorated wrapper function that adds validation and error handling

3. **MCP Tool Registration**: The `@mcp.tool()` decorator registers the search function as an MCP tool, making it available to LLMs through the MCP protocol.

4. **Multiple Operation Modes**:
   - STDIO mode via `duckduckgo-mcp serve` (default transport)
   - HTTP mode via `uvx` (requires [uvx] extra dependencies)
   - CLI testing mode via `duckduckgo-mcp search` command

5. **Error Handling**:
   - Parameter validation for query and max_results
   - Specific exception handling for HTTP requests
   - Graceful error responses

## File Structure

- `cli.py`: Command-line interface implementation
- `duckduckgo_search.py`: Core search functionality
- `__init__.py`: Package exports and version information
- `__main__.py`: Entry point for running as a module
- `asgi.py`: ASGI application for HTTP transport (uvx/uvicorn)
- `_version.py`: Generated version information (from setuptools_scm)

## API

The MCP server exposes a single tool:

- **Tool Name**: `duckduckgo_search` (or `search` when using the CLI entry point)
- **Description**: Search the web using DuckDuckGo

### Parameters

- `query` (string, required): The search query
- `max_results` (integer, optional, default: 5): Maximum number of search results to return

### Response

A list of dictionaries containing search results with:
- `title`: Result title
- `url`: Result URL
- `snippet`: Text snippet from the search result