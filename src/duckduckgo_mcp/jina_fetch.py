#!/usr/bin/env python3
"""
Jina Reader URL Fetcher

This module provides functionality to fetch URLs and convert them to markdown or JSON
using the Jina Reader API. It supports different content types including HTML and PDFs.
"""

import logging
import requests
import json
from typing import Dict, Any, Optional, Union
from urllib.parse import urlparse, quote
from fastmcp import FastMCP

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create the MCP server (will be imported by cli.py)
mcp = FastMCP(name="duckduckgo_mcp")

# Jina Reader API base URL
JINA_READER_BASE_URL = "https://r.jina.ai/"

def fetch_url(
    url: str, 
    format: str = "markdown", 
    max_length: Optional[int] = None, 
    with_images: bool = False
) -> Union[str, Dict[str, Any]]:
    """
    Fetch a URL and convert its content using Jina Reader API.
    
    Args:
        url: The URL to fetch and convert
        format: Output format - "markdown" (default) or "json"
        max_length: Maximum content length to return (None for no limit)
        with_images: Whether to include image alt text generation
        
    Returns:
        The fetched content as markdown string or JSON dict depending on format parameter
        
    Raises:
        ValueError: If the URL is invalid
        RuntimeError: If there is an error fetching or processing the content
    """
    # Validate URL
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")
        
    # Check URL format
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL format")
    except Exception as e:
        raise ValueError(f"Invalid URL: {str(e)}")
    
    # Prepare request
    headers = {}
    
    # Set appropriate Accept header based on format
    if format.lower() == "json":
        headers["Accept"] = "application/json"
    elif format.lower() != "markdown":
        logger.warning(f"Unsupported format: {format}. Using markdown as default.")
    
    # Set header for image alt text generation if requested
    if with_images:
        headers["X-With-Generated-Alt"] = "true"
    
    # Set x-no-cache to get fresh content
    headers["x-no-cache"] = "true"
    
    # Prepare the full Jina Reader URL
    jina_url = f"{JINA_READER_BASE_URL}{quote(url)}"
    
    try:
        logger.debug(f"Fetching URL: {url} via Jina Reader")
        response = requests.get(jina_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Handle response based on format
        if format.lower() == "json":
            content = response.json()
            
            # Trim content if max_length is specified
            if max_length and content.get("content") and len(content["content"]) > max_length:
                content["content"] = content["content"][:max_length] + "... (content truncated)"
                
            return content
        else:
            # Default is markdown
            content = response.text
            
            # Trim content if max_length is specified
            if max_length and len(content) > max_length:
                content = content[:max_length] + "... (content truncated)"
                
            return content
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Error fetching URL ({url}): {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except json.JSONDecodeError as e:
        error_msg = f"Error decoding JSON response: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error while fetching URL: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

@mcp.tool()
def jina_fetch(
    url: str, 
    format: str = "markdown", 
    max_length: Optional[int] = None, 
    with_images: bool = False
) -> Union[str, Dict[str, Any]]:
    """
    Fetch a URL and convert it to markdown or JSON using Jina Reader.
    
    Args:
        url: The URL to fetch and convert
        format: Output format - "markdown" or "json"
        max_length: Maximum content length to return (None for no limit)
        with_images: Whether to include image alt text generation
        
    Returns:
        The fetched content in the specified format (markdown string or JSON object)
    """
    # Validate parameters
    if not url:
        raise ValueError("Missing required parameter: url")
    
    if format and format.lower() not in ["markdown", "json"]:
        raise ValueError("Format must be either 'markdown' or 'json'")
    
    if max_length is not None:
        try:
            max_length = int(max_length)
            if max_length <= 0:
                raise ValueError("max_length must be a positive integer")
        except (ValueError, TypeError):
            raise ValueError("max_length must be a positive integer")
    
    # Perform URL fetching
    try:
        result = fetch_url(url, format, max_length, with_images)
        return result
    except Exception as e:
        logger.error(f"Error in jina_fetch: {str(e)}")
        raise

if __name__ == "__main__":
    # Simple command-line test if run directly
    import sys
    if len(sys.argv) > 1:
        try:
            result = fetch_url(sys.argv[1], "markdown", None, True)
            print(result)
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
    else:
        print("Usage: python jina_fetch.py <url>")
        sys.exit(1)