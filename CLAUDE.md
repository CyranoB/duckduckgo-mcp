# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a DuckDuckGo Model Context Protocol (MCP) server that provides two main capabilities:
1. Searching the web using DuckDuckGo
2. Fetching and converting web content to markdown using Jina Reader

The server implements the MCP protocol, enabling LLMs to perform web searches and retrieve content through a standardized interface.

The implementation uses the FastMCP library to create an MCP server that communicates via STDIO transport in a clean, Pythonic way.

## Commands

### Installation

```bash
# Install dependencies for development
uv pip install -e .

# With development tools
uv pip install -e ".[dev]"
```

### Running the MCP Server

```bash
# Run the MCP server with the CLI
duckduckgo-mcp serve

# Run with debug logging
duckduckgo-mcp serve --debug

# Add to Claude Code
claude mcp add duckduckgo -- duckduckgo-mcp serve
```

### Testing

```bash
# Test the search functionality from the command line
duckduckgo-mcp search "your search query" --max-results 5 --safesearch moderate

# Test the URL fetching functionality from the command line
duckduckgo-mcp fetch "https://example.com" --format markdown --with-images

# Get a URL in JSON format
duckduckgo-mcp fetch "https://example.com" --format json

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

The project has a modular architecture:

1. **CLI Entry Point**: `cli.py` provides the command-line interface with subcommands for serving, searching, fetching URLs, and displaying version information.

2. **Search Implementation**: `duckduckgo_search.py` contains:
   - `search_duckduckgo()`: Core function that uses the duckduckgo-search library to query DuckDuckGo and return structured results
   - `duckduckgo_search()`: MCP-decorated wrapper function that adds validation and error handling

3. **URL Fetch Implementation**: `jina_fetch.py` contains:
   - `fetch_url()`: Core function that uses the Jina Reader API to fetch and convert web content to markdown or JSON
   - `jina_fetch()`: MCP-decorated wrapper function that adds validation and error handling

4. **MCP Tool Registration**: The `@mcp.tool()` decorator registers both functions as MCP tools, making them available to LLMs through the MCP protocol.

5. **Multiple Operation Modes**:
   - STDIO mode via `duckduckgo-mcp serve` (default transport)
   - CLI testing modes via `duckduckgo-mcp search` and `duckduckgo-mcp fetch` commands

6. **Error Handling**:
   - Parameter validation for all inputs
   - Specific exception handling for HTTP requests
   - Graceful error responses with meaningful messages

## File Structure

- `cli.py`: Command-line interface implementation
- `duckduckgo_search.py`: Search functionality using DuckDuckGo
- `jina_fetch.py`: URL fetching functionality using Jina Reader
- `__init__.py`: Package exports and version information
- `__main__.py`: Entry point for running as a module
- `_version.py`: Generated version information (from setuptools_scm)

## API

The MCP server exposes two tools:

### Tool 1: Search

- **Tool Name**: `duckduckgo_search` (or `search` when using the CLI entry point)
- **Description**: Search the web using DuckDuckGo

#### Parameters

- `query` (string, required): The search query
- `max_results` (integer, optional, default: 5): Maximum number of search results to return
- `safesearch` (string, optional, default: "moderate"): Safe search setting ("on", "moderate", or "off")

#### Response

A list of dictionaries containing search results with:
- `title`: Result title
- `url`: Result URL
- `snippet`: Text snippet from the search result

### Tool 2: URL Fetch

- **Tool Name**: `jina_fetch`
- **Description**: Fetch a URL and convert it to markdown or JSON using Jina Reader

#### Parameters

- `url` (string, required): The URL to fetch and convert
- `format` (string, optional, default: "markdown"): Output format - "markdown" or "json"
- `max_length` (integer, optional): Maximum content length to return (None for no limit)
- `with_images` (boolean, optional, default: false): Whether to include image alt text generation

#### Response

For markdown format: A string containing the markdown content
For JSON format: A dictionary with the following structure:
- `url`: The fetched URL
- `title`: Page title
- `content`: Page content in markdown format