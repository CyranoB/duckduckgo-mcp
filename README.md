# DuckDuckGo MCP Server

A Model Context Protocol (MCP) server that allows searching the web using DuckDuckGo.

## Features

- Search the web using DuckDuckGo
- Return structured results with titles, URLs, and snippets
- Configurable number of results
- Implemented using FastMCP library with STDIO transport

## Installation

1. Clone this repository
2. Install dependencies:

```bash
uv pip install -r requirements.txt
```

## Usage

### Running the MCP Server

#### Option 1: STDIO Transport (Default)

```bash
# Using the mcp CLI tool
python -m mcp run duckduckgo_search.py

# Or run the script directly
python duckduckgo_search.py
```

The STDIO transport protocol is ideal for integrations with LLMs and other tools that communicate over standard input/output.

#### Option 2: Using uvx (or other ASGI servers)

```bash
# Install required dependencies
uv pip install -e ".[uvx]"  # or ".[uvicorn]" for uvicorn

# Run with uvx
uvx

# Or run with uvicorn
uvicorn asgi:app
```

This starts the server with a HTTP transport, making it accessible via web requests.

### Command Line Testing

You can test the search functionality directly from the command line:

```bash
python duckduckgo_search.py --cli "your search query" [max_results]
```

This will output the search results as JSON directly to your terminal.

### Integration with LLM Tools

This MCP server can be used with any LLM tool that supports the Model Context Protocol over the STDIO transport:

```bash
# Example using Claude Code
claude code --mcp duckduckgo_search.py
```

Then you can ask the LLM to search the web using DuckDuckGo.

## API

The MCP server exposes a single tool:

- **Tool Name**: `duckduckgo_search`
- **Description**: Search the web using DuckDuckGo

### Parameters

- `query` (string, required): The search query
- `max_results` (integer, optional, default: 5): Maximum number of search results to return

### Response

```json
{
  "results": [
    {
      "title": "Result title",
      "url": "https://example.com",
      "snippet": "Text snippet from the search result"
    },
    ...
  ]
}
```
