# DuckDuckGo MCP Server

[![PyPI](https://img.shields.io/pypi/v/duckduckgo-mcp?style=flat-square)](https://pypi.org/project/duckduckgo-mcp/)
[![Python Version](https://img.shields.io/pypi/pyversions/duckduckgo-mcp?style=flat-square)](https://pypi.org/project/duckduckgo-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/duckduckgo-mcp/month)](https://pepy.tech/project/duckduckgo-mcp)
[![Smithery](https://smithery.ai/badge/@cyranob/duckduckgo-mcp)](https://smithery.ai/server/@cyranob/duckduckgo-mcp)

A Model Context Protocol (MCP) server that provides two capabilities:
1) Search the web using DuckDuckGo
2) Fetch and convert web content using Jina Reader

## Features

- DuckDuckGo web search with safe search controls
- Fetch and convert URLs to markdown or JSON using Jina Reader
- LLM-friendly output format option for search results
- CLI for search, fetch, serve, and version commands
- MCP tools for LLM integration
- Docker support for containerized deployment

## Installation

### Prerequisites

- Python 3.10 or higher
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

### Install via Smithery

To install DuckDuckGo MCP Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@cyranob/duckduckgo-mcp):

```bash
npx -y @smithery/cli install @cyranob/duckduckgo-mcp --client claude
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

### Docker

Build and run with Docker:

```bash
# Build the image (uses version from latest git tag)
docker build --build-arg VERSION=$(git describe --tags --abbrev=0 | sed 's/^v//') -t duckduckgo-mcp .

# Or specify a version manually
docker build --build-arg VERSION=2.0.2 -t duckduckgo-mcp .

# Run the server (MCP servers use STDIO, so typically run within an MCP client)
docker run -i duckduckgo-mcp
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

```bash
# Search DuckDuckGo (JSON output, default)
duckduckgo-mcp search "your search query" --max-results 5 --safesearch moderate

# Search with LLM-friendly text output
duckduckgo-mcp search "your search query" --output-format text
```

### Testing the Fetch Tool

```bash
# Fetch a URL and return markdown
duckduckgo-mcp fetch "https://example.com" --format markdown

# Fetch a URL and return JSON
duckduckgo-mcp fetch "https://example.com" --format json

# Limit output length

duckduckgo-mcp fetch "https://example.com" --max-length 2000

# Include generated image alt text
duckduckgo-mcp fetch "https://example.com" --with-images
```

### Version Information

```bash
# Show version
duckduckgo-mcp version

# Show detailed version info
duckduckgo-mcp version --debug
```

## MCP Client Setup

This MCP server works with any MCP-compatible client. Use one of the setups below.

Python 3.10-3.13 is supported (3.14 not yet). Use `--python ">=3.10,<3.14"` with `uvx` to enforce. Verified with Python 3.12 and 3.13.

### Claude Desktop

1. Open Claude Desktop > Settings > Developer > Edit Config.
2. Edit the config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
3. Add the server config under `mcpServers`:
   ```json
    {
      "mcpServers": {
        "duckduckgo": {
          "command": "uvx",
          "args": ["--python", ">=3.10,<3.14", "duckduckgo-mcp", "serve"]
        }
      }
    }

   ```
4. Restart Claude Desktop.

### Claude Code

Add a local stdio server:

```bash
claude mcp add --transport stdio duckduckgo -- uvx --python ">=3.10,<3.14" duckduckgo-mcp serve
```

Optional: `claude mcp list` to verify, or `claude mcp add-from-claude-desktop` to import.

### Codex (CLI + IDE)

Add via CLI:

```bash
codex mcp add duckduckgo -- uvx --python ">=3.10,<3.14" duckduckgo-mcp serve
```

Or configure `~/.codex/config.toml`:

```toml
[mcp_servers.duckduckgo]
command = "uvx"
args = ["--python", ">=3.10,<3.14", "duckduckgo-mcp", "serve"]
```

### OpenCode

Add to your OpenCode config (`~/.config/opencode/opencode.json` or project `opencode.json`):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "duckduckgo": {
      "type": "local",
      "command": ["uvx", "--python", ">=3.10,<3.14", "duckduckgo-mcp", "serve"],
      "enabled": true
    }
  }
}
```

Or run `opencode mcp add` and follow the prompts.

### Cursor

Add to `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project):

```json
{
  "mcpServers": {
    "duckduckgo": {
      "command": "uvx",
      "args": ["--python", ">=3.10,<3.14", "duckduckgo-mcp", "serve"]
    }
  }
}
```

Verify with:

```bash
cursor-agent mcp list
```

## MCP Tools

The server exposes these tools to MCP clients:

```python
@mcp.tool()
def duckduckgo_search(
    query: str,
    max_results: int = 5,
    safesearch: str = "moderate",
    output_format: str = "json"
) -> list | str:
    """Search DuckDuckGo for the given query."""
```

```python
@mcp.tool()
def jina_fetch(url: str, format: str = "markdown", max_length: int | None = None, with_images: bool = False) -> str | dict:
    """Fetch a URL and convert it using Jina Reader."""
```

Example usage in an MCP client:

```python
# This is handled automatically by the MCP client
results = duckduckgo_search("Python programming", max_results=3)
content = jina_fetch("https://example.com", format="markdown")

# Get LLM-friendly text output
text_results = duckduckgo_search("Python programming", output_format="text")
```

## API

### Tool 1: Search

- **Tool Name**: `duckduckgo_search`
- **Description**: Search the web using DuckDuckGo (powered by the `ddgs` library)

#### Parameters

- `query` (string, required): The search query
- `max_results` (integer, optional, default: 5): Maximum number of search results to return
- `safesearch` (string, optional, default: "moderate"): Safe search setting ("on", "moderate", or "off")
- `output_format` (string, optional, default: "json"): Output format - "json" for structured data, "text" for LLM-friendly formatted string

#### Response

**JSON format** (default): A list of dictionaries:

```json
[
  {
    "position": 1,
    "title": "Result title",
    "url": "https://example.com",
    "snippet": "Text snippet from the search result"
  },
  {
    "position": 2,
    "title": "Another result",
    "url": "https://example2.com",
    "snippet": "Another snippet"
  }
]
```

**Text format**: An LLM-friendly formatted string:

```
Found 3 search results:

1. Result title
   URL: https://example.com
   Summary: Text snippet from the search result

2. Another result
   URL: https://example2.com
   Summary: Another snippet
```

### Tool 2: Fetch

- **Tool Name**: `jina_fetch`
- **Description**: Fetch a URL and convert it to markdown or JSON using Jina Reader

#### Parameters

- `url` (string, required): The URL to fetch and convert
- `format` (string, optional, default: "markdown"): Output format ("markdown" or "json")
- `max_length` (integer, optional): Maximum content length to return (None for no limit)
- `with_images` (boolean, optional, default: false): Whether to include image alt text generation

#### Response

For markdown format: a string containing markdown content

For JSON format: a dictionary with the structure:

```json
{
  "url": "https://example.com",
  "title": "Page title",
  "content": "Markdown content"
}
```

## Notes

- Search uses the `ddgs` package (renamed from `duckduckgo-search`).
- Fetch uses the Jina Reader API at `https://r.jina.ai/`.

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
