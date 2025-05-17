# DuckDuckGo MCP Server

[![PyPI](https://img.shields.io/pypi/v/duckduckgo-mcp?style=flat-square)](https://pypi.org/project/duckduckgo-mcp/)
[![Python Version](https://img.shields.io/pypi/pyversions/duckduckgo-mcp?style=flat-square)](https://pypi.org/project/duckduckgo-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server that allows searching the web using DuckDuckGo.

## Features

- Search the web using DuckDuckGo
- Return structured results with titles, URLs, and snippets
- Configurable number of results
- Implemented using FastMCP library with STDIO transport

## Installation

### From PyPI (recommended)

```bash
uv pip install duckduckgo-mcp
```

### From source

1. Clone this repository
2. Install with uv:

```bash
# Basic installation
uv pip install -e .

# With uvx support
uv pip install -e ".[uvx]"

# With uvicorn support
uv pip install -e ".[uvicorn]"
```

## Development

### Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setting up development environment

1. Clone the repository:
   ```bash
   git clone https://github.com/CyranoB/duckduckgo-mcp.git
   cd duckduckgo-mcp
   ```

2. Create and activate a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Unix/macOS
   # Or on Windows: .venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   uv pip install -e ".[dev]"
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

## Contributing

Contributions are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

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

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/CyranoB/duckduckgo-mcp/issues).