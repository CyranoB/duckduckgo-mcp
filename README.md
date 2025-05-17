# DuckDuckGo MCP Server

[![PyPI](https://img.shields.io/pypi/v/duckduckgo-mcp?style=flat-square)](https://pypi.org/project/duckduckgo-mcp/)
[![Python Version](https://img.shields.io/pypi/pyversions/duckduckgo-mcp?style=flat-square)](https://pypi.org/project/duckduckgo-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/duckduckgo-mcp/month)](https://pepy.tech/project/duckduckgo-mcp)

A Model Context Protocol (MCP) server that allows searching the web using DuckDuckGo. This package provides an easy way to integrate DuckDuckGo search functionality into your Python applications and LLM workflows.

## Features

- Search the web using DuckDuckGo
- Return structured results with titles, URLs, and snippets
- Configurable number of results
- Implemented using FastMCP library with STDIO transport

## Installation

### Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Install from PyPI (recommended)

```bash
# Using uv (recommended)
uv pip install duckduckgo-mcp

# Or using pip
pip install duckduckgo-mcp
```

### Install with UVX (for Claude Desktop)

```bash
# Install UVX if you haven't already
pip install uvx

# Install the DuckDuckGo MCP package
uvx install duckduckgo-mcp
```

### Install from source

For development or to get the latest changes:

```bash
# Clone the repository
git clone https://github.com/CyranoB/duckduckgo-mcp.git
cd duckduckgo-mcp

# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

## Usage

### Starting the Server (STDIO Mode)

```bash
# Start the server in STDIO mode (for use with MCP clients like Claude)
duckduckgo-mcp serve

# Enable debug logging
duckduckgo-mcp serve --debug
```

### Testing the Search Tool

You can test the search functionality directly from the command line:

```bash
# Search DuckDuckGo
duckduckgo-mcp search "your search query" --max-results 5
```

### Integration with LLM Tools

This MCP server is designed to work with any LLM tool that supports the Model Context Protocol (MCP).

#### Using with Claude

1. Install the package using one of the methods above

2. Use it with Claude:
   ```bash
   claude code --mcp duckduckgo-mcp
   ```
   
   Or with the full path:
   ```bash
   claude code --mcp $(which duckduckgo-mcp)
   ```

#### MCP Integration

When using with an MCP client (like Claude), the server exposes a single tool:

```python
@mcp.tool()
def search(query: str, max_results: int = 5) -> list:
    """Search DuckDuckGo for the given query.
    
    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 5)
        
    Returns:
        List of search results with title, url, and snippet for each result
    """
```

Example usage in an MCP client:

```python
# This is handled automatically by the MCP client
results = search("Python programming", max_results=3)
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

## Contributing

Contributions are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/CyranoB/duckduckgo-mcp/issues).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.