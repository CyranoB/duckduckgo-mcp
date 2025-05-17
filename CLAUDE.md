# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a DuckDuckGo Model Context Protocol (MCP) server that allows searching the web using DuckDuckGo. The server implements the MCP protocol, enabling LLMs to perform web searches through a standardized interface.

The implementation uses the FastMCP library to create an MCP server that communicates via STDIO transport in a clean, Pythonic way.

## Commands

### Installation

```bash
# Install dependencies
uv pip install -r requirements.txt
```

### Running the MCP Server

```bash
# Run using the mcp command line tool (STDIO transport)
python -m mcp run duckduckgo_search.py

# Run the script directly (STDIO transport)
python duckduckgo_search.py

# Run with uvx (HTTP transport)
uv pip install -e ".[uvx]"
uvx
```

### Testing

```bash
# Test the search functionality from the command line
python duckduckgo_search.py --cli "your search query" [max_results]
```

## Architecture

The project has a simple architecture:

1. **FastMCP Server**: The `duckduckgo_search.py` file creates an MCP server using the FastMCP library.

2. **Search Function**: The `search_duckduckgo()` function handles:
   - Formatting search queries
   - Making HTTP requests to DuckDuckGo's HTML interface
   - Parsing results using BeautifulSoup
   - Returning structured data with titles, URLs, and snippets

3. **MCP Tool Registration**: The `@mcp.tool()` decorator registers the `duckduckgo_search` function as an MCP tool, making it available to LLMs through the MCP protocol.

4. **Multiple Operation Modes**:
   - STDIO mode (default when run directly)
   - HTTP mode (when run with uvx or uvicorn)
   - CLI testing mode (when run with `--cli` flag)

5. **Error Handling**:
   - Parameter validation for query and max_results
   - Specific exception handling for HTTP requests
   - Graceful error responses

## API

The MCP server exposes a single tool:

- **Tool Name**: `duckduckgo_search`
- **Description**: Search the web using DuckDuckGo

### Parameters

- `query` (string, required): The search query
- `max_results` (integer, optional, default: 5): Maximum number of search results to return

### Response

A list of dictionaries containing search results with:
- `title`: Result title
- `url`: Result URL
- `snippet`: Text snippet from the search result